
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import database, api
from core.config import dp
from core.states import FilterStates
from core.variables import course_filters_names, course_difficulty_names


@dp.callback_query(F.data == 'search_course')
async def search_course(call: types.CallbackQuery, state: FSMContext):
    user = await database.get_user(call.message.chat.id)
    state_data = await state.get_data()

    index, courses, page = state_data.get('index', 0), state_data.get('courses', []), state_data.get('page', 0)
    if index >= len(courses):
        page += 1
        courses += api.stepik_get_courses(user['course_filters'], page)

    if index >= len(courses):
        return await call.answer('Больше курсов по заданным фильтрам нет')
    await state.update_data(page=page, courses=courses, index=index+1)
    course = courses[index]

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='ℹ️ Подробнее', url=course['canonical_url']))
    keyboard.row(types.InlineKeyboardButton(text=f'☑️ Пройдено', callback_data=f'completed_{course["id"]}'),
                 types.InlineKeyboardButton(text=f'➡️ Далее', callback_data='search_course'))
    keyboard.row(types.InlineKeyboardButton(text='🏚 Назад', callback_data='start'))

    text = (f'<b>{course["title"]}</b>\n\n'
            f'<b>Цена:</b> {course.get("price", "") + " ₽" if course["is_paid"] else "Бесплатный"}\n'
            f'<b>Сложность:</b> {course_difficulty_names[course["difficulty"]]}\n'
            f'<b>Язык:</b> {"🇷🇺 Русский" if course["language"] == "ru" else "🇬🇧 Английский"}\n'
            f'<b>Учащихся:</b> {course["learners_count"]} человек\n'
            f'{"<b>Сертификат:</b> ✅ Есть" if course.get("certificate") else ""}\n')

    await call.answer()
    if course['cover']:
        await call.message.answer_photo(course['cover'], caption=text, reply_markup=keyboard.as_markup())
    else:
        await call.message.answer(text, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)


@dp.callback_query(F.data.startswith('completed_'))
async def filter_salary(call: types.CallbackQuery):
    course_id = int(call.data.split('_')[-1])
    course = api.stepik_get_course(course_id)

    await database.add_message(call.message.chat.id, 'system',
                               f'Пользователь прошел курс "{course["title"]}", сложность курса: {course["difficulty"]}. '
                               f'Учитывай это при дальнейшем составлении траектории развития.')

    await call.answer('☑️ Сохранено')


@dp.callback_query(F.data == 'course_filters')
async def courses_filter(data):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    user = await database.get_user(message.chat.id)

    keyboard = InlineKeyboardBuilder()
    for key, name in course_filters_names.items():
        if key in ['price__gte', 'price__lte']:
            continue
        key, name = ('price', 'Цена') if key == 'is_paid' else (key, name)
        if key == 'with_certificate':
            name = '🔳 ' + name if user['course_filters'].get(key, False) else '⬜️ ' + name
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f'course_filter_{key}'))
    keyboard.adjust(2, 2, 2)
    keyboard.row(types.InlineKeyboardButton(text='🔄 Сбросить все', callback_data='reset_course_filters'),
                 types.InlineKeyboardButton(text='⬅️ Назад', callback_data='start'))

    text = f'🔎 <b>Фильтры поиска курсов</b>\n'
    for key, value in user['course_filters'].items():
        if key == 'difficulty':
            value = course_difficulty_names[value]
        if key == 'is_paid' and not value:
            text += '\nБесплатный курс'
            continue
        if key == 'with_certificate':
            continue
        text += f'\n<b>{course_filters_names[key]}:</b> {value}'
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        await message.answer(text, reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == 'course_filter_interests')
async def filter_interests(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(education=call.data.split('_')[1])
    await state.set_state(FilterStates.interests)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='course_filters'))
    await call.message.edit_text('Введите Ваши области знаний через пробел\n\n'
                                 'Например: <code>Python</code>, <code>ML</code>, <code>дизайн</code>',
                                 reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.interests)
async def filter_interests_save(message: types.Message, state: FSMContext):
    user = await database.get_user(message.chat.id)
    user['course_filters']['interests'] = message.text
    await database.update_user(message.chat.id, {'course_filters': user['course_filters']})
    await state.clear()
    await courses_filter(message)


@dp.callback_query(F.data == 'course_filter_price')
async def filter_salary(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterStates.price)
    await state.update_data(choice='is_paid')

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='Бесплатный', callback_data='free_course'))
    keyboard.add(types.InlineKeyboardButton(text='Не важно', callback_data='course_no_matter'))
    keyboard.adjust(2)
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='course_filters'))
    await call.message.edit_text('Введите диапазон стоимости курса в рублях\n\n'
                                 'Например: <code>1000-5500</code>', reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', FilterStates.price)
async def filter_salary_save(message: types.Message, state: FSMContext):
    user = await database.get_user(message.chat.id)
    user['course_filters']['price__gte'], user['course_filters']['price__lte'] = message.text.split('-')
    if 'is_paid' in user['course_filters']:
        user['course_filters'].pop('is_paid')
    await database.update_user(message.chat.id, {'course_filters': user['course_filters']})
    await state.clear()
    await courses_filter(message)


@dp.callback_query(F.data == 'free_course', FilterStates.price)
async def free_course_save(call: types.CallbackQuery, state: FSMContext):
    user = await database.get_user(call.message.chat.id)
    user['course_filters']['is_paid'] = False
    if 'price__gte' in user['course_filters'] and 'price__lte' in user['course_filters']:
        user['course_filters'].pop('price__gte')
        user['course_filters'].pop('price__lte')
    await database.update_user(call.message.chat.id, {'course_filters': user['course_filters']})
    await state.clear()
    await courses_filter(call)


@dp.callback_query(F.data == 'course_filter_difficulty')
async def filter_difficulty(call: types.CallbackQuery, state: FSMContext):
    user = await database.get_user(call.message.chat.id)

    keyboard = InlineKeyboardBuilder()
    for dif, name in course_difficulty_names.items():
        name = '✅ ' + name if user['course_filters'].get('difficulty') == dif else name
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data='difficulty_' + dif))
    keyboard.add(types.InlineKeyboardButton(text='Не важно', callback_data='course_no_matter'))
    keyboard.adjust(2)
    keyboard.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='course_filters'))

    await state.set_state(FilterStates.difficulty)
    await state.update_data(message_id=call.message.message_id, choice='difficulty')
    await call.message.edit_text('Выберите сложность курса', reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('difficulty_'))
async def filter_difficulty_save(call: types.CallbackQuery):
    user = await database.get_user(call.message.chat.id)
    user['course_filters']['difficulty'] = call.data.split('_')[1]
    await database.update_user(call.message.chat.id, {'course_filters': user['course_filters']})
    await courses_filter(call)


@dp.callback_query(F.data == 'course_no_matter')
async def filter_choice_no_matter_save(call: types.CallbackQuery, state: FSMContext):
    choice = (await state.get_data()).get('choice')
    user = await database.get_user(call.message.chat.id)

    if choice == 'is_paid' and 'price__gte' in user['course_filters'] and 'price__lte' in user['course_filters']:
        user['course_filters'].pop('price__gte')
        user['course_filters'].pop('price__lte')

    if choice in user['course_filters']:
        user['course_filters'].pop(choice)
    await database.update_user(call.message.chat.id, {'course_filters': user['course_filters']})
    await courses_filter(call)


@dp.callback_query(F.data == 'course_filter_with_certificate')
async def filter_change_with_certificate(call: types.CallbackQuery):
    user = await database.get_user(call.message.chat.id)
    user['course_filters']['with_certificate'] = not user['course_filters'].get('with_certificate', False)

    await database.update_user(call.message.chat.id, {'course_filters': user['course_filters']})
    await courses_filter(call)


@dp.callback_query(F.data == 'course_filter_lang')
async def filter_change_language(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(choice='lang')

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='🇷🇺 Русский', callback_data='ru_language'))
    keyboard.add(types.InlineKeyboardButton(text='🇬🇧 Английский', callback_data='en_language'))
    keyboard.add(types.InlineKeyboardButton(text='Не важно', callback_data='course_no_matter'))
    keyboard.add(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='course_filters'))
    keyboard.adjust(2, 2)

    await call.message.edit_text('Выберите язык курса', reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.in_(['ru_language', 'en_language']))
async def filter_change_language_save(call: types.CallbackQuery):
    user = await database.get_user(call.message.chat.id)
    user['course_filters']['lang'] = call.data.split('_')[0]

    await database.update_user(call.message.chat.id, {'course_filters': user['course_filters']})
    await courses_filter(call)


@dp.callback_query(F.data == 'reset_course_filters')
async def reset_course_filters(call: types.CallbackQuery):
    await database.update_user(call.message.chat.id, {'course_filters': {}})
    await courses_filter(call)
