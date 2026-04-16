import hashlib
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from cachetools import TTLCache
import os
import time
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

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
    # Ministry Name
    p1 = doc.add_paragraph("O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM FAN VA INNOVATSIYA VAZIRLIGI")
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.runs[0].bold = True
    p1.runs[0].font.size = Pt(12)
    
    # University Name
    p2 = doc.add_paragraph(university.upper())
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.runs[0].bold = True
    p2.runs[0].font.size = Pt(14)
    
    # Large Space
    for _ in range(5): doc.add_paragraph("")
    
    # Document Type (MUSTAQIL ISH / MAQOLA)
    p3 = doc.add_paragraph(doc_type.upper())
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.runs[0].bold = True
    p3.runs[0].font.size = Pt(36)
    
    doc.add_paragraph("")
    
    # Topic
    p4 = doc.add_paragraph(topic.upper())
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p4.runs[0].bold = True
    p4.runs[0].font.size = Pt(16)
    
    # Space before author
    for _ in range(3): doc.add_paragraph("")
    
    # Author Info
    p5 = doc.add_paragraph(f"Bajardi: {author}")
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p5.runs[0].font.size = Pt(14)
    
    # Push Year to bottom (approximate)
    for _ in range(5): doc.add_paragraph("")
    
    p6 = doc.add_paragraph("2025-2026 O'quv Yili")
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p6.runs[0].font.size = Pt(12)
    
    doc.add_page_break()
    
    # --- PAGE 2: OUTLINE (REJA) ---
    # Try to extract REJA section from AI text
    content_parts = text.split("REJA:", 1)
    if len(content_parts) > 1:
        # Check if there is a header after REJA to stop at
        parts = content_parts[1].split("\n\n", 1)  # Usually REJA is followed by double newline
        reja_text = parts[0].strip()
        actual_content = parts[1].strip() if len(parts) > 1 else ""
    else:
        reja_text = ""
        actual_content = text
        
    p_reja_title = doc.add_paragraph("REJA")
    p_reja_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_reja_title.runs[0].bold = True
    p_reja_title.runs[0].font.size = Pt(16)
    
    doc.add_paragraph("")
    
    if reja_text:
        for line in reja_text.split("\n"):
            if line.strip():
                # Clean up prefix like "1. ", "- " if AI added them
                doc.add_paragraph(line.strip())
    else:
        doc.add_paragraph("Ma'lumot topilmadi.")
        
    doc.add_page_break()
    
    # --- PAGE 3+: CONTENT ---
    for line in actual_content.split('\n'):
        p = doc.add_paragraph(line)
        if line.isupper() or "**" in line: # Simple header detection
            p.runs[0].bold = True
            
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    doc.save(file_path)
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
