## Поиск курсов и вакансий

### Описание
Бот для поиска обучающих курсов и вакансий по фильтрам или описанию.

### Установка и запуск
1. Склонируйте репозиторий
```bash
git clone https://github.com/KIvanX/Career_bot.git
```
2. Установите зависимости
```bash
pip install -r requirements.txt
```
3. Создайте файл `.env` в корне проекта и добавьте в него 
переменные окружения. Необходимые переменные находятся в `.env.exemple`

4. Создайте базу данных и таблицу пользователей
```sql
create database career_bot;

create table users
(
    user_id         bigint not null primary key,
    name            varchar(255),
    age             integer,
    city            varchar(255),
    vacancy_filters json default '{}'::json,
    course_filters  json default '{}'::json
);

create table messages
(
    id              serial primary key,
    user_id         bigint not null,
    role            varchar(64),
    content         text,
    created_at      timestamp default now()
);
```

5. Запустите бота
```bash
python main.py
```

### Используемые технологии
- Python 3.10 - язык программирования
- PostgreSQL - база данных

### Библиотеки
- aiogram - фреймворк для создания ботов
- asyncpg - асинхронный драйвер для работы с PostgreSQL
- python-dotenv - загрузка переменных окружения из файла `.env`
- requests - библиотека для отправки HTTP запросов
- groq - библиотека для работы с языковыми моделями
