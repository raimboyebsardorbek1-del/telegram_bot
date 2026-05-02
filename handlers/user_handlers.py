from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, cancel_kb, payment_confirm_kb, admin_order_approval_kb
from database import add_user, get_balance, get_order
from config import CLICK_CARD_NUMBER, ADMIN_ID
import logging

router = Router()

class PaymentState(StatesGroup):
    waiting_for_proof = State()

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



@router.callback_query(F.data.startswith("paid_"))
async def payment_sent_handler(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.replace("paid_", "")

    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    if order['status'] == 'paid':
        await callback.answer("✅ Bu buyurtma allaqachon tasdiqlangan!", show_alert=True)
        return

    await state.set_state(PaymentState.waiting_for_proof)
    await state.update_data(payment_id=order_id)

    await callback.message.edit_text(
        "📎 <b>To'lov chekini yuboring</b>\n\n"
        "Iltimos, to'lov tasdig'ini (screenshot) rasm formatida yuboring.\n\n"
        "⚠️ Faqat <b>rasm (photo)</b> qabul qilinadi.",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await callback.answer()

@router.message(PaymentState.waiting_for_proof, F.photo)
async def receive_payment_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("payment_id")
    user = message.from_user

    file_id = message.photo[-1].file_id
    order = await get_order(order_id)
    
    if not order:
        await message.answer("❌ Buyurtma topilmadi.", reply_markup=main_menu_kb())
        await state.clear()
        return

    # Send to admin
    username_str = f"@{user.username}" if user.username else "Username yo'q"
    caption = (
        f"🔔 <b>Yangi to'lov cheki keldi! (Qo'lda to'lov)</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"📱 Username: {username_str}\n\n"
        f"💳 Order ID: <code>{order_id}</code>\n"
        f"📦 Buyurtma: {order['service_type']} ({order['pages']})\n"
        f"💰 Miqdor: <b>{order['amount']:,} so'm</b>\n\n"
        f"Rasmni ko'rib tasdiqlang yoki rad eting:"
    )

    try:
        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=admin_order_approval_kb(order_id)
        )
        await message.answer(
            "✅ <b>Chekingiz yuborildi!</b>\n\n"
            "Admin to'lovingizni tekshirib, tez orada tasdiqlaydi.\n"
            "Tasdiqlangandan so'ng hujjat avtomatik yuboriladi.",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception as e:
        logging.error(f"Failed to send proof to admin: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi. Iltimos, @urdu_admin ga murojaat qiling.",
            reply_markup=main_menu_kb()
        )

    await state.clear()

@router.message(PaymentState.waiting_for_proof)
async def proof_not_photo(message: Message):
    await message.answer(
        "⚠️ Iltimos, faqat <b>rasm (screenshot)</b> yuboring!\n"
        "Matn, fayl yoki boshqa formatlar qabul qilinmaydi.",
        parse_mode="HTML"
    )
