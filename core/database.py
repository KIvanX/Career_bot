import json
import os
import asyncpg
from core.config import dp


async def get_db_pool():
    db_pool = await asyncpg.create_pool(host=os.environ['POSTGRES_HOST'],
                                        database=os.environ['POSTGRES_DB'],
                                        user=os.environ['POSTGRES_USER'],
                                        password=os.environ['POSTGRES_PASSWORD'])
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


async def add_message(user_id: int, role: str, content: str):
    async with dp.db_pool.acquire() as connection:
        await connection.execute(f'INSERT INTO messages(user_id, role, content) VALUES ($1, $2, $3)', user_id, role, content)


async def get_messages(user_id: int):
    async with dp.db_pool.acquire() as connection:
        messages = []
        for m in await connection.fetch(f'SELECT role, content FROM messages WHERE user_id = $1', user_id):
            messages.append({'role': m[0], 'content': m[1]})
        return messages


async def delete_account(user_id):
    async with dp.db_pool.acquire() as connection:
        await connection.execute('DELETE FROM users WHERE user_id = $1', user_id)
        await connection.execute('DELETE FROM messages WHERE user_id = $1', user_id)
