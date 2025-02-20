from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import api, database
from core.config import dp, bot
from core.states import FilterStates
from core.variables import courses_filters_names


@dp.callback_query(F.data == 'search_courses')
async def search_courses(data):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data

    keyboard = InlineKeyboardBuilder()
    for key, name in courses_filters_names.items():
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f'filter_{key}'))
    keyboard.adjust(2, 2, 2)
    keyboard.row(types.InlineKeyboardButton(text='Назад', callback_data='start'))

    user = await database.get_user(message.chat.id)
    text = f'Фильтры поиска\n\nОбласти интересов: {user["interests"]}'
    for key, value in user['search_courses'].items():
        text += f'\n{courses_filters_names[key]}: {value["name"]}'
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        await message.answer(text, reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == 'filter_price')
async def filter_salary(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterStates.salary)
    await state.update_data(choice='price')

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='Бесплатный', callback_data='free_course'))
    keyboard.add(types.InlineKeyboardButton(text='Не важно', callback_data='course_no_matter'))
    keyboard.adjust(2)
    keyboard.row(types.InlineKeyboardButton(text='Назад', callback_data='search_courses'))
    await call.message.edit_text('Введите диапазон стоимости курса в рублях\n\n'
                                 'Например: <code>1000-5500</code>', reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.salary)
async def filter_salary_save(message: types.Message, state: FSMContext):
    user = await database.get_user(message.chat.id)
    user['search_courses']['salary'] = {'id': int(message.text), 'name': message.text + '₽'}
    await database.update_user(message.chat.id, {'search_courses': user['search_courses']})
    await state.clear()
    await search_courses(message)


@dp.callback_query(F.data == 'filter_difficulty')
async def filter_city(call: types.CallbackQuery, state: FSMContext):
    user = await database.get_user(call.message.chat.id)
    await state.update_data(choice='difficulty')
    keyboard = InlineKeyboardBuilder()
    for dif, name in [('easy', 'Начальный'), ('normal', 'Средний'), ('hard', 'Продвинутый')]:
        name = '✅ ' + name if user['search_courses'].get('difficulty') == dif else name
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data='difficulty_' + dif))
    keyboard.add(types.InlineKeyboardButton(text='Не важно', callback_data='course_no_matter'))
    keyboard.adjust(2)
    keyboard.row(types.InlineKeyboardButton(text='Назад', callback_data='search_courses'))

    await state.set_state(FilterStates.difficulty)
    await state.update_data(message_id=call.message.message_id, choice='city')
    await call.message.edit_text('Выбери сложность курса', reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('difficulty_'))
async def filter_difficulty_save(call: types.CallbackQuery, state: FSMContext):
    user = await database.get_user(call.message.chat.id)
    user['search_courses']['difficulty'] = call.data.split('_')[1]
    await database.update_user(call.message.chat.id, {'search_courses': user['search_courses']})
    await search_courses(call)


@dp.callback_query(F.data == 'course_no_matter')
async def filter_choice_no_matter_save(call: types.CallbackQuery, state: FSMContext):
    choice = (await state.get_data()).get('choice')
    user = await database.get_user(call.message.chat.id)
    if choice in user['search_courses']:
        user['search_courses'].pop(choice)
    await database.update_user(call.message.chat.id, {'search_courses': user['search_courses']})
    await search_courses(call)
