from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import main_menu_kb
from database import add_user, is_banned

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handles the /start command and sends the main menu."""
    # Clear FSM state if user was in another process
    await state.clear()
    
    # Bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username
    )
    
    text = (
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Men sizning shaxsiy AI yordamchigizman. Quyidagi menudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=main_menu_kb())

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancels the current action and returns to the main menu."""
    await state.clear()
    await callback.message.edit_text("Amal bekor qilindi.\n\nAsosiy menyu:", reply_markup=main_menu_kb())

@router.callback_query(F.data == "menu_contact")
async def contact_handler(callback: CallbackQuery):
    """Shows contact information and support."""
    await callback.message.edit_text(
        "📞 Markaziy aloqa bo'limi:\n\n"
        "Admin: +998772243435\n"
        "Yordam uchun biz bilan bog'laning!\n\n"
        "Asosiy menyuga qaytish:",
        reply_markup=main_menu_kb()
    )
