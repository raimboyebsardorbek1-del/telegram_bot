from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import cancel_kb, main_menu_kb
from services.ai_service import generate_presentation_text
from utils import create_pptx
from database import check_subscription

router = Router()

class PresentationState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_slides = State()
    waiting_for_author = State()

@router.callback_query(F.data == "menu_presentation")
async def start_presentation_flow(callback: CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Sizda faol obuna yo'q! Iltimos, obuna sotib oling.", show_alert=True)
        return
        
    await state.set_state(PresentationState.waiting_for_topic)
    await callback.message.edit_text(
        "📊 Taqdimot bo'limi. Mavzuni kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(PresentationState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(PresentationState.waiting_for_slides)
    await message.answer(
        "Slaydlar sonini kiriting (Masalan: 10):",
        reply_markup=cancel_kb()
    )

@router.message(PresentationState.waiting_for_slides)
async def process_slides(message: Message, state: FSMContext):
    await state.update_data(slides=message.text)
    await state.set_state(PresentationState.waiting_for_author)
    await message.answer(
        "Taqdimotchi ism-familiyasini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(PresentationState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    author = message.text
    data = await state.get_data()
    topic = data.get("topic")
    slides = data.get("slides")
    
    await message.answer("⏳ Taqdimot tayyorlanmoqda, iltimos kuting...")
    
    try:
        presentation_text = await generate_presentation_text(topic, slides)
        file_path = create_pptx(presentation_text, f"Taqdimot_{message.from_user.id}.pptx", topic, author)
        await message.answer_document(
            FSInputFile(file_path),
            caption=f"✅ '{topic}' mavzusidagi taqdimot tayyor!"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await state.clear()
