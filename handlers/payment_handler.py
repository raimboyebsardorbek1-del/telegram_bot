"""
To'lov tasdiqlash handleri.
Faqat ADMIN_ID ga to'lov so'rovlarini ko'rsatadi va tasdiqlash/rad etish imkonini beradi.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_order, update_order_status
from keyboards.inline_keyboards import main_menu_kb
from config import ADMIN_ID
from services.generation_service import fulfill_order
import asyncio

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    # Faqat admin tasdiqlashi mumkin
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return

    order_id = callback.data.replace("approve_", "")

    # To'lovni bazadan olish
    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    if order['status'] == 'paid':
        await callback.message.edit_text(
            f"ℹ️ Bu to'lov allaqachon tasdiqlangan.\n"
            f"Buyurtma ID: <code>{order_id}</code>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    user_id = order['user_id']

    # To'lovni "paid" holatiga o'tkazish
    await update_order_status(order_id, "paid")

    # Generate and send the document asynchronously
    asyncio.create_task(fulfill_order(callback.bot, order))

    # Admin interfeysi yangilanadi
    await callback.message.edit_text(
        f"✅ <b>Tasdiqlandi!</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"💳 Order ID: <code>{order_id}</code>\n"
        f"⏳ Hujjat avtomatik tayyorlanmoqda va foydalanuvchiga yuboriladi.",
        parse_mode="HTML"
    )
    await callback.answer("✅ To'lov tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    # Faqat admin rad etishi mumkin
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return

    order_id = callback.data.replace("reject_", "")

    # To'lovni bazadan olish
    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    user_id = order['user_id']

    # To'lovni "rejected" holatiga o'tkazish
    await update_order_status(order_id, "rejected")

    # Foydalanuvchiga rad xabarini yuborish
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
                f"Buyurtma: {order['service_type']}\n\n"
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
        f"💳 Order ID: <code>{order_id}</code>",
        parse_mode="HTML"
    )
    await callback.answer("❌ To'lov rad etildi.")
