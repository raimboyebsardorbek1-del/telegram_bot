import logging
import json
from aiogram import Bot
from aiogram.types import FSInputFile
from services.ai_service import (
    generate_assignment,
    generate_report,
    generate_esse,
    generate_kurs_ishi,
    generate_presentation_text
)
from utils import create_academic_docx, create_pptx
from database import get_referrer, has_referred_ordered, mark_referral_order_completed, update_balance

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
        
    topic = params.get("topic", "Nomsiz mavzu")
    subject = params.get("subject", "Umumiy fan")
    author = params.get("author", "Talaba")
    
    await bot.send_message(user_id, f"✅ Buyurtma qabul qilindi!\n\n📄 '{topic}' mavzusidagi hujjat tayyorlanmoqda, iltimos kuting...")
    
    try:
        if service_type == "mustaqil":
            text = await generate_assignment(topic, subject, tier)
            file_path = create_academic_docx(text, f"Mustaqil_ish_{user_id}.docx", topic, subject, "MUSTAQIL ISH", author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Sizning mustaqil ishingiz tayyor!")
            
        elif service_type == "referat":
            text = await generate_report(topic, subject, tier)
            file_path = create_academic_docx(text, f"Referat_{user_id}.docx", topic, subject, "REFERAT", author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Sizning referatingiz tayyor!")
            
        elif service_type == "esse":
            text = await generate_esse(topic, subject, tier)
            file_path = create_academic_docx(text, f"Esse_{user_id}.docx", topic, subject, "ESSE", author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Sizning esseyiz tayyor!")
            
        elif service_type == "kurs":
            text = await generate_kurs_ishi(topic, subject, tier)
            file_path = create_academic_docx(text, f"Kurs_ishi_{user_id}.docx", topic, subject, "KURS ISHI", author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Sizning kurs ishingiz tayyor!")
            
        elif service_type == "taqdimot":
            text = await generate_presentation_text(topic, subject, tier)
            file_path = create_pptx(text, f"Taqdimot_{user_id}.pptx", topic, author)
            await bot.send_document(user_id, FSInputFile(file_path), caption="Sizning taqdimotingiz tayyor!")
            
        # Referral completion reward
        referrer_id = await get_referrer(user_id)
        if referrer_id:
            already_rewarded = await has_referred_ordered(user_id)
            if not already_rewarded:
                await mark_referral_order_completed(user_id)
                await update_balance(referrer_id, 3000.0)
                await update_balance(user_id, 3000.0)
                try:
                    await bot.send_message(
                        referrer_id,
                        "🎉 Siz taklif qilgan do'stingiz birinchi buyurtmasini yakunladi!\n"
                        "Sizga va do'stingizga 3,000 so'mdan bonus taqdim etildi."
                    )
                except Exception:
                    pass
                try:
                    await bot.send_message(
                        user_id,
                        "🎉 Birinchi buyurtmangiz yakunlandi!\n"
                        "Sizga va sizni taklif qilgan do'stingizga 3,000 so'mdan bonus taqdim etildi."
                    )
                except Exception:
                    pass
                    
    except Exception as e:
        logging.error(f"Fulfillment error for order {order['order_id']}: {e}")
        await bot.send_message(user_id, f"❌ Hujjat yaratishda xatolik yuz berdi: {e}. Iltimos admin bilan bog'laning.")