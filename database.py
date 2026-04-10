import aiosqlite
from datetime import datetime
from config import DATABASE_PATH, ROLES

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'ученик',
                code_name TEXT,
                age INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                warnings INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                time_limit TEXT,
                client_name TEXT,
                sent_time TEXT,
                urgency TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS task_solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                answer_text TEXT,
                answer_file_id TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                curator_id INTEGER,
                score INTEGER,
                curator_comment TEXT,
                evaluated_at TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES tasks(id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, role, code_name, age, joined_at, warnings FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row

async def add_user(user_id: int, username: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

async def update_user_profile(user_id: int, code_name: str = None, age: int = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if code_name is not None:
            await db.execute("UPDATE users SET code_name = ? WHERE user_id = ?", (code_name, user_id))
        if age is not None:
            await db.execute("UPDATE users SET age = ? WHERE user_id = ?", (age, user_id))
        await db.commit()

async def get_user_role(user_id: int) -> str:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "ученик"

async def set_user_role(user_id: int, role: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, role) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET role = ?",
            (user_id, role, role)
        )
        await db.commit()

async def add_warning(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def reset_warnings(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def is_admin(user_id: int) -> bool:
    role = await get_user_role(user_id)
    return ROLES.get(role, 0) >= ROLES["админ"]

async def is_curator_or_higher(user_id: int) -> bool:
    role = await get_user_role(user_id)
    return ROLES.get(role, 0) >= ROLES["куратор"]

async def add_task(description, time_limit, client_name, sent_time, urgency, created_by):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO tasks (description, time_limit, client_name, sent_time, urgency, created_by) VALUES (?, ?, ?, ?, ?, ?)",
            (description, time_limit, client_name, sent_time, urgency, created_by)
        )
        await db.commit()

async def get_tasks(limit=5):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, description, time_limit, client_name, sent_time, urgency, created_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def get_task_by_id(task_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, description, time_limit, client_name, sent_time, urgency, created_by FROM tasks WHERE id = ?",
            (task_id,)
        ) as cursor:
            return await cursor.fetchone()

async def add_solution(task_id: int, user_id: int, answer_text: str = None, file_id: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO task_solutions (task_id, user_id, answer_text, answer_file_id) VALUES (?, ?, ?, ?)",
            (task_id, user_id, answer_text, file_id)
        )
        await db.commit()
        async with db.execute("SELECT created_by FROM tasks WHERE id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def evaluate_solution(solution_id: int, curator_id: int, score: int, comment: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE task_solutions SET status = 'evaluated', curator_id = ?, score = ?, curator_comment = ?, evaluated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (curator_id, score, comment, solution_id)
        )
        await db.commit()

async def get_top_students(limit=5):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT u.user_id, u.username, u.code_name, AVG(s.score) as avg_score, COUNT(s.id) as solutions_count
            FROM users u
            JOIN task_solutions s ON u.user_id = s.user_id
            WHERE s.status = 'evaluated' AND s.score IS NOT NULL
            GROUP BY u.user_id
            HAVING solutions_count > 0
            ORDER BY avg_score DESC
            LIMIT ?
        ''', (limit,)) as cursor:
            return await cursor.fetchall()

async def add_faq(question: str, answer: str, created_by: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO faq (question, answer, created_by) VALUES (?, ?, ?)",
            (question, answer, created_by)
        )
        await db.commit()

async def get_faq(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, question, answer, created_at FROM faq ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()