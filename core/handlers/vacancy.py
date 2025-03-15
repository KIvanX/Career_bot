from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import api, database
from core.config import dp, bot
from core.states import FilterStates
from core.utils import get_salary
from core.variables import choose_vacancy_filters, vacancy_filters_names


@dp.callback_query(F.data == 'search_vacancy')
async def search_vacancy(call: types.CallbackQuery, state: FSMContext):
    page = (await state.get_data()).get('page', -1) + 1
    user = await database.get_user(call.message.chat.id)
    vacancies = api.hh_get_vacancies(user['vacancy_filters'], page)

    if not vacancies:
        return await call.answer('Больше вакансий по заданным фильтрам нет')
    vacancy = vacancies[0]

    await state.update_data(page=page)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='ℹ️ Подробнее', url=vacancy['alternate_url']))
    keyboard.row(types.InlineKeyboardButton(text=f'➡️ Далее', callback_data='search_vacancy'))
    keyboard.row(types.InlineKeyboardButton(text='🏚 Назад', callback_data='start'))

    text = (f'<b>{vacancy["name"]}</b>\n\n'
            f'Компания: <a href="{vacancy["employer"]["alternate_url"]}">{vacancy["employer"]["name"]}</a>\n'
            f'Город: {vacancy["area"]["name"]}\n'
            f'Зарплата: {get_salary(vacancy["salary"])}\n'
            f'Опыт работы: {vacancy["experience"]["name"]}\n'
            f'График работы: {vacancy["schedule"]["name"]}\n'
            f'Занятость: {vacancy["employment"]["name"]}\n')

    await call.answer()
    if vacancy['employer']['logo_urls']:
        await call.message.answer_photo(vacancy['employer']['logo_urls']['240'],
                                        caption=text, reply_markup=keyboard.as_markup())
    else:
        await call.message.answer(text, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)


@dp.callback_query(F.data == 'vacancy_filters')
async def vacancy_filters(data):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data

    keyboard = InlineKeyboardBuilder()
    for key, name in vacancy_filters_names.items():
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f'filter_{key}'))
    keyboard.adjust(2, 2, 2)
    keyboard.row(types.InlineKeyboardButton(text='🔄 Сбросить все', callback_data='reset_vacancy_filters'),
                 types.InlineKeyboardButton(text='⬅️ Назад', callback_data='start'))

    user = await database.get_user(message.chat.id)
    text = f'🔎 <b>Фильтры поиска вакансий</b>\n'
    for key, value in user['vacancy_filters'].items():
        if key == 'city':
            value = value['name']
        elif key in choose_vacancy_filters:
            value = next((e for e in choose_vacancy_filters[key] if e['id'] == value))['name']
        text += f'\n{vacancy_filters_names[key]}: {value}'
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        await message.answer(text, reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == 'filter_knowledge')
async def filter_interests(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(education=call.data.split('_')[1])
    await state.set_state(FilterStates.knowledge)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='vacancy_filters'))
    await call.message.edit_text('Введите ваши области знаний пробел запятую\n\n'
                                 'Например: <code>Python</code>, <code>ML</code>, <code>дизайн</code>',
                                 reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.knowledge)
async def filter_knowledge_save(message: types.Message, state: FSMContext):
    user = await database.get_user(message.chat.id)
    user['vacancy_filters']['knowledge'] = message.text
    await database.update_user(message.chat.id, {'vacancy_filters': user['vacancy_filters']})
    await state.clear()
    await vacancy_filters(message)


@dp.callback_query(F.data == 'filter_salary')
async def filter_salary(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterStates.salary)
    await state.update_data(choice='salary')

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Не важно', callback_data='vacancy_no_matter'))
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='vacancy_filters'))
    await call.message.edit_text('Введите интересующую вас зарплату в рублях\n\n'
                                 'Например: <code>110000</code>', reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.salary)
async def filter_salary_save(message: types.Message, state: FSMContext):
    user = await database.get_user(message.chat.id)
    user['vacancy_filters']['salary'] = int(message.text)
    await database.update_user(message.chat.id, {'vacancy_filters': user['vacancy_filters']})
    await state.clear()
    await vacancy_filters(message)


@dp.callback_query(F.data == 'filter_city')
async def filter_city(call: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Не важно', callback_data='vacancy_no_matter'))
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='vacancy_filters'))

    await state.set_state(FilterStates.city)
    await state.update_data(message_id=call.message.message_id, choice='city')
    await call.message.edit_text('Введи свой город', reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.city)
async def filter_city_choose(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    await message.delete()
    await state.clear()
    cities = api.hh_get_city(message.text)[:10]
    await state.update_data(cities={str(city['id']): city['name'] for city in cities})
    keyboard = InlineKeyboardBuilder()
    for city in cities:
        keyboard.add(types.InlineKeyboardButton(text=city['name'], callback_data='city_' + city['id']))
    keyboard.adjust(2)
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='filter_city'))

    await bot.edit_message_text('Выбери свой город из списка', chat_id=message.chat.id,
                                message_id=state_data.get('message_id'), reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('city_'))
async def filter_city_save(call: types.CallbackQuery, state: FSMContext):
    city = {'id': call.data.split('_')[1], 'name': (await state.get_data()).get('cities')[call.data.split('_')[1]]}
    user = await database.get_user(call.message.chat.id)
    user['vacancy_filters']['city'] = city
    await database.update_user(call.message.chat.id, {'vacancy_filters': user['vacancy_filters']})
    await vacancy_filters(call)


@dp.callback_query(F.data.in_(['filter_experience', 'filter_schedule', 'filter_employment']))
async def filter_choice(call: types.CallbackQuery, state: FSMContext):
    choice = call.data.split('_')[1]
    await state.update_data(choice=choice)
    name = {'experience': 'свой опыт', 'schedule': 'удобный график', 'employment': 'занятость'}[choice]
    keyboard = InlineKeyboardBuilder()
    for var in choose_vacancy_filters[choice]:
        keyboard.add(types.InlineKeyboardButton(text=var['name'], callback_data='choice_' + var['id']))
    keyboard.adjust(3)
    keyboard.row(types.InlineKeyboardButton(text='Не важно', callback_data='vacancy_no_matter'),
                 types.InlineKeyboardButton(text='⬅️ Назад', callback_data='vacancy_filters'))
    await call.message.edit_text(f'Выберите {name}', reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('choice_'))
async def filter_choice_save(call: types.CallbackQuery, state: FSMContext):
    choice = (await state.get_data()).get('choice')
    user = await database.get_user(call.message.chat.id)
    user['vacancy_filters'][choice] = call.data.split('_')[1]

    await database.update_user(call.message.chat.id, {'vacancy_filters': user['vacancy_filters']})
    await vacancy_filters(call)


@dp.callback_query(F.data == 'vacancy_no_matter')
async def filter_choice_no_matter_save(call: types.CallbackQuery, state: FSMContext):
    choice = (await state.get_data()).get('choice')
    user = await database.get_user(call.message.chat.id)
    if choice in user['vacancy_filters']:
        user['vacancy_filters'].pop(choice)
    await database.update_user(call.message.chat.id, {'vacancy_filters': user['vacancy_filters']})
    await vacancy_filters(call)


@dp.callback_query(F.data == 'reset_vacancy_filters')
async def reset_vacancy_filters(call: types.CallbackQuery):
    await database.update_user(call.message.chat.id, {'vacancy_filters': {}})
    await vacancy_filters(call)
