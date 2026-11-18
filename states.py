from aiogram.fsm.state import State, StatesGroup


class Offer(StatesGroup):
    waiting_content = State()


class AdminEditStates(StatesGroup):
    waiting_for_new_content = State()
