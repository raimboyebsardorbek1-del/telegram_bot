from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, price_selection_kb, cancel_kb, payment_method_kb
from database import check_free_usage, mark_free_usage, create_order
from services.ai_service import generate_presentation_text
from services.click_service import generate_click_url
from utils import create_pptx
from config import PRICES, CLICK_CARD_NUMBER
from keyboards.inline_keyboards import payment_confirm_kb
import uuid

router = Router()

class PresentationState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_author = State()
    waiting_for_tier = State()

@router.callback_query(F.data == "menu_presentation")
async def start_presentation_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PresentationState.waiting_for_topic)
    await callback.message.edit_text(
        "📊 Taqdimot tayyorlash bo'limi.\n\nTaqdimot mavzusini kiriting:",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(PresentationState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(PresentationState.waiting_for_author)
    await message.answer("Taqdimotchi ism-familiyasini kiriting:", reply_markup=cancel_kb())

@router.message(PresentationState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(PresentationState.waiting_for_tier)
    await message.answer(
        "Taqdimot necha slayd bo'lishini tanlang:",
        reply_markup=price_selection_kb("taqdimot")
    )

@router.callback_query(PresentationState.waiting_for_tier, F.data.startswith("price_taqdimot_"))
async def process_tier(callback: CallbackQuery, state: FSMContext):
    tier = callback.data.split("_")[-1]
    amount = PRICES["taqdimot"][tier]
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    is_free = await check_free_usage(user_id, "taqdimot")
    
    if is_free:
        await callback.message.edit_text(
            f"🎁 <b>Sizda 1 marta bepul foydalanish mavjud!</b>\n\n"
            f"Mavzu: {data['topic']}\n"
            f"Slaydlar: {tier}\n\n"
            "⏳ Taqdimot tayyorlanmoqda, iltimos kuting...",
            parse_mode="HTML"
        )
        await mark_free_usage(user_id, "taqdimot")
        await generate_and_send_presentation(callback.message, data, tier, user_id)
        await state.clear()
    else:
        import json
        order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
        params = json.dumps({"topic": data["topic"], "author": data["author"]})
        await create_order(order_id, user_id, "taqdimot", tier, amount, params)
        
        text = (
            f"📊 <b>Tanlandi:</b> {tier} slayd\n"
            f"💰 <b>Narx:</b> {amount:,} so'm\n\n"
            f"💳 <b>Karta orqali to'lov</b>\n"
            f"Quyidagi karta raqamiga to'lovni amalga oshiring:\n"
            f"<code>{CLICK_CARD_NUMBER}</code>\n\n"
            f"To'lovni amalga oshirgandan so'ng, <b>\"To'ladim\"</b> tugmasini bosing."
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_confirm_kb(order_id))
        await state.clear()
    await callback.answer()

async def generate_and_send_presentation(message: Message, data: dict, tier: str, user_id: int):
    topic = data.get("topic")
    author = data.get("author")
    
    try:
        content = await generate_presentation_text(topic, tier)
        file_path = create_pptx(content, f"Taqdimot_{user_id}.pptx", topic, author)
        await message.answer_document(
            FSInputFile(file_path),
            caption=f"✅ '{topic}' mavzusidagi taqdimot tayyor!"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
