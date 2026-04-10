from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import back_to_menu_btn, admin_panel_kb
from database import (
    is_admin, is_curator_or_higher, add_task, set_user_role,
    add_warning, reset_warnings, get_user
)
from states import AddTaskForm
from config import ROLES, MAX_WARNINGS

router = Router()

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "🛠 Административная панель",
        reply_markup=admin_panel_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_task")
async def start_add_task(callback: types.CallbackQuery, state: FSMContext):
    if not await is_curator_or_higher(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await state.set_state(AddTaskForm.description)
    await callback.message.edit_text(
        "📝 Введите описание задания:",
        reply_markup=back_to_menu_btn()
    )
    await callback.answer()

@router.message(AddTaskForm.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddTaskForm.time_limit)
    await message.reply("⏳ Введите время на выполнение (например, 15 минут):", reply_markup=back_to_menu_btn())

@router.message(AddTaskForm.time_limit)
async def process_time_limit(message: types.Message, state: FSMContext):
    await state.update_data(time_limit=message.text)
    await state.set_state(AddTaskForm.client_name)
    await message.reply("👤 Введите имя клиента:", reply_markup=back_to_menu_btn())

@router.message(AddTaskForm.client_name)
async def process_client_name(message: types.Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    await state.set_state(AddTaskForm.sent_time)
    await message.reply("📅 Введите время отправки (когда клиент обратился):", reply_markup=back_to_menu_btn())

@router.message(AddTaskForm.sent_time)
async def process_sent_time(message: types.Message, state: FSMContext):
    await state.update_data(sent_time=message.text)
    await state.set_state(AddTaskForm.urgency)
    builder = InlineKeyboardBuilder()
    for level in ["🔥 Высокая", "⚠️ Средняя", "🟢 Низкая"]:
        builder.row(InlineKeyboardButton(text=level, callback_data=f"urgency_{level.split()[1]}"))
    builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu"))
    await message.reply("🔥 Выберите срочность:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("urgency_"))
async def process_urgency(callback: types.CallbackQuery, state: FSMContext):
    urgency = callback.data.split("_")[1]
    data = await state.get_data()
    await add_task(
        description=data["description"],
        time_limit=data["time_limit"],
        client_name=data["client_name"],
        sent_time=data["sent_time"],
        urgency=urgency,
        created_by=callback.from_user.id
    )
    await state.clear()
    await callback.message.edit_text("✅ Задание успешно добавлено!", reply_markup=back_to_menu_btn())
    await callback.answer()

@router.callback_query(F.data == "admin_roles")
async def admin_roles(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "👥 Для изменения роли пользователя отправьте команду:\n"
        "<code>/setrole USER_ID ROLE</code>\n\n"
        f"Доступные роли: {', '.join(ROLES.keys())}",
        reply_markup=back_to_menu_btn(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("setrole"))
async def cmd_setrole(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.reply("⛔ Недостаточно прав")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("❌ Формат: /setrole USER_ID ROLE")
        return
    try:
        target_id = int(parts[1])
        role = parts[2].lower()
        if role not in ROLES:
            await message.reply(f"❌ Недопустимая роль. Доступны: {', '.join(ROLES.keys())}")
            return
        await set_user_role(target_id, role)
        await message.reply(f"✅ Роль пользователя {target_id} изменена на <b>{role}</b>", parse_mode="HTML")
    except ValueError:
        await message.reply("❌ USER_ID должен быть числом")

@router.callback_query(F.data == "admin_warn")
async def admin_warn_prompt(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "⚠️ Для выдачи предупреждения отправьте команду:\n"
        "<code>/warn USER_ID</code>\n\n"
        "Для сброса предупреждений:\n"
        "<code>/resetwarn USER_ID</code>",
        reply_markup=back_to_menu_btn(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("warn"))
async def cmd_warn(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.reply("Недостаточно прав")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Формат: /warn USER_ID")
        return
    try:
        target_id = int(parts[1])
        await add_warning(target_id)
        user = await get_user(target_id)
        if user:
            await message.reply(f"⚠️ Пользователю {target_id} выдано предупреждение. Всего: {user[6]+1}/{MAX_WARNINGS}")
        else:
            await message.reply("Пользователь не найден")
    except ValueError:
        await message.reply("USER_ID должен быть числом")

@router.message(Command("resetwarn"))
async def cmd_reset_warn(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.reply("Недостаточно прав")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Формат: /resetwarn USER_ID")
        return
    try:
        target_id = int(parts[1])
        await reset_warnings(target_id)
        await message.reply(f"Предупреждения пользователя {target_id} сброшены.")
    except ValueError:
        await message.reply("USER_ID должен быть числом")