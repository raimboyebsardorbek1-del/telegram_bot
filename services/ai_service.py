import google.generativeai as genai
import re
from config import GEMINI_API_KEY
from database import log_ai_history, get_user_chat_history
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Gemini API ni kalit bilan sozlash
genai.configure(api_key=GEMINI_API_KEY)

# Global safety settings to minimize content blocking
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Generation config for longer outputs
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Use flash model for performance and lower cost
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=GENERATION_CONFIG,
    safety_settings=SAFETY_SETTINGS
)

async def generate_article(topic: str, pages: str, language: str) -> str:
    """Generates an article based on the topic and language requirements."""
    # Calculate word count based on pages
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 2
    word_target = num_pages * 300

    prompt = (
        f"Write an article about '{topic}' in {language} language. "
        f"The content MUST be at least {word_target} words long to fill exactly {num_pages} pages. "
        f"Structure MUST start with a section titled 'REJA:' which lists the main points. "
        f"Following the REJA section, provide the full content: Kirish, Asosiy qism, and Xulosa."
    )
    try:
        response = await model.generate_content_async(prompt)
        # Check if the response was blocked
        if not response.text:
            return "Kechirasiz, ushbu mavzu bo'yicha ma'lumot generatsiya qilishni AI havfsizlik filtri blokladi."
        return response.text
    except ValueError as ve:
        # ValueError is often raised when response.text is accessed but it's empty/blocked
        import logging
        logging.warning(f"Content blocked or empty: {ve}")
        return "Kechirasiz, mavzu havfsizlik filtrlari tomonidan bloklandi yoki AI javob bera olmadi."
    except Exception as e:
        import logging
        logging.error(f"Error in generate_article: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def generate_assignment(subject: str, pages: str, difficulty: str) -> str:
    """Generates an independent work assignment and its solution."""
    match = re.search(r'(\d+)', str(pages))
    num_pages = int(match.group(1)) if match else 3
    word_target = num_pages * 300

    prompt = (
        f"Create an independent work assignment (mustaqil ish) about '{subject}' "
        f"with '{difficulty}' difficulty. At least {word_target} words long for {num_pages} pages. "
        f"Start with 'REJA:', then provide the complete solution in Uzbek."
    )
    try:
        response = await model.generate_content_async(prompt)
        if not response.text:
            return "Kechirasiz, ushbu mavzu bo'yicha ma'lumot bloklandi."
        return response.text
    except ValueError:
        return "Kechirasiz, mavzu AI filtrlariga to'g'ri kelmadi."
    except Exception as e:
        import logging
        logging.error(f"Error in generate_assignment: {e}")
        return f"Xatolik yuz berdi. (Xato: {e})"

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
