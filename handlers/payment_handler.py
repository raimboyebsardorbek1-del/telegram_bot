"""
To'lov tasdiqlash handleri.
Faqat ADMIN_ID ga to'lov so'rovlarini ko'rsatadi va tasdiqlash/rad etish imkonini beradi.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import (
    get_payment, update_payment_status,
    add_user_subscription, check_subscription
)
from keyboards.inline_keyboards import main_menu_kb
from config import ADMIN_ID, SUBSCRIPTION_DAYS

router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    # Faqat admin tasdiqlashi mumkin
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return

    payment_id = callback.data.replace("approve_", "")

    # To'lovni bazadan olish
    payment = await get_payment(payment_id)
    if not payment:
        await callback.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    if payment['status'] == 'paid':
        await callback.message.edit_text(
            f"ℹ️ Bu to'lov allaqachon tasdiqlangan.\n"
            f"To'lov ID: <code>{payment_id}</code>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    user_id = payment['user_id']

    # To'lovni "paid" holatiga o'tkazish
    await update_payment_status(payment_id, "paid")

    # Foydalanuvchiga 30 kunlik obuna berish
    await add_user_subscription(user_id, SUBSCRIPTION_DAYS)

    # Foydalanuvchiga xabar yuborish
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>Tabriklaymiz!</b>\n\n"
                f"To'lovingiz tasdiqlandi va <b>{SUBSCRIPTION_DAYS} kunlik</b> obunangiz faollashtirildi! 🎉\n\n"
                f"Endi barcha funksiyalardan foydalanishingiz mumkin."
            ),
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception:
        pass  # Foydalanuvchi botni bloklagan bo'lishi mumkin

    # Admin interfeysi yangilanadi
    await callback.message.edit_text(
        f"✅ <b>Tasdiqlandi!</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"💳 To'lov ID: <code>{payment_id}</code>\n"
        f"📅 {SUBSCRIPTION_DAYS} kunlik obuna berildi.",
        parse_mode="HTML"
    )
    await callback.answer("✅ Obuna faollashtirildi!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    # Faqat admin rad etishi mumkin
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return

    payment_id = callback.data.replace("reject_", "")

    # To'lovni bazadan olish
    payment = await get_payment(payment_id)
    if not payment:
        await callback.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    user_id = payment['user_id']

    # To'lovni "rejected" holatiga o'tkazish
    await update_payment_status(payment_id, "rejected")

    # Foydalanuvchiga rad xabarini yuborish
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
                "Sabab: To'lov aniqlanmadi yoki noto'g'ri miqdorda yuborilgan.\n\n"
                "Qayta urinib ko'ring yoki admin bilan bog'laning."
            ),
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception:
        pass

    # Admin interfeysi yangilanadi
    await callback.message.edit_text(
        f"❌ <b>Rad etildi.</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"💳 To'lov ID: <code>{payment_id}</code>",
        parse_mode="HTML"
    )
    await callback.answer("❌ To'lov rad etildi.")
