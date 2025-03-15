import json
import os
import asyncpg
from core.config import dp


async def get_db_pool():
    db_pool = await asyncpg.create_pool(host=os.environ['DB_HOST'],
                                        database=os.environ['DB_NAME'],
                                        user=os.environ['DB_USER'],
                                        password=os.environ['DB_PASSWORD'])
    return db_pool


async def add_user(user_id: int, name, age, city, vacancy_filters, course_filters):
    async with dp.db_pool.acquire() as connection:
        await connection.execute('INSERT INTO users(user_id, name, age, city, vacancy_filters, course_filters) '
                                 'VALUES ($1, $2, $3, $4, $5, $6)', user_id, name, age, city,
                                 json.dumps(vacancy_filters, ensure_ascii=False),
                                 json.dumps(course_filters, ensure_ascii=False))


async def get_user(user_id):
    async with dp.db_pool.acquire() as connection:
        user = await connection.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        if user:
            user = dict(user)
            user['vacancy_filters'] = json.loads(user['vacancy_filters'])
            user['course_filters'] = json.loads(user['course_filters'])
            return user
        return {}


async def update_user(user_id: int, data: dict):
    async with dp.db_pool.acquire() as connection:
        for key in data:
            data[key] = json.dumps(data[key], ensure_ascii=False) if isinstance(data[key], dict) else data[key]
            await connection.execute(f'UPDATE users SET {key} = $1 WHERE user_id = $2', data[key], user_id)
