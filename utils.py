import hashlib
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from cachetools import TTLCache
import os
import time
import re
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches, Pt as PptxPt

# We use a simple TTL cache to keep track of requests per user ID
# 1-second TTL means 1 message per second allowed per user
rate_limit_cache = TTLCache(maxsize=10000, ttl=1)

def hash_password(password: str) -> str:
    """Returns SHA-256 hash of a given password."""
    return hashlib.sha256(password.encode()).hexdigest()

async def send_split_message(message: Message, text: str):
    """Splits a long message into chunks and sends them sequentially."""
    limit = 4000  # Telegram limit is 4096, using 4000 for safety
    if len(text) <= limit:
        await message.answer(text)
    else:
        for i in range(0, len(text), limit):
            chunk = text[i:i + limit]
            await message.answer(chunk)

def clean_markdown(text: str) -> str:
    """Removes common markdown-style formatting symbols."""
    # Remove Bold/Italic stars
    text = re.sub(r'\*+', '', text)
    # Remove Hashtags headings (###, ####, etc.)
    text = re.sub(r'#+\s*', '', text)
    # Remove Underscores
    text = re.sub(r'_+', '', text)
    # Remove horizontal lines represented by dashes
    text = re.sub(r'-{3,}', '', text)
    return text.strip()

def cleanup_old_files():
    """Deletes files older than 24 hours from the exports directory."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        return
    
    now = time.time()
    for f in os.listdir(exports_dir):
        f_path = os.path.join(exports_dir, f)
        if os.path.isfile(f_path):
            # 86400 seconds = 24 hours
            if os.stat(f_path).st_mtime < now - 86400:
                try:
                    os.remove(f_path)
                except Exception:
                    pass

def create_docx(text: str, filename: str, university: str, author: str, topic: str, doc_type: str) -> str:
    """Generates a structured .docx file with Cover, Outline, and Content."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    
    cleanup_old_files()
    
    doc = Document()
    
    # --- PAGE 1: COVER ---
    # Combined Ministry and University Name
    uni_text = f"O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM FAN VA INNOVATSIYA VAZIRLIGI\n{university.upper()}"
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_header = p_header.add_run(uni_text)
    run_header.bold = True
    run_header.font.size = Pt(18)
    
    # Large Space
    for _ in range(6): doc.add_paragraph("")
    
    # Document Type (MUSTAQIL ISH / MAQOLA)
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run3 = p3.add_run(doc_type.upper())
    run3.bold = True
    run3.font.size = Pt(36)
    
    doc.add_paragraph("")
    
    # Topic
    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run4 = p4.add_run(topic.upper())
    run4.bold = True
    run4.font.size = Pt(16)
    
    # Space before author
    for _ in range(4): doc.add_paragraph("")
    
    # Author Info
    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run5 = p5.add_run(f"Bajardi: {author}")
    run5.font.size = Pt(14)
    
    # Push Year to bottom
    for _ in range(6): doc.add_paragraph("")
    
    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run6 = p6.add_run("2025-2026 O'quv Yili")
    run6.font.size = Pt(12)
    
    doc.add_page_break()
    
    # --- PAGE 2: OUTLINE (REJA) ---
    content_parts = text.split("REJA:", 1)
    if len(content_parts) > 1:
        parts = content_parts[1].split("\n\n", 1)
        reja_text = parts[0].strip()
        actual_content = parts[1].strip() if len(parts) > 1 else ""
    else:
        reja_text = ""
        actual_content = text
        
    p_reja_title = doc.add_paragraph()
    p_reja_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_reja = p_reja_title.add_run("REJA")
    run_reja.bold = True
    run_reja.font.size = Pt(16)
    
    doc.add_paragraph("")
    
    if reja_text:
        # Clean reja before adding
        for line in reja_text.split("\n"):
            if line.strip():
                p_r = doc.add_paragraph()
                run_r = p_r.add_run(clean_markdown(line))
                run_r.font.size = Pt(14)
    else:
        doc.add_paragraph("Ma'lumot topilmadi.").runs[0].font.size = Pt(14)
        
    doc.add_page_break()
    
    # --- PAGE 3+: CONTENT ---
    # Split content by double newlines or similar to detect paragraph breaks
    paragraphs = actual_content.split('\n')
    for line in paragraphs:
        if not line.strip():
            continue
            
        p = doc.add_paragraph()
        # Set 1.5 lines spacing
        p.paragraph_format.line_spacing = 1.5
        
        cleaned_line = clean_markdown(line)
        run = p.add_run(cleaned_line)
        run.font.size = Pt(14)
        
        # Simple bold check for headers (if entire line was uppercase in original)
        if line.isupper() or line.strip().startswith('###'):
            run.bold = True
            
        # Add space between paragraphs as requested
        # We also set 1.5 spacing for these empty paragraphs to maintain consistency
        empty_p = doc.add_paragraph("")
        empty_p.paragraph_format.line_spacing = 1.5
            
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    doc.save(file_path)
    return file_path

def add_toc(doc):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    r = run._r
    r.append(fldChar)
    r.append(instrText)
    r.append(fldChar2)
    r.append(fldChar3)

def create_mustaqil_ish_docx(text: str, filename: str, topic: str, subject: str, university: str, teacher: str, author: str) -> str:
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    cleanup_old_files()
    
    doc = Document()
    
    # 1. Formatting
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    for h in ['Heading 1', 'Heading 2']:
        hs = doc.styles[h]
        hs.font.name = 'Times New Roman'
        hs.font.size = Pt(14)
        hs.font.bold = True
        hs.font.color.rgb = None # Black
        hs.paragraph_format.line_spacing = 1.5
        hs.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    
    # 2. Cover Page
    uni_lines = university.split(',')
    uni_name = uni_lines[0].strip().upper() if uni_lines else "OLIY TA'LIM MUASSASASI"
    city_name = uni_lines[1].strip() if len(uni_lines) > 1 else "Toshkent"
    
    p_gov = doc.add_paragraph()
    p_gov.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_gov = p_gov.add_run("O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM FAN VA INNOVATSIYA VAZIRLIGI\n" + uni_name)
    run_gov.bold = True
    run_gov.font.size = Pt(14)
    
    for _ in range(5): doc.add_paragraph("")
    
    p_fac = doc.add_paragraph()
    p_fac.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fac.add_run(f"\"{subject.upper()}\" fanidan").bold = True
    
    p_type = doc.add_paragraph()
    p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_type = p_type.add_run("MUSTAQIL ISH")
    r_type.bold = True
    r_type.font.size = Pt(24)
    
    doc.add_paragraph("")
    
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.add_run(f"Mavzu: {topic.upper()}").bold = True
    
    for _ in range(5): doc.add_paragraph("")
    
    # Signatures
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.add_run(f"Bajardi: {author}\nTekshirdi: {teacher}")
    
    for _ in range(5): doc.add_paragraph("")
    
    # Bottom Year
    p_year = doc.add_paragraph()
    p_year.alignment = WD_ALIGN_PARAGRAPH.CENTER
    import datetime
    year = datetime.datetime.now().year
    p_year.add_run(f"{city_name} - {year}")
    
    doc.add_page_break()
    
    # 3. TOC
    p_toc = doc.add_paragraph()
    p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc.add_run("MUNDARIJA").bold = True
    add_toc(doc)
    doc.add_page_break()
    
    # 4. Content
    # We parse the text. Skip REJA part since we use Word TOC.
    parts = text.split("KIRISH:")
    if len(parts) > 1:
        # Strip out anything before KIRISH
        content = "KIRISH:\n" + parts[1].strip()
    else:
        content = text
        
    paragraphs = content.split('\n')
    for line in paragraphs:
        if not line.strip():
            continue
            
        line_clean = clean_markdown(line)
        
        # Determine if heading
        is_heading = False
        if line_clean.startswith("KIRISH") or line_clean.startswith("XULOSA") or line_clean.startswith("ASOSIY QISM") or line_clean.startswith("FOYDALANILGAN ADABIYOTLAR"):
            p = doc.add_paragraph(line_clean, style='Heading 1')
            is_heading = True
        elif re.match(r'^\d+\.\d+\.', line_clean) or re.match(r'^\d+\.', line_clean):
            p = doc.add_paragraph(line_clean, style='Heading 2')
            is_heading = True
        else:
            p = doc.add_paragraph()
            run = p.add_run(line_clean)
            if line.isupper() and len(line) > 5:
                run.bold = True
                
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    doc.save(file_path)
    return file_path

def create_pptx(text: str, filename: str, topic: str, author: str) -> str:
    """Generates a .pptx file with slides from structured text."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    
    cleanup_old_files()
    
    prs = Presentation()
    
    # --- SLIDE 1: TITLE SLIDE ---
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = topic.upper()
    slide.placeholders[1].text = f"Taqdimotchi: {author}\n2025-2026 O'quv Yili"
    
    # --- SLIDES 2+: CONTENT ---
    sections = re.split(r'Slayd \d+:|Bo\'lim:', text)
    if len(sections) == 1: # If no markers, just split by double newlines or similar
         sections = text.split('\n\n')

    for section in sections:
        section = section.strip()
        if not section: continue
        
        lines = section.split('\n')
        slide_title = lines[0].strip()[:50]
        slide_body = "\n".join(lines[1:]).strip()
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = clean_markdown(slide_title)
        tf = slide.placeholders[1].text_frame
        for line in slide_body.split('\n'):
            if line.strip():
                p = tf.add_paragraph()
                p.text = clean_markdown(line)
                p.level = 0

    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    prs.save(file_path)
    return file_path

class ThrottlingMiddleware(BaseMiddleware):
    """Simple anti-spam middleware to prevent rapid messaging (Rate Limit)."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user:
            user_id = event.from_user.id
            if user_id in rate_limit_cache:
                # Silently drop the spamming message
                return
            rate_limit_cache[user_id] = True
        return await handler(event, data)

class BannedUserMiddleware(BaseMiddleware):
    """Middleware to check if the user is banned from using the bot."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        from database import is_banned
        if event.from_user:
            if await is_banned(event.from_user.id):
                # Optionally inform the user they are banned, or just drop
                return
        return await handler(event, data)
