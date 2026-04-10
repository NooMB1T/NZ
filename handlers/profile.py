from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import back_to_menu_btn
from database import get_user, update_user_profile
from states import EditProfileForm
from config import MAX_WARNINGS

router = Router()

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Профиль не найден.", reply_markup=back_to_menu_btn())
        await callback.answer()
        return

    user_id, username, role, code_name, age, joined_at, warnings = user

    display_name = code_name if code_name else f"@{username}" if username else "Не указан"
    age_str = str(age) if age else "Не указан"
    joined_str = joined_at[:10] if joined_at else "Неизвестно"
    warnings_str = f"{warnings}/{MAX_WARNINGS}"

    text = (
        f"📊 <b>Моя статистика</b>\n\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"👤 Имя в академии: {display_name}\n"
        f"🔞 Возраст: {age_str}\n"
        f"📅 В академии с: {joined_str}\n"
        f"⚠️ Предупреждения: {warnings_str}\n"
        f"📌 Роль: {role}\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile"))
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(EditProfileForm.code_name)
    await callback.message.edit_text(
        "Введите ваш кодовый никнейм (как вас будут видеть другие саппорты):",
        reply_markup=back_to_menu_btn()
    )
    await callback.answer()

@router.message(EditProfileForm.code_name)
async def process_code_name(message: types.Message, state: FSMContext):
    await state.update_data(code_name=message.text)
    await state.set_state(EditProfileForm.age)
    await message.reply("Введите ваш возраст (число):", reply_markup=back_to_menu_btn())

@router.message(EditProfileForm.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.reply("Возраст должен быть числом. Попробуйте снова:")
        return

    data = await state.get_data()
    await update_user_profile(message.from_user.id, code_name=data["code_name"], age=age)
    await state.clear()
    await message.reply("Профиль обновлён!", reply_markup=back_to_menu_btn())