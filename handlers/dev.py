from aiogram import types, F, Router
from keyboards import back_to_menu_btn

router = Router()

@router.callback_query(F.data == "menu_dev")
async def show_dev(callback: types.CallbackQuery):
    text = "🚧 Раздел находится в разработке.\nСкоро здесь появится новый функционал."
    await callback.message.edit_text(text, reply_markup=back_to_menu_btn())
    await callback.answer()