from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import back_to_menu_btn
from database import get_faq, add_faq, is_curator_or_higher
from states import AddFAQForm

router = Router()

@router.callback_query(F.data == "menu_faq")
async def show_faq(callback: types.CallbackQuery):
    faq_list = await get_faq(limit=10)
    if not faq_list:
        text = "📭 Пока нет вопросов и ответов."
    else:
        lines = ["❓ <b>Часто задаваемые вопросы</b>\n"]
        for q in faq_list:
            lines.append(f"<b>Вопрос:</b> {q[1]}\n<b>Ответ:</b> {q[2]}\n➖➖➖➖➖➖➖➖➖➖")
        text = "\n".join(lines)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))
    if await is_curator_or_higher(callback.from_user.id):
        builder.row(InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="admin_add_faq"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_add_faq")
async def start_add_faq(callback: types.CallbackQuery, state: FSMContext):
    if not await is_curator_or_higher(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await state.set_state(AddFAQForm.question)
    await callback.message.edit_text("Введите вопрос:", reply_markup=back_to_menu_btn())
    await callback.answer()

@router.message(AddFAQForm.question)
async def process_faq_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(AddFAQForm.answer)
    await message.reply("Введите ответ на вопрос:", reply_markup=back_to_menu_btn())

@router.message(AddFAQForm.answer)
async def process_faq_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_faq(data["question"], message.text, message.from_user.id)
    await state.clear()
    await message.reply("Вопрос и ответ добавлены в базу знаний.", reply_markup=back_to_menu_btn())