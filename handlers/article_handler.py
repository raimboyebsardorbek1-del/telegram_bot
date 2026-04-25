from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, price_selection_kb, cancel_kb, payment_method_kb
from database import check_free_usage, mark_free_usage, create_order
from services.ai_service import generate_article
from services.click_service import generate_click_url
from utils import create_docx
from config import PRICES
import uuid

router = Router()

class ArticleState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_university = State()
    waiting_for_author = State()
    waiting_for_tier = State()

@router.callback_query(F.data == "menu_article")
async def start_article_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ArticleState.waiting_for_topic)
    await callback.message.edit_text(
        "📚 Maqola yozish bo'limi.\n\nQaysi mavzuda maqola yozmoqchisiz? Mavzuni kiriting:",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(ArticleState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(ArticleState.waiting_for_university)
    await message.answer("Oliygohingiz nomini kiriting (Titul uchun):", reply_markup=cancel_kb())

@router.message(ArticleState.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await state.set_state(ArticleState.waiting_for_author)
    await message.answer("Muallif ism-familiyasini kiriting:", reply_markup=cancel_kb())

@router.message(ArticleState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(ArticleState.waiting_for_tier)
    await message.answer(
        "Maqola necha bet bo'lishini tanlang:",
        reply_markup=price_selection_kb("maqola")
    )

@router.callback_query(ArticleState.waiting_for_tier, F.data.startswith("price_maqola_"))
async def process_tier(callback: CallbackQuery, state: FSMContext):
    tier = callback.data.split("_")[-1] # e.g. "3-10"
    amount = PRICES["maqola"][tier]
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Check Free Usage
    is_free = await check_free_usage(user_id, "maqola")
    
    if is_free:
        await callback.message.edit_text(
            f"🎁 <b>Sizda 1 marta bepul foydalanish mavjud!</b>\n\n"
            f"Mavzu: {data['topic']}\n"
            f"Sahifa: {tier} bet\n\n"
            "⏳ Ish tayyorlanmoqda, iltimos kuting...",
            parse_mode="HTML"
        )
        await mark_free_usage(user_id, "maqola")
        await generate_and_send_article(callback.message, data, tier, user_id)
        await state.clear()
    else:
        # Create Order and Show Click Link
        import json
        order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
        params = json.dumps({"topic": data["topic"], "university": data["university"], "author": data["author"]})
        
        await create_order(order_id, user_id, "maqola", tier, amount, params)
        
        click_url = generate_click_url(order_id, amount)
        
        text = (
            f"📄 <b>Tanlandi:</b> {tier} bet\n"
            f"💰 <b>Narx:</b> {amount:,} so'm\n\n"
            "To'lov usulini tanlang. Muvaffaqiyatli to'lovdan so'ng maqola avtomatik yuboriladi."
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_method_kb(order_id, click_url))
        await state.clear()
    
    await callback.answer()

async def generate_and_send_article(message: Message, data: dict, tier: str, user_id: int):
    topic = data.get("topic")
    university = data.get("university")
    author = data.get("author")
    
    try:
        article_text = await generate_article(topic, tier, "O'zbek")
        file_path = create_docx(article_text, f"Maqola_{user_id}.docx", university, author, topic, "MAQOLA")
        await message.answer_document(
            FSInputFile(file_path),
            caption=f"✅ '{topic}' mavzusidagi maqola tayyor!"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
