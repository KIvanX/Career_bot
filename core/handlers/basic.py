import json
import logging

from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import database, api
from core.config import dp, groq_client
from core.handlers.registration import registration
from core.states import BasicStates
from core.variables import get_order_prompt, choose_vacancy_filters, vacancy_filters_names, course_filters_names, \
    course_difficulty_names


@dp.callback_query(F.data == 'start')
async def start(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    await state.clear()

    user = await database.get_user(message.chat.id)
    if not user:
        return await registration(message, state)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='🔮 Я хочу...', callback_data='get_order'))
    keyboard.add(types.InlineKeyboardButton(text='💼 Поиск вакансии', callback_data='search_vacancy'))
    keyboard.add(types.InlineKeyboardButton(text='👨‍🏫 Поиск курса', callback_data='search_course'))
    keyboard.add(types.InlineKeyboardButton(text='⚙️ Фильтры вакансий', callback_data='vacancy_filters'))
    keyboard.add(types.InlineKeyboardButton(text='⚙️ Фильтры курсов', callback_data='course_filters'))
    keyboard.adjust(1, 2, 2)

    text = ('Главное меню\n\n'
            f'<b>{user["name"]}</b>, {user["age"]}\n'
            f'Город: {user["city"]}\n')
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        if isinstance(data, types.CallbackQuery):
            await data.answer()
        await message.answer(text, reply_markup=keyboard.as_markup())


@dp.message(F.text[0] != '/', BasicStates.assistantChat)
@dp.callback_query(F.data == 'get_order')
async def get_order(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    state_data = await state.get_data()

    if isinstance(data, types.CallbackQuery):
        state_data['chat'] = [{"role": "system", "content": get_order_prompt}, {"role": "user", "content": 'Привет'}]
        await data.answer()
        await state.set_state(BasicStates.assistantChat)
    else:
        state_data['chat'] = state_data.get('chat', []) + [{"role": "user", "content": message.text}]

    res = await groq_client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=state_data['chat'],
    )
    ans = res.choices[0].message.content
    if ans.startswith('{'):
        try:
            info = json.loads(ans)
        except Exception as e:
            logging.error('JSON load error: ' + str(e))
            return 0
        keyboard = InlineKeyboardBuilder()
        user = await database.get_user(message.chat.id)
        if 'knowledge' in ans:
            keyboard.row(types.InlineKeyboardButton(text='🔎 Начать поиск', callback_data='search_vacancy'))
            keyboard.row(types.InlineKeyboardButton(text='🏚 В меню', callback_data='start'))
            user['vacancy_filters'] = info
            if 'city' in user['vacancy_filters']:
                cities = api.hh_get_city(message.text)
                user['vacancy_filters'].update({'city': cities[0]}) if cities else user['vacancy_filters'].pop('city')
            await database.update_user(message.chat.id, {'vacancy_filters': user['vacancy_filters']})
            text = 'Хорошо, вот такие фильтры устанавливаю для поиска вакансий:\n'
            for key, value in user['vacancy_filters'].items():
                if key == 'city':
                    value = value['name']
                elif key in choose_vacancy_filters:
                    value = next((e for e in choose_vacancy_filters[key] if e['id'] == value))['name']
                text += f'\n{vacancy_filters_names[key]}: {value}'

            await message.answer(text, reply_markup=keyboard.as_markup())
        else:
            keyboard.row(types.InlineKeyboardButton(text='🔎 Начать поиск', callback_data='search_course'))
            keyboard.row(types.InlineKeyboardButton(text='🏚 В меню', callback_data='start'))
            user['course_filters'] = info
            await database.update_user(message.chat.id, {'course_filters': user['course_filters']})
            text = 'Хорошо, вот такие фильтры устанавливаю для поиска курсов:\n'
            for key, value in user['course_filters'].items():
                if key == 'difficulty':
                    value = course_difficulty_names[value]
                if key == 'is_paid' and not value:
                    text += '\nБесплатный курс'
                    continue
                if key == 'with_certificate':
                    continue
                text += f'\n{course_filters_names[key]}: {value}'

            await message.answer(text, reply_markup=keyboard.as_markup())

        return 0

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='🏚 В меню', callback_data='start'))

    state_data['chat'] += [{"role": "assistant", "content": ans}]
    await state.update_data(chat=state_data['chat'])
    await message.answer(ans, reply_markup=keyboard.as_markup())
