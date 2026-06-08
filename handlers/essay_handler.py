from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, price_selection_kb, cancel_kb
from utils import parse_pages_input, handle_order_payment
from config import PRICES

router = Router()

class EssayState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_subject = State()
    waiting_for_tier = State()

@router.callback_query(F.data == "menu_essay")
async def start_essay_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EssayState.waiting_for_topic)
    await callback.message.edit_text(
        "✍️ <b>Esse yozish bo'limi</b>\n\nEsse mavzusini kiriting:",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(EssayState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(EssayState.waiting_for_subject)
    await message.answer(
        "Qaysi fan uchun tayyorlanmoqda? Fan nomini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(EssayState.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(EssayState.waiting_for_tier)
    await message.answer(
        "Esse necha bet bo'lishini tanlang yoki yozing (Masalan: 4):",
        reply_markup=price_selection_kb("esse")
    )

async def finish_essay_order(event, state: FSMContext, tier: str, bot, user_id: int):
    data = await state.get_data()
    amount = PRICES["esse"][tier]
    
    params_dict = {
        "topic": data["topic"],
        "subject": data["subject"],
        "author": data.get("author", event.from_user.full_name)
    }
    
    await state.clear()
    await handle_order_payment(bot, user_id, "esse", tier, amount, params_dict, event)

@router.callback_query(EssayState.waiting_for_tier, F.data.startswith("price_esse_"))
async def process_tier_callback(callback: CallbackQuery, state: FSMContext):
    tier = callback.data.split("_")[-1]
    await finish_essay_order(callback.message, state, tier, callback.message.bot, callback.from_user.id)
    await callback.answer()

@router.message(EssayState.waiting_for_tier)
async def process_tier_text(message: Message, state: FSMContext):
    tier = parse_pages_input("esse", message.text)
    await finish_essay_order(message, state, tier, message.bot, message.from_user.id)
