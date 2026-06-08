from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, price_selection_kb, cancel_kb
from utils import parse_pages_input, handle_order_payment
from config import PRICES

router = Router()

class PresentationState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_subject = State()
    waiting_for_tier = State()

@router.callback_query(F.data == "menu_presentation")
async def start_presentation_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PresentationState.waiting_for_topic)
    await callback.message.edit_text(
        "📊 <b>Taqdimot tayyorlash bo'limi</b>\n\nTaqdimot mavzusini kiriting:",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(PresentationState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(PresentationState.waiting_for_subject)
    await message.answer(
        "Qaysi fan uchun tayyorlanmoqda? Fan nomini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(PresentationState.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(PresentationState.waiting_for_tier)
    await message.answer(
        "Taqdimot necha slayd bo'lishini tanlang yoki yozing (Masalan: 10):",
        reply_markup=price_selection_kb("taqdimot")
    )

async def finish_presentation_order(event, state: FSMContext, tier: str, bot, user_id: int):
    data = await state.get_data()
    amount = PRICES["taqdimot"][tier]
    
    params_dict = {
        "topic": data["topic"],
        "subject": data["subject"],
        "author": data.get("author", event.from_user.full_name)
    }
    
    await state.clear()
    await handle_order_payment(bot, user_id, "taqdimot", tier, amount, params_dict, event)

@router.callback_query(PresentationState.waiting_for_tier, F.data.startswith("price_taqdimot_"))
async def process_tier_callback(callback: CallbackQuery, state: FSMContext):
    tier = callback.data.split("_")[-1]
    await finish_presentation_order(callback.message, state, tier, callback.message.bot, callback.from_user.id)
    await callback.answer()

@router.message(PresentationState.waiting_for_tier)
async def process_tier_text(message: Message, state: FSMContext):
    tier = parse_pages_input("taqdimot", message.text)
    await finish_presentation_order(message, state, tier, message.bot, message.from_user.id)
