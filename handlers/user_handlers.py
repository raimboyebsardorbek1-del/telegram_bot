from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import (
    main_menu_kb,
    cancel_kb,
    payment_confirm_kb,
    admin_order_approval_kb,
    pay_balance_kb
)
from database import (
    add_user,
    get_balance,
    get_order,
    get_all_users,
    add_referral,
    update_balance,
    get_referral_stats,
    update_order_status
)
from config import CLICK_CARD_NUMBER, ADMIN_ID
from services.generation_service import fulfill_order
import logging

router = Router()

class PaymentState(StatesGroup):
    waiting_for_proof = State()

async def get_referral_text_and_kb(user_id: int, bot_username: str):
    stats = await get_referral_stats(user_id)
    bot_link = f"https://t.me/{bot_username}?start={user_id}"
    text = (
        "👥 <b>Do'stlarni taklif qilish tizimi</b>\n\n"
        f"Sizning taklif havolangiz:\n<code>{bot_link}</code>\n\n"
        f"Taklifingiz orqali ro'yxatdan o'tganlar: <b>{stats['total_referred']} ta</b>\n"
        f"Buyurtma berganlar: <b>{stats['ordered_referred']} ta</b>\n"
        f"Jami ishlangan bonus: <b>{stats['total_bonus']:,} so'm</b>\n\n"
        "<i>Har bir taklif qilingan do'stingiz ro'yxatdan o'tganda sizga 3,000 so'm bonus berildi. "
        "Do'stingiz birinchi buyurtmasini berganda, ham sizga, ham do'stingizga yana 3,000 so'mdan bonus beriladi!</i>"
    )
    return text

async def get_balance_text(user_id: int) -> str:
    balance = await get_balance(user_id)
    text = (
        f"💰 <b>Sizning balansingiz</b>\n\n"
        f"Hisobingizda: <b>{balance:,} so'm</b>\n\n"
        f"Ushbu mablag'ni bot orqali buyurtmalarni to'lashga ishlatishingiz mumkin.\n"
        f"Balansni ko'paytirish uchun do'stlaringizni taklif qiling!"
    )
    return text

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None
    
    user_id = message.from_user.id
    all_users = await get_all_users()
    is_new = user_id not in all_users
    
    await add_user(
        user_id=user_id,
        name=message.from_user.first_name,
        username=message.from_user.username
    )
    
    if is_new and referrer_id and referrer_id.isdigit():
        ref_id_int = int(referrer_id)
        if ref_id_int != user_id and ref_id_int in all_users:
            await add_referral(ref_id_int, user_id)
            await update_balance(ref_id_int, 3000.0)
            logging.info(f"User {user_id} joined via referral {ref_id_int}. Referrer rewarded with 3000 UZS.")
            try:
                await message.bot.send_message(
                    ref_id_int,
                    f"🎉 Siz taklif qilgan do'stingiz ({message.from_user.first_name}) ro'yxatdan o'tdi!\n"
                    f"Sizga 3,000 so'm bonus berildi."
                )
            except Exception as e:
                logging.error(f"Failed to send referral notification to {ref_id_int}: {e}")

    text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        f"Men sizning shaxsiy AI yordamchingizman. "
        f"Hujjatlar yozish, referat, esse, kurs ishlari va taqdimotlar tayyorlashda yordam beraman.\n\n"
        f"Quyidagi menudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

@router.message(Command("referral"))
async def cmd_referral(message: Message):
    bot_info = await message.bot.get_me()
    text = await get_referral_text_and_kb(message.from_user.id, bot_info.username)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    text = await get_balance_text(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())

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
    text = await get_balance_text(callback.from_user.id)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "menu_invite")
async def invite_handler(callback: CallbackQuery):
    bot_info = await callback.message.bot.get_me()
    text = await get_referral_text_and_kb(callback.from_user.id, bot_info.username)
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

@router.callback_query(F.data.startswith("pay_balance_"))
async def pay_balance_handler(callback: CallbackQuery):
    order_id = callback.data.replace("pay_balance_", "")
    user_id = callback.from_user.id
    
    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return
        
    if order['status'] == 'paid':
        await callback.answer("✅ Bu buyurtma allaqachon to'langan!", show_alert=True)
        return
        
    balance = await get_balance(user_id)
    if balance >= order['amount']:
        await update_balance(user_id, -order['amount'])
        await update_order_status(order_id, 'paid')
        order['status'] = 'paid'
        await callback.message.edit_text("💰 To'lov balansingizdan muvaffaqiyatli yechib olindi! Hujjat tayyorlanmoqda...")
        await callback.answer("To'lov muvaffaqiyatli bajarildi!")
        # Trigger fulfillment asynchronously
        await fulfill_order(callback.message.bot, order)
    else:
        await callback.answer("❌ Balansingizda yetarli mablag' mavjud emas!", show_alert=True)

@router.callback_query(F.data.startswith("pay_card_"))
async def pay_card_handler(callback: CallbackQuery):
    order_id = callback.data.replace("pay_card_", "")
    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return
        
    text = (
        f"💳 <b>To'lov tafsilotlari</b>\n\n"
        f"Buyurtma ID: <code>{order_id}</code>\n"
        f"Xizmat turi: <b>{order['service_type']}</b>\n"
        f"Hajmi: <b>{order['pages']}</b>\n"
        f"To'lov miqdori: <b>{order['amount']:,} so'm</b>\n\n"
        f"To'lovni amalga oshirish uchun quyidagi Click kartaga pul o'tkazing:\n"
        f"<code>{CLICK_CARD_NUMBER}</code>\n\n"
        f"To'lovni amalga oshirgandan so'ng, pastdagi \"✅ To'ladim\" tugmasini bosing va chek rasmini yuboring."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_confirm_kb(order_id))
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
