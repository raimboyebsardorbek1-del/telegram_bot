from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, price_selection_kb, cancel_kb, payment_method_kb
from database import check_free_usage, mark_free_usage, create_order
from services.ai_service import generate_assignment
from services.click_service import generate_click_url
from utils import create_docx
from config import PRICES, CLICK_CARD_NUMBER
from keyboards.inline_keyboards import payment_confirm_kb
import uuid

router = Router()

class AssignmentState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_subject = State()
    waiting_for_university = State()
    waiting_for_teacher = State()
    waiting_for_author = State()
    waiting_for_tier = State()

@router.callback_query(F.data == "menu_assignment")
async def start_assignment_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AssignmentState.waiting_for_topic)
    await callback.message.edit_text(
        "📝 Mustaqil ish bo'limi.\n\nQaysi mavzuda mustaqil ish kerak? Kiriting:",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(AssignmentState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(AssignmentState.waiting_for_subject)
    await message.answer("Qaysi fan uchun tayyorlanmoqda? Fan nomini kiriting:", reply_markup=cancel_kb())

@router.message(AssignmentState.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(AssignmentState.waiting_for_university)
    await message.answer("Muassasa va joylashgan shaharni kiriting (Masalan: Urganch davlat universiteti, Urganch):", reply_markup=cancel_kb())

@router.message(AssignmentState.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await state.set_state(AssignmentState.waiting_for_teacher)
    await message.answer("O'qituvchining ism-familiyasini kiriting:", reply_markup=cancel_kb())

@router.message(AssignmentState.waiting_for_teacher)
async def process_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await state.set_state(AssignmentState.waiting_for_author)
    await message.answer("Talaba (Bajardi) ism-familiyasini kiriting:", reply_markup=cancel_kb())

@router.message(AssignmentState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(AssignmentState.waiting_for_tier)
    await message.answer(
        "Mustaqil ish necha bet bo'lishini tanlang:",
        reply_markup=price_selection_kb("mustaqil")
    )

@router.callback_query(AssignmentState.waiting_for_tier, F.data.startswith("price_mustaqil_"))
async def process_tier(callback: CallbackQuery, state: FSMContext):
    tier = callback.data.split("_")[-1]
    amount = PRICES["mustaqil"][tier]
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    is_free = await check_free_usage(user_id, "mustaqil")
    
    if is_free:
        await callback.message.edit_text(
            f"🎁 <b>Sizda 1 marta bepul foydalanish mavjud!</b>\n\n"
            f"Mavzu: {data['topic']}\n"
            f"Sahifa: {tier} bet\n\n"
            "⏳ Ish tayyorlanmoqda, iltimos kuting...",
            parse_mode="HTML"
        )
        await mark_free_usage(user_id, "mustaqil")
        await generate_and_send_assignment(callback.message, data, tier, user_id)
        await state.clear()
    else:
        import json
        order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
        params = json.dumps({
            "topic": data["topic"], 
            "subject": data.get("subject", "Nomsiz fan"),
            "university": data["university"], 
            "teacher": data.get("teacher", "O'qituvchi"),
            "author": data["author"]
        })
        await create_order(order_id, user_id, "mustaqil", tier, amount, params)
        
        text = (
            f"📄 <b>Tanlandi:</b> {tier} bet\n"
            f"💰 <b>Narx:</b> {amount:,} so'm\n\n"
            f"💳 <b>Karta orqali to'lov</b>\n"
            f"Quyidagi karta raqamiga to'lovni amalga oshiring:\n"
            f"<code>{CLICK_CARD_NUMBER}</code>\n\n"
            f"To'lovni amalga oshirgandan so'ng, <b>\"To'ladim\"</b> tugmasini bosing."
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_confirm_kb(order_id))
        await state.clear()
    await callback.answer()

async def generate_and_send_assignment(message: Message, data: dict, tier: str, user_id: int):
    topic = data.get("topic")
    subject = data.get("subject", "Nomsiz fan")
    university = data.get("university")
    teacher = data.get("teacher", "O'qituvchi")
    author = data.get("author")
    
    try:
        # Since this is a free usage generation, we call our new generation flow
        from services.generation_service import fulfill_order
        # Mock order dict
        import json
        params = json.dumps({
            "topic": topic, 
            "subject": subject,
            "university": university, 
            "teacher": teacher,
            "author": author
        })
        mock_order = {
            "order_id": "FREE_USAGE",
            "user_id": user_id,
            "service_type": "mustaqil",
            "pages": tier,
            "parameters": params
        }
        await fulfill_order(message.bot, mock_order)
        # We don't need to send the file directly here anymore because fulfill_order does it
        # BUT fulfill_order sends to user_id. We can just wait for it.
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
