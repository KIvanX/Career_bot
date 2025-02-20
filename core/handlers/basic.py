from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import database, api
from core.config import dp
from core.registration import registration
from core.utils import get_salary


@dp.callback_query(F.data == 'start')
async def start(data, state: FSMContext):
    message: types.Message = data.message if isinstance(data, types.CallbackQuery) else data
    await state.clear()

    user = await database.get_user(message.chat.id)
    if not user:
        return await registration(message, state)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text='Поиск вакансии', callback_data='search_vacancy'))
    keyboard.add(types.InlineKeyboardButton(text='Поиск курса', callback_data='search_courses'))
    keyboard.add(types.InlineKeyboardButton(text='Фильтры вакансий', callback_data='vacancy_filters'))
    keyboard.add(types.InlineKeyboardButton(text='Фильтры курсов', callback_data='courses_filters'))
    keyboard.adjust(2)

    text = ('Главное меню\n\n'
            f'<b>{user["name"]}</b>, {user["age"]}\n'
            f'Город: {user["city"]}\n'
            f'Интересы: {user["interests"]}')
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    except:
        if isinstance(data, types.CallbackQuery):
            await data.answer()
        await message.answer(text, reply_markup=keyboard.as_markup())


@dp.callback_query(F.data == 'search_vacancy')
async def search_vacancy(call: types.CallbackQuery, state: FSMContext):
    page = (await state.get_data()).get('page', -1) + 1
    user = await database.get_user(call.message.chat.id)
    vacancies = api.hh_get_vacancies(user['interests'], user['vacancy_filters'], page)

    if not vacancies:
        return await call.answer('Больше вакансий по заданным фильтрам нет')
    vacancy = vacancies[0]

    await state.update_data(page=page)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text='Подробнее', url=vacancy['alternate_url']))
    keyboard.row(types.InlineKeyboardButton(text=f'Далее', callback_data='search_vacancy'))
    keyboard.row(types.InlineKeyboardButton(text='Назад', callback_data='start'))

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
