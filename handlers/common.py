from aiogram import types, F, Router
from aiogram.filters import Command
from keyboards import main_menu_kb
from database import add_user

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        "Добро пожаловать в Академию поддержки.\n"
        "Выберите нужный раздел в меню.",
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Главное меню",
        reply_markup=main_menu_kb()
    )
    await callback.answer()