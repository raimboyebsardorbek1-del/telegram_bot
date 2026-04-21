from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import main_menu_kb
from database import add_user, is_banned, create_payment, check_subscription
import uuid
from config import SUBSCRIPTION_PRICE, SUBSCRIPTION_DAYS

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # FSM state ni tozalash, agar user boshqa holatda bo'lsa
    await state.clear()
    
    # Bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username
    )
    
    # Status check
    has_sub = await check_subscription(message.from_user.id)
    status_text = "✅ Faol" if has_sub else "❌ Faol emas"

    text = (
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"Men sizning shaxsiy AI yordamchingizman. Quyidagi menudan kerakli bo'limni tanlang:\n\n"
        f"Obuna holati: {status_text}"
    )
    await message.answer(text, reply_markup=main_menu_kb())

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Amaliyot bekor qilindi.\n\nAsosiy menyu:", reply_markup=main_menu_kb())

@router.callback_query(F.data == "menu_contact")
async def contact_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 Markaziy aloqa bo'limi:\n\n"
        "Admin: +998901234567\n"
        "Yordam uchun biz bilan bog'laning!\n\n"
        "Asosiy menyuga qaytish:",
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "menu_subscribe")
async def subscribe_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    payment_id = str(uuid.uuid4())
    amount = SUBSCRIPTION_PRICE
    
    # Save pending payment
    await create_payment(payment_id, user_id, amount)
    
    # Send instructions
    payme_link = "https://payme.uz/fallback/merchant/?m=ID_OF_MERCHANT&ac.payment_id=" + payment_id + f"&a={amount*100}"
    
    text = (
        f"💳 <b>Obuna sotib olish</b>\n\n"
        f"Narxi: {amount:,.0f} so'm ({SUBSCRIPTION_DAYS} kun)\n\n"
        f"1. Quyidagi havolaga o'ting.\n"
        f"2. To'lovni amalga oshiring.\n"
        f"3. Izoh (kommentariy) qismiga quyidagi ID ni kiritishni unutmang:\n\n"
        f"<code>{payment_id}</code>\n\n"
        f"To'lov avtomatik tarzda tasdiqlanadi va obunangiz yoqiladi."
    )
    
    await callback.message.edit_text(
        text, 
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
