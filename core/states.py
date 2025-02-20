from aiogram.fsm.state import StatesGroup, State


class BasicStates(StatesGroup):
    assistantChat = State()


class RegistrationStates(StatesGroup):
    name = State()
    age = State()
    city = State()
    education = State()
    interests = State()


class FilterStates(StatesGroup):
    city = State()
    knowledge = State()
    interests = State()
    salary = State()
    choice = State()
    difficulty = State()
    price = State()

