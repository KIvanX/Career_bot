import json
import logging

from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import database, api
from core.config import dp, groq_client, LLM_MODEL_NAME
from core.handlers.registration import registration
from core.states import BasicStates
from core.variables import get_order_prompt, choose_vacancy_filters, vacancy_filters_names, course_filters_names, \
    course_difficulty_names, get_dev_path_prompt


@dp.callback_query(F.data == 'start')
async def start(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    await state.clear()

    user = await database.get_user(message.chat.id)
    if not user:
        return await registration(message, state)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='🔮 Я хочу...', callback_data='get_order'))
    keyboard.add(types.InlineKeyboardButton(text='🎯 Траектория развития', callback_data='development_path'))
    keyboard.add(types.InlineKeyboardButton(text='💼 Поиск вакансии', callback_data='search_vacancy'))
    keyboard.add(types.InlineKeyboardButton(text='👨‍🏫 Поиск курса', callback_data='search_course'))
    keyboard.add(types.InlineKeyboardButton(text='⚙️ Фильтры вакансий', callback_data='vacancy_filters'))
    keyboard.add(types.InlineKeyboardButton(text='⚙️ Фильтры курсов', callback_data='course_filters'))
    keyboard.add(types.InlineKeyboardButton(text='🖊 Редактировать профиль', callback_data='update_profile'))
    keyboard.adjust(2, 2, 2, 1)

    text = ('<b>Главное меню</b>\n\n'
            f'<b>{user["name"]}</b>, {user["age"]}\n'
            f'<b>Город проживания:</b> {user["city"]}\n')
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        if isinstance(data, types.CallbackQuery):
            await data.answer()
        await message.answer(text, reply_markup=keyboard.as_markup())


async def delete_account_confirm(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Да, уверен', callback_data='delete_account'))
    keyboard.row(types.InlineKeyboardButton(text='Отмена', callback_data='delete_account_cancel'))

    await message.answer('Вы уверены, что хотите удалить свой профиль?\n\n'
                         '❗️ Траектория развития и фильтры поиска также будут удалены\n\n'
                         'Профиль можно будет создать заново.', reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == 'delete_account')
async def delete_account(call: types.CallbackQuery):
    await database.delete_account(call.message.chat.id)
    await call.message.edit_text('✅ Профиль удален')


@dp.callback_query(F.data == 'delete_account_cancel')
async def delete_account_cancel(call: types.CallbackQuery):
    await call.message.edit_text('✅ Удаление отменено')


@dp.callback_query(F.data == 'update_profile')
async def update_profile(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await registration(call.message, state)


@dp.message(F.text[0] != '/', BasicStates.orderAssistantChat)
@dp.callback_query(F.data == 'get_order')
async def get_order(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    state_data = await state.get_data()

    if isinstance(data, types.CallbackQuery):
        state_data['chat'] = [{"role": "system", "content": get_order_prompt}, {"role": "user", "content": 'Привет'}]
        await data.answer()
        await state.set_state(BasicStates.orderAssistantChat)
    else:
        state_data['chat'] = state_data.get('chat', []) + [{"role": "user", "content": message.text}]

    res = await groq_client.chat.completions.create(
        model=LLM_MODEL_NAME,
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


@dp.message(F.text[0] != '/', BasicStates.devPathAssistant)
@dp.callback_query(F.data == 'development_path')
async def development_path(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    chat = await database.get_messages(message.chat.id)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='🏚 В меню', callback_data='start'))

    if isinstance(data, types.CallbackQuery):
        await data.answer()
        await state.set_state(BasicStates.devPathAssistant)
        if not chat:
            chat.append({"role": "system", "content": get_dev_path_prompt})
            await database.add_message(message.chat.id, 'system', get_dev_path_prompt)
        elif chat[-1]['role'] == 'assistant':
            return await message.answer(chat[-1]['content'], reply_markup=keyboard.as_markup())
    else:
        chat.append({"role": "user", "content": message.text})
        await database.add_message(message.chat.id, 'user', message.text)

    res = await groq_client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=chat,
    )
    ans = res.choices[0].message.content

    await database.add_message(message.chat.id, 'assistant', ans)
    await message.answer(ans, reply_markup=keyboard.as_markup())
