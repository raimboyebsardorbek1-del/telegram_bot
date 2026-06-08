from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import admin_panel_kb, cancel_kb
from config import ADMIN_PASSWORD
from database import get_stats, ban_user, unban_user, get_all_users_details, get_detailed_admin_stats
from services.broadcast_service import broadcast_message

router = Router()

class AdminState(StatesGroup):
    waiting_for_password = State()
    waiting_for_broadcast = State()
    waiting_for_ban = State()
    waiting_for_unban = State()
    is_admin = State()

def verify_pwd(pwd: str) -> bool:
    return pwd == ADMIN_PASSWORD

@router.message(Command("admin"))
async def start_admin(message: Message, state: FSMContext):
    await state.set_state(AdminState.waiting_for_password)
    await message.answer("Admin parolini kiriting:")

@router.message(AdminState.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext):
    if verify_pwd(message.text):
        await message.answer("✅ Admin paneliga xush kelibsiz!", reply_markup=admin_panel_kb())
        await state.set_state(AdminState.is_admin)
        try:
            await message.delete()
        except Exception:
            pass
    else:
        await message.answer("Ruxsatsiz!")
        await state.clear()

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin.state:
        await callback.answer("Ruxsatsiz kirish!", show_alert=True)
        return

    stats = await get_detailed_admin_stats()
    
    active_users_str = ""
    for idx, user in enumerate(stats['active_users'], 1):
        uid, name, username, count = user
        username_str = f"@{username}" if username else "yo'q"
        active_users_str += f"{idx}. {name} (ID: {uid}, {username_str}) - {count} ta buyurtma\n"
        
    if not active_users_str:
        active_users_str = "Hozircha faol foydalanuvchilar yo'q."
        
    text = (
        "📊 <b>Kengaytirilgan Bot Statistikasi</b>\n\n"
        f"👥 Umumiy foydalanuvchilar: <b>{stats['total_users']} ta</b>\n"
        f"📦 Buyurtmalar jami: <b>{stats['total_orders']} ta</b>\n"
        f"✅ To'langan buyurtmalar: <b>{stats['paid_orders']} ta</b>\n\n"
        f"💸 Bugungi tushum: <b>{stats['daily_revenue']:,} so'm</b>\n"
        f"📅 Shu oydagi tushum: <b>{stats['monthly_revenue']:,} so'm</b>\n"
        f"💰 Umumiy tushum: <b>{stats['total_revenue']:,} so'm</b>\n\n"
        f"👥 Taklif qilingan do'stlar (Referallar): <b>{stats['total_referrals']} ta</b>\n"
        f"🎓 Referal orqali birinchi buyurtma berganlar: <b>{stats['ordered_referrals']} ta</b>\n\n"
        f"⭐ <b>Eng faol top 5 foydalanuvchi:</b>\n{active_users_str}"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def ask_broadcast(callback: CallbackQuery, state: FSMContext):
    curr_state = await state.get_state()
    if curr_state != AdminState.is_admin.state:
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
    if curr_state != AdminState.is_admin.state:
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
    if curr_state != AdminState.is_admin.state:
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
