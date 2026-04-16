from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import admin_panel_kb, cancel_kb
from config import ADMIN_PASSWORD
from database import get_stats, ban_user, unban_user, get_all_users_details
from services.broadcast_service import broadcast_message
# Admin paneli haqidagi barcha amallarni boshqaruvchi fayl.
# Parolni tekshirish uchun utils.py dagi hash_password funksiyasidan foydalanish mumkin.
from utils import hash_password

router = Router()

class AdminState(StatesGroup):
    """Admin paneli uchun holatlar (FSM)."""
    waiting_for_password = State()
    waiting_for_broadcast = State()
    waiting_for_ban = State()
    waiting_for_unban = State()
    is_admin = State()

def verify_pwd(pwd: str) -> bool:
    """Parolni tekshiradi. Hozircha oddiy matn ko'rinishida solishtiradi."""
    return pwd == ADMIN_PASSWORD

@router.message(Command("admin"))
async def start_admin(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_for_password)
    await message.answer("Admin parolini kiriting:")

@router.message(AdminState.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext):
    """Kiritilgan parolni tekshiradi va adminga ruxsat beradi."""
    if verify_pwd(message.text):
        await message.answer("✅ Admin paneliga xush kelibsiz!", reply_markup=admin_panel_kb())
        await state.set_state(AdminState.is_admin)
        # Xavfsizlik uchun parol yozilgan xabarni o'chirib tashlaymiz
        try:
            await message.delete()
        except Exception:
            pass
    else:
        await message.answer("Ruxsat yo‘q")
        await state.clear()

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin:
        await callback.answer("Ruxsatsiz kirish!", show_alert=True)
        return

    stats = await get_stats()
    text = (
        "📊 Bot Statistikasi:\n\n"
        f"👥 Umumiy foydalanuvchilar: {stats['users']}\n"
        f"🤖 AI so'rovlar soni: {stats['requests']}\n"
        f"🚫 Ban qilinganlar: {stats['banned']}"
    )
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_users_list")
async def show_users_list(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin:
        await callback.answer("Ruxsatsiz!", show_alert=True)
        return

    users = await get_all_users_details()
    if not users:
        await callback.message.answer("Foydalanuvchilar mavjud emas.")
        await callback.answer()
        return

    text = "👥 Foydalanuvchilar ro'yxati:\n\n"
    for user_id, name, username in users:
        username_str = f"@{username}" if username else "Username yo'q"
        text += f"🆔 {user_id} - {username_str} ({name})\n"
        
        # Telegram xabar limiti (4096) dan oshib ketmasligi uchun tekshiramiz
        if len(text) > 3900:
            await callback.message.answer(text)
            text = "" # Keyingi qism uchun tozalaymiz
            
    if text:
        await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def ask_broadcast(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin:
        await callback.answer("Ruxsatsiz", show_alert=True)
        return
        
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:", reply_markup=cancel_kb())
    await callback.answer()

@router.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    await message.answer("⏳ Xabar yuborilmoqda...")
    success, fail = await broadcast_message(message.bot, message.text)
    await message.answer(f"✅ Xabar {success} ta foydalanuvchiga yuborildi.\n❌ Xatoliklar: {fail} ta.", reply_markup=admin_panel_kb())
    await state.set_state(AdminState.is_admin)

@router.callback_query(F.data == "admin_ban")
async def ask_ban(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin:
        await callback.answer("Ruxsatsiz", show_alert=True)
        return
        
    await state.set_state(AdminState.waiting_for_ban)
    await callback.message.answer("Ban qilinadigan foydalanuvchi ID sini kiriting:", reply_markup=cancel_kb())
    await callback.answer()

@router.message(AdminState.waiting_for_ban)
async def process_ban(message: Message, state: FSMContext):
    if message.text.isdigit():
        user_id = int(message.text)
        await ban_user(user_id)
        await message.answer(f"✅ User {user_id} ban qilindi.", reply_markup=admin_panel_kb())
    else:
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak.", reply_markup=admin_panel_kb())
    await state.set_state(AdminState.is_admin)

@router.callback_query(F.data == "admin_unban")
async def ask_unban(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin:
        await callback.answer("Ruxsatsiz", show_alert=True)
        return
        
    await state.set_state(AdminState.waiting_for_unban)
    await callback.message.answer("Ban'dan chiqariladigan foydalanuvchi ID sini kiriting:", reply_markup=cancel_kb())
    await callback.answer()

@router.message(AdminState.waiting_for_unban)
async def process_unban(message: Message, state: FSMContext):
    if message.text.isdigit():
        user_id = int(message.text)
        await unban_user(user_id)
        await message.answer(f"✅ User {user_id} ban'dan chiqarildi.", reply_markup=admin_panel_kb())
    else:
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak.", reply_markup=admin_panel_kb())
    await state.set_state(AdminState.is_admin)
