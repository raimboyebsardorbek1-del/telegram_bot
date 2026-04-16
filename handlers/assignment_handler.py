from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import assignment_difficulty_kb, cancel_kb, main_menu_kb
from services.ai_service import generate_assignment
from utils import send_split_message, create_docx

router = Router()

class AssignmentState(StatesGroup):
    waiting_for_subject = State()
    waiting_for_university = State()
    waiting_for_author = State()
    waiting_for_pages = State()
    waiting_for_difficulty = State()

@router.callback_query(F.data == "menu_assignment")
async def start_assignment_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AssignmentState.waiting_for_subject)
    await callback.message.edit_text(
        "📝 Mustaqil ish uchun fanni (yoki mavzuni) kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(AssignmentState.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(AssignmentState.waiting_for_university)
    await message.answer(
        "Oliygohingiz nomini kiriting (Titul varag'i uchun):",
        reply_markup=cancel_kb()
    )

@router.message(AssignmentState.waiting_for_university)
async def process_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await state.set_state(AssignmentState.waiting_for_author)
    await message.answer(
        "Muallifning (talabaning) ism-familiyasini kiriting:",
        reply_markup=cancel_kb()
    )

@router.message(AssignmentState.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(AssignmentState.waiting_for_pages)
    await message.answer(
        "Mustaqil ish taxminan necha bet bo'lishi kerak? (Masalan: 5-10 bet):",
        reply_markup=cancel_kb()
    )

@router.message(AssignmentState.waiting_for_pages)
async def process_pages(message: Message, state: FSMContext):
    await state.update_data(pages=message.text)
    await state.set_state(AssignmentState.waiting_for_difficulty)
    await message.answer(
        "Qiyinlik darajasini tanlang:",
        reply_markup=assignment_difficulty_kb()
    )

@router.callback_query(AssignmentState.waiting_for_difficulty, F.data.startswith("diff_"))
async def process_difficulty(callback: CallbackQuery, state: FSMContext):
    diff_map = {"diff_easy": "Oson", "diff_medium": "O‘rta", "diff_hard": "Qiyin"}
    difficulty = diff_map.get(callback.data)
    
    data = await state.get_data()
    subject = data.get("subject")
    pages = data.get("pages")
    university = data.get("university")
    author = data.get("author")
    
    await callback.message.edit_text(f"⏳ '{subject}' fanidan {pages} betli, {difficulty} darajadagi mustaqil ish tayyorlanmoqda. Iltimos kuting...")
    
    try:
        assignment_response = await generate_assignment(subject, pages, difficulty)
        await send_split_message(callback.message, assignment_response)
        
        # Word faylni yaratish va yuborish
        file_path = create_docx(assignment_response, f"Mustaqil_ish_{callback.from_user.id}.docx", university, author, subject, "MUSTAQIL ISH")
        await callback.message.answer_document(
            FSInputFile(file_path),
            caption="📄 Mustaqil ishning titul varag'i va rejasi bilan Word varianti"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Kechirasiz, topshiriq tayyorlashda xatolik yuz berdi: {e}")
    
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await state.clear()
