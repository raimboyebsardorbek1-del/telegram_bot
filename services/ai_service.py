import google.generativeai as genai
import re
from config import GEMINI_API_KEY
from database import log_ai_history, get_user_chat_history

# Gemini API ni kalit bilan sozlash
genai.configure(api_key=GEMINI_API_KEY)

# Yaxshi ishlashi va arzonligi uchun flash modelidan foydalanamiz
model = genai.GenerativeModel('gemini-1.5-flash')

async def generate_article(topic: str, pages: str, language: str) -> str:
    """Generates an article based on the topic and language requirements."""
    # Calculate word count based on pages: ~300 words per page (Pt 14, 1.5 spacing)
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 2
    word_target = num_pages * 300

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

async def generate_assignment(subject: str, pages: str, difficulty: str) -> str:
    """Generates an independent work assignment and its solution."""
    # Calculate word count target
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 3
    word_target = num_pages * 300

    prompt = (
        f"Create an independent work assignment (mustaqil ish) about the subject '{subject}' "
        f"with '{difficulty}' difficulty level. The content MUST be at least {word_target} words long to fill exactly {num_pages} pages. "
        f"Structure MUST start with a section titled 'REJA:' which lists the main points in a numbered list (1., 2., 3., etc.). "
        f"Following the REJA section, provide the complete solution/content. "
        f"The entire response must be in Uzbek."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_assignment: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def chat_with_gemini(user_id: int, message: str) -> str:
    """Interacts with Gemini and logs history."""
    # Get last messages history from DB
    history = await get_user_chat_history(user_id, limit=7)
    
    chat_history = []
    for h_msg, h_res in history:
        chat_history.append({"role": "user", "parts": [h_msg]})
        chat_history.append({"role": "model", "parts": [h_res]})
    
    try:
        chat = model.start_chat(history=chat_history)
        response = await chat.send_message_async(message)
        # Tarixni DB ga yozamiz
        await log_ai_history(user_id, message, response.text)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in chat_with_gemini: {e}")
        if "quota" in str(e).lower():
            return "Kechirasiz, AI xizmati limiti tugagan. Iltimos bir ozdan so'ng harakat qilib ko'ring."
        return f"Xatolik yuz berdi. Savolingizga hozircha javob bera olmayman. (Xato: {e})"
