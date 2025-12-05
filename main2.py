import sqlite3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Создаем соединение с базой данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS files
                  (name TEXT, modified_date TEXT)''')


# Создаем класс, который будет обрабатывать события файловой системы
class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            # Получаем название файла и дату изменения
            file_name = event.src_path
            modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Записываем данные в базу данных
            cursor.execute("INSERT INTO files VALUES (?, ?)", (file_name, modified_date))
            conn.commit()


# Создаем наблюдатель за папкой
# Create an instance of the observer and attach the event handler
observer = Observer()
observer.schedule(FileEventHandler(), path='path/to/folder', recursive=False)

# Start the observer
observer.start()
