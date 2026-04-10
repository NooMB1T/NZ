from aiogram import types, F, Router
from keyboards import back_to_menu_btn

router = Router()

@router.callback_query(F.data == "menu_info")
async def show_info(callback: types.CallbackQuery):
    text = (
        "ℹ️ <b>Академия поддержки</b>\n\n"
        "Бот предназначен для обучения и аттестации сотрудников службы поддержки.\n"
        "Версия: 1.0.0\n"
        "Разработчик: команда академии\n\n"
        "По всем вопросам обращайтесь к куратору."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_btn(), parse_mode="HTML")
    await callback.answer()