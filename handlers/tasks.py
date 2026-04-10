from aiogram import types, F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import back_to_menu_btn
from database import (
    get_tasks, get_task_by_id, add_solution, is_curator_or_higher,
    get_solution_by_id, evaluate_solution
)
from states import SolveTaskForm, EvaluationCommentForm
from datetime import datetime
from config import TASKS_PER_PAGE

router = Router()

@router.callback_query(F.data == "menu_tasks")
async def show_tasks(callback: types.CallbackQuery):
    tasks = await get_tasks(limit=TASKS_PER_PAGE)
    if not tasks:
        text = "📭 Пока нет активных заданий."
    else:
        lines = ["📋 <b>Последние задания:</b>\n"]
        for t in tasks:
            lines.append(
                f"🆔 <b>#{t[0]}</b>\n"
                f"📌 Задание: {t[1]}\n"
                f"⏳ Время на выполнение: {t[2]}\n"
                f"👤 Имя клиента: {t[3]}\n"
                f"📅 Время отправки: {t[4]}\n"
                f"🔥 Срочность: {t[5]}\n"
                f"🕒 Создано: {t[6]}\n"
                "➖➖➖➖➖➖➖➖➖➖"
            )
        text = "\n".join(lines)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Я выполнил задание", callback_data="solve_task"))
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))
    if await is_curator_or_higher(callback.from_user.id):
        builder.row(InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_add_task"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "solve_task")
async def start_solve_task(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SolveTaskForm.waiting_for_task_id)
    await callback.message.edit_text(
        "🆔 Введите номер задания (ID), которое вы выполнили.\n"
        "Номер указан в списке заданий (например, 42)",
        reply_markup=back_to_menu_btn()
    )
    await callback.answer()

@router.message(SolveTaskForm.waiting_for_task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text.strip())
    except ValueError:
        await message.reply("❌ Пожалуйста, введите число — ID задания.", reply_markup=back_to_menu_btn())
        return
    task = await get_task_by_id(task_id)
    if not task:
        await message.reply("❌ Задание с таким ID не найдено.", reply_markup=back_to_menu_btn())
        return
    await state.update_data(task_id=task_id)
    await state.set_state(SolveTaskForm.waiting_for_answer)
    await message.reply(
        "📎 Отправьте ваш ответ.\n"
        "Вы можете написать текст, прикрепить фото или файл.\n"
        "Отправьте одним сообщением.",
        reply_markup=back_to_menu_btn()
    )

@router.message(SolveTaskForm.waiting_for_answer, F.content_type.in_({'text', 'photo', 'document'}))
async def process_solution(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    task_id = data["task_id"]
    user_id = message.from_user.id

    answer_text = None
    file_id = None
    if message.text:
        answer_text = message.text
    elif message.photo:
        file_id = message.photo[-1].file_id
        answer_text = message.caption or ""
    elif message.document:
        file_id = message.document.file_id
        answer_text = message.caption or ""

    curator_id = await add_solution(task_id, user_id, answer_text, file_id)
    await state.clear()

    if curator_id:
        try:
            curator_msg = (
                f"📬 Новое решение задания #{task_id}\n"
                f"👤 Ученик ID: {user_id}\n"
                f"📝 Ответ: {answer_text if answer_text else 'Без текста'}\n"
                f"🕒 Время: {datetime.now().strftime('%H:%M')}"
            )
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="⭐ Оценить", callback_data=f"evaluate_{task_id}_{user_id}"))
            await bot.send_message(curator_id, curator_msg, reply_markup=builder.as_markup())
            if file_id:
                if message.photo:
                    await bot.send_photo(curator_id, file_id, caption="📎 Прикреплённое фото")
                elif message.document:
                    await bot.send_document(curator_id, file_id, caption="📎 Прикреплённый файл")
        except Exception as e:
            print(f"Ошибка уведомления куратора: {e}")

    await message.reply(
        "✅ Ваше решение отправлено куратору на проверку!",
        reply_markup=back_to_menu_btn()
    )

@router.callback_query(F.data.startswith("evaluate_"))
async def start_evaluation(callback: types.CallbackQuery):
    if not await is_curator_or_higher(callback.from_user.id):
        await callback.answer("Только куратор может оценивать", show_alert=True)
        return
    parts = callback.data.split("_")
    task_id = int(parts[1])
    user_id = int(parts[2])
    import aiosqlite
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id FROM task_solutions WHERE task_id = ? AND user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
            (task_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                await callback.answer("Решение уже оценено или не найдено", show_alert=True)
                return
            solution_id = row[0]

    builder = InlineKeyboardBuilder()
    for i in range(11):
        builder.button(text=str(i), callback_data=f"score_{solution_id}_{i}")
    builder.adjust(5, 5, 1)
    builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu"))
    await callback.message.edit_text(
        f"⭐ Оценка решения задания #{task_id}\n"
        f"👤 Ученик ID: {user_id}\n\n"
        "Выберите оценку от 0 до 10:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("score_"))
async def process_score(callback: types.CallbackQuery, state: FSMContext):
    if not await is_curator_or_higher(callback.from_user.id):
        await callback.answer("Только куратор может оценивать", show_alert=True)
        return
    parts = callback.data.split("_")
    solution_id = int(parts[1])
    score = int(parts[2])
    await state.update_data(eval_solution_id=solution_id, eval_score=score)
    await state.set_state(EvaluationCommentForm.waiting_for_comment)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_comment"))
    builder.row(InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu"))
    await callback.message.edit_text(
        f"📝 Оценка: {score}/10\n\n"
        "💬 Добавьте комментарий (необязательно).\n"
        "Напишите, что сделано хорошо, а что можно улучшить.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "skip_comment")
async def skip_comment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    solution_id = data.get("eval_solution_id")
    score = data.get("eval_score")
    await evaluate_solution(solution_id, callback.from_user.id, score)
    await state.clear()
    await callback.message.edit_text("✅ Оценка сохранена без комментария.", reply_markup=back_to_menu_btn())
    await callback.answer()

@router.message(EvaluationCommentForm.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    solution_id = data.get("eval_solution_id")
    score = data.get("eval_score")
    comment = message.text
    await evaluate_solution(solution_id, message.from_user.id, score, comment)
    await state.clear()
    await message.reply("✅ Оценка с комментарием сохранена.", reply_markup=back_to_menu_btn())