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
from docx.shared import Pt

# User ID bo'yicha so'rovlar sonini kuzatish uchun oddiy TTL keshidan foydalanamiz
# 1-soniyali TTL bitta foydalanuvchiga sekundiga faqat 1 ta xabar yuborishga ruxsat beradi
request_cache = TTLCache(maxsize=10000, ttl=1.0)

def hash_password(password: str) -> str:
    """Berilgan parolni SHA-256 formatida kodlaydi."""
    return hashlib.sha256(password.encode()).hexdigest()

async def send_split_message(message: Message, text: str):
    """Uzun xabarni bo'laklarga bo'lib ketma-ket yuboradi."""
    limit = 4000  # Telegram limiti 4096, xavfsizlik uchun 4000 dan foydalanamiz
    if len(text) <= limit:
        await message.answer(text)
    else:
        for i in range(0, len(text), limit):
            chunk = text[i:i + limit]
            await message.answer(chunk)

def clean_markdown(text: str) -> str:
    """Markdown formatidagi belgilarni (###, **, _) olib tashlaydi."""
    # Qalin/Kursiv yulduzchalarini olib tashlash
    text = re.sub(r'\*+', '', text)
    # Sarlavha heshteglarini olib tashlash (###, #### va hk)
    text = re.sub(r'#+\s*', '', text)
    # Pastki chiziklarni olib tashlash
    text = re.sub(r'_+', '', text)
    # Chiziqli ajratkichlarni olib tashlash
    text = re.sub(r'-{3,}', '', text)
    return text.strip()

def cleanup_old_files():
    """Exports direktoriyasidan 24 soatdan eski bo'lgan fayllarni o'chiradi."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        return
    
    now = time.time()
    for f in os.listdir(exports_dir):
        f_path = os.path.join(exports_dir, f)
        if os.path.isfile(f_path):
            # 86400 soniya = 24 soat
            if os.stat(f_path).st_mtime < now - 86400:
                try:
                    os.remove(f_path)
                except Exception:
                    pass

def create_docx(text: str, filename: str, university: str, author: str, topic: str, doc_type: str) -> str:
    """Titul varag'i, Reja va Asosiy qismdan iborat .docx fayl yaratadi."""
    exports_dir = "exports"
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    
    cleanup_old_files()
    
    doc = Document()
    
    # --- 1-BET: TITUL ---
    # Vazirlik va Oliygoh nomi birgalikda
    uni_text = f"O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM FAN VA INNOVATSIYA VAZIRLIGI\n{university.upper()}"
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_header = p_header.add_run(uni_text)
    run_header.bold = True
    run_header.font.size = Pt(18)
    
    # Kataroq bo'sh joy
    for _ in range(6): doc.add_paragraph("")
    
    # Ish turi (MUSTAQIL ISH / MAQOLA)
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run3 = p3.add_run(doc_type.upper())
    run3.bold = True
    run3.font.size = Pt(36)
    
    doc.add_paragraph("")
    
    # Mavzu
    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run4 = p4.add_run(topic.upper())
    run4.bold = True
    run4.font.size = Pt(16)
    
    # Muallifdan oldin bo'sh joy
    for _ in range(4): doc.add_paragraph("")
    
    # Muallif haqida ma'lumot
    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run5 = p5.add_run(f"Bajardi: {author}")
    run5.font.size = Pt(14)
    
    # O'quv yilini pastga tushirish
    for _ in range(6): doc.add_paragraph("")
    
    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run6 = p6.add_run("2025-2026 O'quv Yili")
    run6.font.size = Pt(12)
    
    doc.add_page_break()
    
    # --- 2-BET: REJA ---
    # AI matnidan REJA qismini ajratib olishga harakat qilamiz
    content_parts = text.split("REJA:", 1)
    if len(content_parts) > 1:
        parts = content_parts[1].split("\n\n", 1)  # Odatda REJA dan keyin ikkita yangi qator keladi
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
        # Rejani qo'shishdan oldin tozalaymiz
        for line in reja_text.split("\n"):
            if line.strip():
                p_r = doc.add_paragraph()
                run_r = p_r.add_run(clean_markdown(line))
                run_r.font.size = Pt(14)
    else:
        doc.add_paragraph("Ma'lumot topilmadi.").runs[0].font.size = Pt(14)
        
    doc.add_page_break()
    
    # --- 3-BET+: ASOSIY MATN ---
    # Paragraf uzilishlarini aniqlash uchun matnni qatorlarga bo'lamiz
    paragraphs = actual_content.split('\n')
    for line in paragraphs:
        if not line.strip():
            continue
            
        p = doc.add_paragraph()
        # Qatorlar orasini 1.5 qilib belgilash
        p.paragraph_format.line_spacing = 1.5
        
        cleaned_line = clean_markdown(line)
        run = p.add_run(cleaned_line)
        run.font.size = Pt(14)
        
        # Sarlavhalar uchun qalinlashtirish (agar hamma harf katta yoki ### bo'lsa)
        if line.isupper() or line.strip().startswith('###'):
            run.bold = True
            
        # Paragraflar orasida bo'sh joy qo'shish
        # To'g'rilikni saqlash uchun bo'sh paragrafga ham 1.5 spacing beramiz
        empty_p = doc.add_paragraph("")
        empty_p.paragraph_format.line_spacing = 1.5
            
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    doc.save(file_path)
    return file_path

class ThrottlingMiddleware(BaseMiddleware):
    """Xabar yuborish tezligini cheklab, spamdan himoya qiluvchi oddiy middleware."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Agar user keshda bo'lsa, xabarga javob bermaymiz
        if user_id in request_cache:
            return
        
        # Userni keshga qo'shamiz
        request_cache[user_id] = True
        return await handler(event, data)

class BannedUserMiddleware(BaseMiddleware):
    """Foydalanuvchi bloklanganligini tekshiruvchi middleware."""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        from database import is_banned
        if event.from_user:
            if await is_banned(event.from_user.id):
                # Foydalanuvchi bloklangan bo'lsa, xabarga javob bermaymiz
                return
        return await handler(event, data)
