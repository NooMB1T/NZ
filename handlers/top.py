from aiogram import types, F, Router
from keyboards import back_to_menu_btn
from database import get_top_students
from utils import get_medal, mask_username

router = Router()

@router.callback_query(F.data == "menu_top")
async def show_top_students(callback: types.CallbackQuery):
    top = await get_top_students(limit=5)
    if not top:
        text = "🏆 Рейтинг пока пуст. Как только появятся первые оценки, здесь будут лучшие студенты."
    else:
        lines = ["🏆 <b>ТОП-5 ЛУЧШИХ СТУДЕНТОВ</b>\n"]
        for i, (uid, username, code_name, avg_score, count) in enumerate(top):
            medal = get_medal(i)
            display = mask_username(username, code_name)
            lines.append(
                f"{medal} {display}\n"
                f"   ⭐ Средний балл: <b>{avg_score:.2f}</b> (из {count} оценок)\n"
            )
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_to_menu_btn(), parse_mode="HTML")
    await callback.answer()