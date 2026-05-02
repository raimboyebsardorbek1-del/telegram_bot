import logging
import json
from aiogram import Bot
from aiogram.types import FSInputFile
from services.ai_service import generate_article, generate_assignment, generate_report, generate_presentation_text
from utils import create_docx, create_pptx, create_mustaqil_ish_docx

async def fulfill_order(bot: Bot, order: dict):
    """
    Called after payment is confirmed to generate and send the document.
    """
    user_id = order['user_id']
    service_type = order['service_type']
    tier = order['pages']
    
    try:
        params = json.loads(order['parameters'])
    except Exception:
        params = {}
        
    topic = params.get("topic", "Nomsiz")
    university = params.get("university", "Oliygoh")
    author = params.get("author", "Ishtirokchi")
    
    await bot.send_message(user_id, f"✅ To'lov qabul qilindi!\n\n📄 '{topic}' mavzusidagi {service_type} tayyorlanmoqda, iltimos kuting...")
    
    try:
        if service_type == "maqola":
            text = await generate_article(topic, tier, "O'zbek")
            file_path = create_docx(text, f"Maqola_{user_id}.docx", university, author, topic, "MAQOLA")
            await bot.send_document(user_id, FSInputFile(file_path), caption="Maqola tayyor!")
            
        elif service_type == "mustaqil":
            subject = params.get("subject", "Nomsiz fan")
            teacher = params.get("teacher", "O'qituvchi")
            text = await generate_assignment(topic, tier, "O'rta")
            file_path = create_mustaqil_ish_docx(text, f"Mustaqil_ish_{user_id}.docx", topic, subject, university, teacher, author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Mustaqil ish tayyor!")
            
        elif service_type == "referat":
            text = await generate_report(topic, tier)
            file_path = create_docx(text, f"Referat_{user_id}.docx", university, author, topic, "REFERAT")
            await bot.send_document(user_id, FSInputFile(file_path), caption="Referat tayyor!")
            
        elif service_type == "taqdimot":
            text = await generate_presentation_text(topic, tier)
            file_path = create_pptx(text, f"Taqdimot_{user_id}.pptx", topic, author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Taqdimot tayyor!")
            
    except Exception as e:
        logging.error(f"Fulfillment error for order {order['order_id']}: {e}")
        await bot.send_message(user_id, f"❌ Hujjat yaratishda xatolik yuz berdi: {e}. Iltimos admin @urdu_admin bilan bog'laning.")
