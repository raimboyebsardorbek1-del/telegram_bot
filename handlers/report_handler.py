from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import cancel_kb, main_menu_kb
from services.ai_service import generate_report
from utils import create_docx
from database import check_subscription

router = Router()

class ReportState(StatesGroup):
    waiting_for_topic = State()
    waiting_for_university = State()
    waiting_for_author = State()
    waiting_for_pages = State()

@router.callback_query(F.data == "menu_report")
async def start_report_flow(callback: CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.from_user.id):
        await callback.answer("Sizda faol obuna yo'q! Iltimos, obuna sotib oling.", show_alert=True)
        return
        
    await state.set_state(ReportState.waiting_for_topic)
    await callback.message.edit_text(
        "📄 Referat bo'limi. Mavzuni kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(ReportState.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(ReportState.waiting_for_university)
    await message.answer(
        "Oliygohingiz nomini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(ReportState.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await state.set_state(ReportState.waiting_for_author)
    await message.answer(
        "Muallif ism-familiyasini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(ReportState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(ReportState.waiting_for_pages)
    await message.answer(
        "Referat necha bet bo'lishi kerak? (Masalan: 10-15):",
        reply_markup=cancel_kb()
    )

@router.message(ReportState.waiting_for_pages)
async def process_pages(message: Message, state: FSMContext):
    pages = message.text
    data = await state.get_data()
    topic = data.get("topic")
    university = data.get("university")
    author = data.get("author")
    
    await message.answer("⏳ Referat tayyorlanmoqda, iltimos kuting...")
    
    try:
        report_text = await generate_report(topic, pages)
        file_path = create_docx(report_text, f"Referat_{message.from_user.id}.docx", university, author, topic, "REFERAT")
        await message.answer_document(
            FSInputFile(file_path),
            caption=f"✅ '{topic}' mavzusidagi referat tayyor!"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await state.clear()
