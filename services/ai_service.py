import google.generativeai as genai
from config import GEMINI_API_KEY
from database import log_ai_history, get_user_chat_history

# Configure the Gemini API with the initialized key
genai.configure(api_key=GEMINI_API_KEY)

# Using flash model for best performance and cost
# Using flash model for better quota and performance
model = genai.GenerativeModel('gemini-flash-latest')

async def generate_article(topic: str, pages: str, language: str) -> str:
    """Generates an article using Gemini based on topic and language requirements."""
    prompt = (
        f"Write an article about '{topic}' in {language} language. "
        f"The article should be approximately {pages} pages long. "
        f"Structure it exactly like this: Sarlavha (Title), Kirish (Introduction), "
        f"Asosiy qism (Main part), Xulosa (Conclusion)."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_article: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def generate_assignment(subject: str, pages: str, difficulty: str) -> str:
    """Generates an assignment and solution."""
    prompt = (
        f"Create an independent work assignment (mustaqil ish) about the subject '{subject}' "
        f"with '{difficulty}' difficulty level. The target length of the assignment should be "
        f"approximately {pages} pages. Provide the assignment task first, and then the complete "
        f"solution/content below it. The entire response must be in Uzbek."
    )
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in generate_assignment: {e}")
        return f"Xatolik yuz berdi. Iltimos keyinroq qayta urunib ko'ring. (Xato: {e})"

async def chat_with_gemini(user_id: int, message: str) -> str:
    """Chats with Gemini, maintaining a short history per user from DB."""
    # Fetch recent history (chronological) from db
    history = await get_user_chat_history(user_id, limit=7)
    
    chat_history = []
    for h_msg, h_res in history:
        chat_history.append({"role": "user", "parts": [h_msg]})
        chat_history.append({"role": "model", "parts": [h_res]})
    
    try:
        chat = model.start_chat(history=chat_history)
        response = await chat.send_message_async(message)
        # Log response mapped to user
        await log_ai_history(user_id, message, response.text)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Error in chat_with_gemini: {e}")
        if "quota" in str(e).lower():
            return "Kechirasiz, AI xizmati limiti tugagan. Iltimos bir ozdan so'ng harakat qilib ko'ring."
        return f"Xatolik yuz berdi. Savolingizga hozircha javob bera olmayman. (Xato: {e})"
