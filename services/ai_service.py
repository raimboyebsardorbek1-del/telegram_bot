import google.generativeai as genai
import re
from config import GEMINI_API_KEY
from database import log_ai_history, get_user_chat_history

# Configure the Gemini API with the initialized key
genai.configure(api_key=GEMINI_API_KEY)

# Using flash model for best performance and cost
# Using flash model for better quota and performance
model = genai.GenerativeModel('gemini-flash-latest')

async def generate_article(topic: str, pages: str, language: str) -> str:
    """Generates an article using Gemini based on topic and language requirements."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 2
    word_target = num_pages * 280

    prompt = (
        f"Write an article about '{topic}' in {language} language. "
        f"The content MUST be at least {word_target} words long to fill exactly {num_pages} pages. "
        f"Structure MUST start with a section titled 'REJA:' which lists the main points in a numbered list (1., 2., 3., etc.). "
        f"Following the REJA section, provide the full content structured into: "
        f"Kirish (Introduction), Asosiy qism (Main part), and Xulosa (Conclusion)."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_article: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def generate_assignment(topic: str, subject: str, pages: str) -> str:
    """Generates an assignment (mustaqil ish) in Uzbek (Latin) with strict structure."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 10
    word_target = num_pages * 280

    prompt = (
        f"Siz O'zbekistondagi oliygoh talabasi uchun '{subject}' fanidan '{topic}' mavzusida Mustaqil ish yozishingiz kerak.\n"
        f"Umumiy hajm kamida {word_target} ta so'zdan iborat bo'lishi va {num_pages} betni qoplashi shart. Tili faqat o'zbek tili (lotin alifbosi), uslubi professional va ilmiy-akademik bo'lishi lozim.\n\n"
        f"Matn tarkibida quyidagi asosiy sarlavhalar bo'lishi va har birining mazmuni keng yoritilishi shart:\n"
        f"REJA:\n"
        f"1. Kirish\n"
        f"2. Asosiy qism\n"
        f"3. Xulosa\n"
        f"4. Foydalanilgan adabiyotlar ro'yxati\n\n"
        f"Ushbu rejadan so'ng matnni quyidagi sarlavhalar ostida yozing:\n"
        f"KIRISH\n"
        f"[Mavzuning dolzarbligi, tadqiqot maqsadi va vazifalari, kamida {int(word_target * 0.1)} so'z]\n\n"
        f"ASOSIY QISM\n"
        f"[Mavzuni to'liq yorituvchi nazariy va amaliy tahlillar, statistik ma'lumotlar, kamida {int(word_target * 0.7)} so'z]\n\n"
        f"XULOSA\n"
        f"[Mavzu bo'yicha yakuniy xulosalar va takliflar, kamida {int(word_target * 0.1)} so'z]\n\n"
        f"FOYDALANILGAN ADABIYOTLAR\n"
        f"[Kamida 5 ta ilmiy adabiyot, darslik yoki ishonchli internet manbalari alifbo tartibida, GOST standartida]\n\n"
        f"Matnda 'KIRISH', 'ASOSIY QISM', 'XULOSA', 'FOYDALANILGAN ADABIYOTLAR' sarlavhalarini aynan shu shaklda bosh harflar bilan yozing."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_assignment: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def generate_report(topic: str, subject: str, pages: str) -> str:
    """Generates a report (referat) in Uzbek (Latin)."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 10
    word_target = num_pages * 280

    prompt = (
        f"Siz O'zbekistondagi oliygoh talabasi uchun '{subject}' fanidan '{topic}' mavzusida Referat yozishingiz kerak.\n"
        f"Umumiy hajm kamida {word_target} ta so'zdan iborat bo'lishi va {num_pages} betni qoplashi shart. Tili faqat o'zbek tili (lotin alifbosi), uslubi ilmiy va ma'lumotlarga boy bo'lishi lozim.\n\n"
        f"Matn tarkibida quyidagi asosiy sarlavhalar bo'lishi va har birining mazmuni keng yoritilishi shart:\n"
        f"REJA:\n"
        f"1. Kirish\n"
        f"2. Asosiy qism\n"
        f"3. Xulosa\n"
        f"4. Foydalanilgan adabiyotlar ro'yxati\n\n"
        f"Ushbu rejadan so'ng matnni quyidagi sarlavhalar ostida yozing:\n"
        f"KIRISH\n"
        f"[Mavzuning dolzarbligi va umumiy ta'rifi, kamida {int(word_target * 0.15)} so'z]\n\n"
        f"ASOSIY QISM\n"
        f"[Tarixiy va nazariy ma'lumotlar, asosiy tushunchalar, tahlillar, kamida {int(word_target * 0.75)} so'z]\n\n"
        f"XULOSA\n"
        f"[Umumiy xulosalar, kamida {int(word_target * 0.1)} so'z]\n\n"
        f"FOYDALANILGAN ADABIYOTLAR\n"
        f"[Kamida 5 ta adabiyot yoki manba alifbo tartibida]\n\n"
        f"Matnda 'KIRISH', 'ASOSIY QISM', 'XULOSA', 'FOYDALANILGAN ADABIYOTLAR' sarlavhalarini aynan shu shaklda bosh harflar bilan yozing."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_report: {e}")
        return f"Xatolik yuz berdi. (Xato: {e})"

async def generate_esse(topic: str, subject: str, pages: str) -> str:
    """Generates an essay (esse) in Uzbek (Latin) - free flow style but structured."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 3
    word_target = num_pages * 280

    prompt = (
        f"Siz '{subject}' fanidan '{topic}' mavzusida Esse yozishingiz kerak.\n"
        f"Umumiy hajm kamida {word_target} ta so'zdan iborat bo'lishi va {num_pages} betni qoplashi shart. Tili faqat o'zbek tili (lotin alifbosi), erkin, mulohazali va insho (essay) uslubida bo'lishi lozim.\n\n"
        f"Essei tarkibida quyidagi sarlavhalar bo'lishi shart:\n"
        f"KIRISH\n"
        f"[Mavzuga kirish, muammoning qo'yilishi, kamida {int(word_target * 0.2)} so'z]\n\n"
        f"ASOSIY QISM\n"
        f"[Muallifning shaxsiy fikrlari, tahliliy mulohazalar, dalillar va asoslar, kamida {int(word_target * 0.6)} so'z]\n\n"
        f"XULOSA\n"
        f"[Umumiy shaxsiy yakun va xulosa, kamida {int(word_target * 0.2)} so'z]\n\n"
        f"Matnda 'KIRISH', 'ASOSIY QISM', 'XULOSA' sarlavhalarini aynan shu shaklda bosh harflar bilan yozing. Reja va adabiyotlar shart emas."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_esse: {e}")
        return f"Xatolik yuz berdi. (Xato: {e})"

async def generate_kurs_ishi(topic: str, subject: str, pages: str) -> str:
    """Generates coursework (kurs ishi) in Uzbek (Latin) - extensive structure."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 20
    word_target = num_pages * 280

    prompt = (
        f"Siz O'zbekistondagi oliygoh talabasi uchun '{subject}' fanidan '{topic}' mavzusida kengaytirilgan Kurs ishi yozishingiz kerak.\n"
        f"Umumiy hajm kamida {word_target} ta so'zdan iborat bo'lishi va {num_pages} betni qoplashi shart. Tili faqat o'zbek tili (lotin alifbosi), yuqori darajadagi akademik va ilmiy-tahliliy uslubda yozilishi lozim.\n\n"
        f"QAT'IY TUZILMA (Shu ketma-ketlikda yozing):\n"
        f"REJA:\n"
        f"1. Kirish\n"
        f"2. I Bob: Nazariy asoslar\n"
        f"3. II Bob: Amaliy tahlillar va samaradorlik\n"
        f"4. Xulosa va takliflar\n"
        f"5. Foydalanilgan adabiyotlar ro'yxati\n\n"
        f"Ushbu rejadan so'ng matnni quyidagi sarlavhalar ostida yozing:\n"
        f"KIRISH\n"
        f"[Mavzuning dolzarbligi, tadqiqot obyekti, predmeti, maqsadlari va vazifalari, metodologiyasi, kamida {int(word_target * 0.1)} so'z]\n\n"
        f"I BOB: NAZARIY ASOSLAR\n"
        f"[Mavzuga oid nazariy tushunchalar, xorijiy va mahalliy olimlarning qarashlari, kamida {int(word_target * 0.35)} so'z]\n\n"
        f"II BOB: AMALIY TAHLILLAR VA SAMARADORLIK\n"
        f"[Mavzu bo'yicha real ma'lumotlar, hisob-kitoblar, jadvallar yoki amaliy muammolar tahlili, taklif qilinayotgan yechimlar, kamida {int(word_target * 0.4)} so'z]\n\n"
        f"XULOSA\n"
        f"[Tadqiqot natijalari va taklif etilgan tavsiyalar, kamida {int(word_target * 0.15)} so'z]\n\n"
        f"FOYDALANILGAN ADABIYOTLAR\n"
        f"[Kamida 8-10 ta ilmiy adabiyot, qonunchilik hujjatlari, statistika nashrlari alifbo tartibida, GOST standartida]\n\n"
        f"Matnda 'KIRISH', 'I BOB: NAZARIY ASOSLAR', 'II BOB: AMALIY TAHLILLAR VA SAMARADORLIK', 'XULOSA', 'FOYDALANILGAN ADABIYOTLAR' sarlavhalarini aynan shu shaklda bosh harflar bilan yozing."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_kurs_ishi: {e}")
        return f"Xatolik yuz berdi. (Xato: {e})"

async def generate_presentation_text(topic: str, subject: str, slides: str) -> str:
    """Generates slide text for a presentation about topic/subject."""
    match = re.search(r'(\d+)', str(slides))
    num_slides = int(match.group(1)) if match else 10

    prompt = (
        f"Siz '{subject}' fanidan '{topic}' mavzusida taqdimot slayd matnlarini tayyorlashingiz kerak.\n"
        f"Umumiy slaydlar soni {num_slides} ta bo'lishi shart. Har bir slayd uchun sarlavha va qisqa ma'lumotlar (punktlar shaklida) yozing.\n"
        f"Tili faqat o'zbek tilida (lotin alifbosida) bo'lsin. Har bir slayd quyidagi formatda bo'lishi shart:\n\n"
        f"Slayd 1: [Slayd sarlavhasi]\n"
        f"- [Qisqa ma'lumot yoki fakt 1]\n"
        f"- [Qisqa ma'lumot yoki fakt 2]\n"
        f"- [Qisqa ma'lumot yoki fakt 3]\n\n"
        f"Formatga juda aniq rioya qiling. Slayd 1 dan boshlab to Slayd {num_slides} gacha davom ettiring."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_presentation_text: {e}")
        return f"Xatolik yuz berdi. (Xato: {e})"

async def chat_with_gemini(user_id: int, message: str) -> str:
    """Chats with Gemini, maintaining a short history per user from DB."""
    history = await get_user_chat_history(user_id, limit=7)
    
    chat_history = []
    for h_msg, h_res in history:
        chat_history.append({"role": "user", "parts": [h_msg]})
        chat_history.append({"role": "model", "parts": [h_res]})
    
    try:
        chat = model.start_chat(history=chat_history)
        response = await chat.send_message_async(message)
        await log_ai_history(user_id, message, response.text)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in chat_with_gemini: {e}")
        if "quota" in str(e).lower():
            return "Kechirasiz, AI xizmati limiti tugagan. Iltimos bir ozdan so'ng harakat qilib ko'ring."
        return f"Xatolik yuz berdi. Savolingizga hozircha javob bera olmayman. (Xato: {e})"
