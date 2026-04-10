from aiogram.fsm.state import State, StatesGroup

class AddTaskForm(StatesGroup):
    description = State()
    time_limit = State()
    client_name = State()
    sent_time = State()
    urgency = State()

class SolveTaskForm(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_answer = State()

class AddFAQForm(StatesGroup):
    question = State()
    answer = State()

class EditProfileForm(StatesGroup):
    code_name = State()
    age = State()