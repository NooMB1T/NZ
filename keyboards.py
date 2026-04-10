from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Задания", callback_data="menu_tasks"))
    builder.row(InlineKeyboardButton(text="🏆 Лучшие студенты", callback_data="menu_top"))
    builder.row(InlineKeyboardButton(text="❓ Вопросы и ответы", callback_data="menu_faq"))
    builder.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="menu_profile"))
    builder.row(InlineKeyboardButton(text="ℹ️ Информация", callback_data="menu_info"))
    builder.row(InlineKeyboardButton(text="🚧 В разработке", callback_data="menu_dev"))
    return builder.as_markup()

def back_to_menu_btn():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu"))
    return builder.as_markup()

def admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task"))
    builder.row(InlineKeyboardButton(text="📚 Добавить вопрос FAQ", callback_data="admin_add_faq"))
    builder.row(InlineKeyboardButton(text="👥 Управление ролями", callback_data="admin_roles"))
    builder.row(InlineKeyboardButton(text="⚠️ Выдать предупреждение", callback_data="admin_warn"))
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))
    return builder.as_markup()

def tasks_menu_kb(is_curator: bool = False):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Я выполнил задание", callback_data="solve_task"))
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))
    if is_curator:
        builder.row(InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task"))
    return builder.as_markup()