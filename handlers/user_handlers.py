from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.inline_keyboards import main_menu_kb, payment_confirm_kb, admin_payment_approval_kb, cancel_kb
from database import add_user, create_payment, check_subscription, get_payment, save_payment_proof
from config import SUBSCRIPTION_PRICE, SUBSCRIPTION_DAYS, CLICK_CARD_NUMBER, ADMIN_ID
import uuid

router = Router()


class PaymentState(StatesGroup):
    waiting_for_proof = State()  # Screenshot yuborilishini kutish


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Oldingi FSM holatini tozalash
    await state.clear()

    # Foydalanuvchini bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username
    )

    # Obuna holatini tekshirish
    has_sub = await check_subscription(message.from_user.id)
    status_text = "✅ Faol" if has_sub else "❌ Faol emas"

    text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        f"Men sizning shaxsiy AI yordamchingizman.\n"
        f"Quyidagi menudan kerakli bo'limni tanlang:\n\n"
        f"📋 Obuna holatingiz: {status_text}"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Amaliyot bekor qilindi.\n\nAsosiy menyu:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "menu_contact")
async def contact_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 Aloqa bo'limi:\n\n"
        "Admin: @urdu_admin\n"
        "Yordam uchun biz bilan bog'laning!\n\n"
        "Asosiy menyuga qaytish:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "menu_subscribe")
async def subscribe_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Noyob to'lov IDsini yaratish
    payment_id = str(uuid.uuid4())[:12].upper()
    amount = SUBSCRIPTION_PRICE

    # Kutayotgan to'lovni bazaga saqlash
    await create_payment(payment_id, user_id, amount)

    text = (
        f"💳 <b>Obuna sotib olish</b>\n\n"
        f"📦 Narxi: <b>{amount:,} so'm</b>\n"
        f"📅 Muddat: <b>{SUBSCRIPTION_DAYS} kun</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏦 <b>Click orqali to'lov:</b>\n\n"
        f"💳 Karta raqami:\n"
        f"<code>{CLICK_CARD_NUMBER}</code>\n\n"
        f"💰 Miqdor: <b>{amount:,} so'm</b>\n\n"
        f"📝 <b>Muhim!</b> To'lov izohiga quyidagi kodni yozing:\n"
        f"<code>{payment_id}</code>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ To'lovni amalga oshirgandan so'ng \"To'ladim\" tugmasini bosing."
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=payment_confirm_kb(payment_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("paid_"))
async def payment_sent_handler(callback: CallbackQuery, state: FSMContext):
    payment_id = callback.data.replace("paid_", "")

    # To'lovni tekshirish
    payment = await get_payment(payment_id)
    if not payment:
        await callback.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    if payment['status'] == 'paid':
        await callback.answer("✅ Bu to'lov allaqachon tasdiqlangan!", show_alert=True)
        return

    # FSM holatga o'tish va payment_id ni saqlash
    await state.set_state(PaymentState.waiting_for_proof)
    await state.update_data(payment_id=payment_id)

    await callback.message.edit_text(
        "📎 <b>To'lov chekini yuboring</b>\n\n"
        "Iltimos, Click ilovasidagi to'lov tasdig'ini screenshot qilib yuboring.\n\n"
        "⚠️ Faqat <b>rasm (photo)</b> qabul qilinadi.",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await callback.answer()


@router.message(PaymentState.waiting_for_proof, F.photo)
async def receive_payment_proof(message: Message, state: FSMContext):
    """Foydalanuvchi screenshot yubordi — file_id ni saqlash va adminga jo'natish."""
    data = await state.get_data()
    payment_id = data.get("payment_id")
    user = message.from_user

    # Eng yuqori sifatli rasmning file_id sini olish
    file_id = message.photo[-1].file_id

    # Bazaga saqlash
    await save_payment_proof(payment_id, file_id)

    # To'lov ma'lumotlarini olish
    payment = await get_payment(payment_id)

    # Adminga rasm + ma'lumot yuborish
    username_str = f"@{user.username}" if user.username else "Username yo'q"
    caption = (
        f"🔔 <b>Yangi to'lov cheki keldi!</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"📱 Username: {username_str}\n\n"
        f"💳 To'lov ID: <code>{payment_id}</code>\n"
        f"💰 Miqdor: <b>{payment['amount']:,} so'm</b>\n\n"
        f"Rasmni ko'rib tasdiqlang yoki rad eting:"
    )

    try:
        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=admin_payment_approval_kb(payment_id)
        )
        await message.answer(
            "✅ <b>Chekingiz yuborildi!</b>\n\n"
            "Admin to'lovingizni tekshirib, tez orada tasdiqlaydi.\n"
            "Odatda 5–15 daqiqa ichida javob olasiz. 🙏",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception:
        await message.answer(
            "❌ Xatolik yuz berdi. Iltimos, @urdu_admin ga murojaat qiling.",
            reply_markup=main_menu_kb()
        )

    await state.clear()


@router.message(PaymentState.waiting_for_proof)
async def proof_not_photo(message: Message):
    """Foydalanuvchi rasm o'rniga boshqa narsa yubordi."""
    await message.answer(
        "⚠️ Iltimos, faqat <b>rasm (screenshot)</b> yuboring!\n"
        "Matn, fayl yoki boshqa formatlar qabul qilinmaydi.",
        parse_mode="HTML"
    )



