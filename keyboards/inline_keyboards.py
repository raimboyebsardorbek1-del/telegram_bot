from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Maqola yozish", callback_data="menu_article")],
            [InlineKeyboardButton(text="📝 Mustaqil ish", callback_data="menu_assignment")],
            [InlineKeyboardButton(text="📄 Referat", callback_data="menu_report")],
            [InlineKeyboardButton(text="📊 Taqdimot", callback_data="menu_presentation")],
            [InlineKeyboardButton(text="🤖 Ai yordamchi", callback_data="menu_ai")],
            [InlineKeyboardButton(text="💳 Obuna sotib olish", callback_data="menu_subscribe")],
            [InlineKeyboardButton(text="👥 Dostlarni taklif qilish", callback_data="menu_invite")],
            [InlineKeyboardButton(text="📞 Aloqa", callback_data="menu_contact")]
        ]
    )

def article_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="O'zbek", callback_data="lang_uz")],
            [InlineKeyboardButton(text="Rus", callback_data="lang_ru")],
            [InlineKeyboardButton(text="Ingliz", callback_data="lang_en")]
        ]
    )

def assignment_difficulty_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Oson", callback_data="diff_easy")],
            [InlineKeyboardButton(text="O'rta", callback_data="diff_medium")],
            [InlineKeyboardButton(text="Qiyin", callback_data="diff_hard")]
        ]
    )

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="💳 To'lovlarni ko'rish", callback_data="admin_payments")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="👥 Foydalanuvchilar ro'yxati", callback_data="admin_users_list")],
            [InlineKeyboardButton(text="🚫 Ban user", callback_data="admin_ban")],
            [InlineKeyboardButton(text="✅ Unban user", callback_data="admin_unban")]
        ]
    )

def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )

def payment_confirm_kb(payment_id: str) -> InlineKeyboardMarkup:
    """Foydalanuvchiga 'To'ladim' tugmasini ko'rsatish."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ To'ladim", callback_data=f"paid_{payment_id}")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="cancel")]
        ]
    )

def admin_payment_approval_kb(payment_id: str) -> InlineKeyboardMarkup:
    """Admin uchun to'lovni tasdiqlash yoki rad etish tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{payment_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{payment_id}")
            ]
        ]
    )
