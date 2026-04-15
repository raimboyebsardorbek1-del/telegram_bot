from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import cancel_kb, main_menu_kb
from services.ai_service import chat_with_gemini
from utils import send_split_message

router = Router()

class AIChatState(StatesGroup):
    chatting = State()

@router.callback_query(F.data == "menu_ai")
async def start_ai_chat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIChatState.chatting)
    await callback.message.edit_text(
        "🤖 AI yordamchi bilan suhbatdasiz. Savolingizni yozing (chiqish uchun 'Bekor qilish' tugmasini bosing):",
        reply_markup=cancel_kb()
    )

@router.message(AIChatState.chatting)
async def process_ai_message(message: Message):
    # If user wants to quit, they can use provide buttons, but we also handle text-based quit?
    # For now, we follow the current design where 'cancel' callback handles exit.
    
    wait_msg = await message.answer("⏳ O'ylanmoqda...")
    
    try:
        response = await chat_with_gemini(message.from_user.id, message.text)
        await wait_msg.delete()
        await send_split_message(message, response)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Kechirasiz, xatolik yuz berdi: {e}")
