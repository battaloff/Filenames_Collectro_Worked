import sqlite3

def add_file_hash_column(db_path):
    """Добавление столбца file_hash в таблицу tasks_politext_tabletask"""
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверка существования столбца
        cursor.execute("PRAGMA table_info(tasks_politext_tabletask)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'file_hash' not in columns:
            # Добавление столбца
            cursor.execute("ALTER TABLE tasks_politext_tabletask ADD COLUMN file_hash TEXT")
            conn.commit()
            print("Столбец file_hash успешно добавлен.")
        else:
            print("Столбец file_hash уже существует.")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        conn.close()

# Путь к базе данных - замените на ваш реальный путь
db_path = r'D:\###TASKS\newproject\politext_tasks\db.sqlite3'
add_file_hash_column(db_path)