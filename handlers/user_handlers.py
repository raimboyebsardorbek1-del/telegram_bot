from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import main_menu_kb, cancel_kb
from database import add_user, get_balance
import logging

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Extract referral code if exists (start parameter)
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None
    
    await add_user(
        user_id=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username
    )
    
    # Log referral if needed (optional)
    if referrer_id:
        logging.info(f"User {message.from_user.id} joined via referral {referrer_id}")

    text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        f"Men sizning shaxsiy AI yordamchingizman. "
        f"Hujjatlar yozish, mustaqil ishlar va taqdimotlar tayyorlashda yordam beraman.\n\n"
        f"🎁 <b>Har bir xizmatdan 1 marta bepul foydalanishingiz mumkin!</b>\n\n"
        f"Quyidagi menudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Amaliyot bekor qilindi.\n\nAsosiy menyu:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_balance")
async def balance_handler(callback: CallbackQuery):
    balance = await get_balance(callback.from_user.id)
    text = (
        f"💰 <b>Sizning balansingiz</b>\n\n"
        f"Hisobingizda: <b>{balance:,} so'm</b>\n\n"
        f"Taklif: Do'stlaringizni taklif qiling va bepul foydalanish imkoniyatini oshiring!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "menu_invite")
async def invite_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await callback.message.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        "👥 <b>Do'stlarni taklif qiling!</b>\n\n"
        "Botimizni do'stlaringizga tavsiya qiling:\n\n"
        f"<code>{bot_link}</code>\n\n"
        "Ushbu havolani nusxalab, do'stlaringizga yuboring! ✨"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "menu_contact")
async def contact_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 <b>Aloqa bo'limi</b>\n\n"
        "Admin: @urdu_admin\n"
        "Texnik yordam va takliflar uchun yozing.\n\n"
        "Asosiy menyuga qaytish:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
    await callback.answer()
