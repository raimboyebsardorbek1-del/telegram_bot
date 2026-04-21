from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import article_language_kb, cancel_kb, main_menu_kb
from services.ai_service import generate_article
from utils import send_split_message, create_docx
from database import check_subscription

router = Router()

class ArticleState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_university = State()
    waiting_for_author = State()
    waiting_for_pages = State()
    waiting_for_language = State()

@router.callback_query(F.data == "menu_article")
async def start_article_flow(callback: CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Sizda faol obuna yo'q! Iltimos, obuna sotib oling.", show_alert=True)
        return
        
    await state.set_state(ArticleState.waiting_for_topic)
    await callback.message.edit_text(
        "📚 Yaxshi! Qaysi mavzuda maqola yozmoqchisiz? Mavzuni kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(ArticleState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(ArticleState.waiting_for_university)
    await message.answer(
        "Oliygohingiz nomini kiriting (Titul varag'i uchun):",
        reply_markup=cancel_kb()
    )

@router.message(ArticleState.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await state.set_state(ArticleState.waiting_for_author)
    await message.answer(
        "Muallifning (talabaning) ism-familiyasini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(ArticleState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(ArticleState.waiting_for_pages)
    await message.answer(
        "Maqola taxminan necha bet bo'lishi kerak? (Masalan: 3-5 bet):",
        reply_markup=cancel_kb()
    )

@router.message(ArticleState.waiting_for_pages)
async def process_pages(message: Message, state: FSMContext):
    await state.update_data(pages=message.text)
    await state.set_state(ArticleState.waiting_for_language)
    await message.answer(
        "Endi maqola qaysi tilda bo'lishini tanlang:",
        reply_markup=article_language_kb()
    )

@router.callback_query(ArticleState.waiting_for_language, F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang_map = {"lang_uz": "O'zbek", "lang_ru": "Rus", "lang_en": "Ingliz"}
    language = lang_map.get(callback.data)
    
    data = await state.get_data()
    topic = data.get("topic")
    pages = data.get("pages")
    university = data.get("university")
    author = data.get("author")
    
    await callback.message.edit_text(f"⏳ '{topic}' mavzusida {pages} betli, {language} tilida maqola tayyorlanmoqda. Iltimos kuting...")
    
    try:
        article = await generate_article(topic, pages, language)
        
        # Word faylni yaratish va yuborish
        file_path = create_docx(article, f"Maqola_{callback.from_user.id}.docx", university, author, topic, "MAQOLA")
        await callback.message.answer_document(
            FSInputFile(file_path),
            caption="📄 Maqolaning titul varag'i va rejasi bilan Word varianti"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Kechirasiz, maqola tayyorlashda xatolik yuz berdi: {e}")
    
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await state.clear()
