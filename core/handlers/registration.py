from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import database, api
from core.config import dp
from core.states import RegistrationStates


async def registration(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationStates.name)
    await message.answer('Введите Ваше имя')


@dp.message(F.text[0] != '/', RegistrationStates.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegistrationStates.age)
    await message.answer('Введите Ваш возраст')


@dp.message(F.text[0] != '/', RegistrationStates.age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 < int(message.text) < 100):
        return await message.answer('Введите корректный возраст')
    await state.update_data(age=int(message.text))
    await state.set_state(RegistrationStates.city)
    await message.answer('Введите Ваш город проживания')


# @dp.message(F.text[0] != '/', RegistrationStates.city)
# async def get_city(message: types.Message, state: FSMContext):
#     cities = api.hh_get_city(message.text)
#     if not cities:
#         return await message.answer('Город не найден')
#     await state.update_data(city=cities[0])
#     keyboard = InlineKeyboardBuilder()
#     for tp in ['Школа', 'Бакалавриат', 'Магистратура', 'Аспирантура']:
#         keyboard.add(types.InlineKeyboardButton(text=tp, callback_data='education_' + tp))
#     keyboard.adjust(2)
#     await state.set_state(RegistrationStates.education)
#     await message.answer('Выберите уровень Вашего образования', reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', RegistrationStates.city)
async def get_education(message: types.Message, state: FSMContext):
    cities = api.hh_get_city(message.text)
    if not cities:
        return await message.answer('Город не найден')
    await state.update_data(city=cities[0])
    # await state.update_data(education=call.data.split('_')[1])
    await state.set_state(RegistrationStates.interests)
    await message.answer('Введите Ваши области интересов через пробел\n\n'
                         'Например: <code>Python</code>, <code>ML</code>, <code>дизайн</code>')


@dp.message(F.text[0] != '/', RegistrationStates.interests)
async def get_interests(message: types.Message, state: FSMContext):
    await state.update_data(interests=message.text)
    state_data = await state.get_data()
    state_data['vacancy_filters'] = {'knowledge': state_data['interests'], 'city': state_data['city']}
    state_data['course_filters'] = {'interests': state_data['interests']}
    state_data.pop('interests')
    state_data['city'] = state_data['city']['name']
    if not await database.get_user(message.chat.id):
        await database.add_user(message.chat.id, **state_data)
        text = '✅ Профиль создан'
    else:
        await database.update_user(message.chat.id, {'name': state_data['name'], 'age': state_data['age'],
                                                     'city': state_data['city'], 'vacancy_filters': state_data['vacancy_filters'],
                                                     'course_filters': state_data['course_filters']})
        text = '✅ Профиль изменен'
    await state.clear()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await message.answer(text, reply_markup=keyboard.as_markup())
