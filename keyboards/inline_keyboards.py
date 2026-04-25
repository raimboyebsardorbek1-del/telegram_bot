from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PRICES

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Maqola yozish", callback_data="menu_article")],
            [InlineKeyboardButton(text="📝 Mustaqil ish", callback_data="menu_assignment")],
            [InlineKeyboardButton(text="📄 Referat", callback_data="menu_report")],
            [InlineKeyboardButton(text="📊 Taqdimot", callback_data="menu_presentation")],
            [InlineKeyboardButton(text="🤖 AI yordamchi", callback_data="menu_ai")],
            [InlineKeyboardButton(text="💰 Balansim", callback_data="menu_balance")],
            [InlineKeyboardButton(text="👥 Do‘stlarni taklif qilish", callback_data="menu_invite")],
            [InlineKeyboardButton(text="📞 Aloqa", callback_data="menu_contact")]
        ]
    )

def price_selection_kb(service_type: str) -> InlineKeyboardMarkup:
    """Generates a keyboard with price tiers for the selected service."""
    keyboard = []
    service_prices = PRICES.get(service_type.lower(), {})
    
    for pages, price in service_prices.items():
        if service_type.lower() == "taqdimot":
            label = f"📊 {pages} slayd ({price} so'm)"
        else:
            label = f"📄 {pages} bet ({price} so'm)"
        keyboard.append([InlineKeyboardButton(text=label, callback_data=f"price_{service_type}_{pages}")])
        
    keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def payment_kb(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 To'lov qilish", url=url)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )

def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]]
    )

def back_kb(back_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Ortga", callback_data=back_data)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")]
        ]
    )
