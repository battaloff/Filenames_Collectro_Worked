"""
Politext Folder Monitor
Мониторинг сетевых папок и запись PDF-файлов в базу данных.
"""

import os
import sqlite3
import time
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

import pytz

# ═══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

# База данных
DB_PATH = r'H:\WORKED_PROGRAMMS_POLITEXT\politext_tasks\db.sqlite3'

# Временная зона
TIMEZONE = pytz.timezone('Asia/Tashkent')

# Корневые папки для мониторинга (все подпапки сканируются автоматически)
ROOT_FOLDERS = [
    r'\\192.168.1.45\e\#SPOOLFOLDER',
    r'\\192.168.1.248\e\#SPOOLFOLDER',
    r'\\192.168.1.44\#shared\#INPUT_FOLDER\NEW_TERMAL',
    r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ',
]

# Сопоставление IP → Оборудование
EQUIPMENT_MAP = {
    '192.168.1.45': 'AURORA',
    '192.168.1.248': 'BLUE',
    '192.168.1.44': 'NEW',
    '192.168.1.85': 'TERMAL',
}

# Интервалы сканирования (секунды)
SCAN_INTERVAL = 1.0  # Пауза между полными сканами
FILE_DELAY = 0.05  # Пауза между файлами (снижает нагрузку на сеть)

# Расширения файлов для обработки
FILE_EXTENSIONS = {'.pdf'}

# ═══════════════════════════════════════════════════════════════════════════════
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('folder_monitor.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# РАБОТА С БАЗОЙ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Менеджер соединения с SQLite базой данных."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Установить соединение с БД."""
        self.conn = sqlite3.connect(self.db_path, timeout=30)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Подключено к базе данных: {self.db_path}")

    def disconnect(self) -> None:
        """Закрыть соединение с БД."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Соединение с БД закрыто")

    def reconnect(self) -> None:
        """Переподключиться к БД."""
        self.disconnect()
        time.sleep(1)
        self.connect()

    def file_exists_today(self, filename: str) -> bool:
        """Проверить, был ли файл уже записан сегодня."""
        today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM tasks_politext_tabletask 
            WHERE file_name = ? AND date(add_date_time) = ?
            LIMIT 1
            """,
            (filename, today)
        )
        return cursor.fetchone() is not None

    def insert_file(self, filename: str, created_at: int, equipment: str) -> bool:
        """Вставить запись о файле в БД."""
        try:
            add_date_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks_politext_tabletask 
                (file_name, created_at, add_date_time, stage, equipment) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (filename, created_at, add_date_time, 'На выводе', equipment)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка вставки в БД: {e}")
            self.conn.rollback()
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

def extract_ip_from_path(path: str) -> Optional[str]:
    """Извлечь IP-адрес из UNC-пути."""
    # \\192.168.1.45\... → 192.168.1.45
    if path.startswith('\\\\'):
        parts = path[2:].split('\\')
        if parts:
            return parts[0]
    return None


def get_equipment(file_path: str) -> str:
    """Определить оборудование по пути к файлу."""
    ip = extract_ip_from_path(file_path)
    return EQUIPMENT_MAP.get(ip, 'UNKNOWN')


def safe_get_ctime(file_path: str) -> Optional[int]:
    """
    Безопасно получить время создания файла.
    Возвращает None если файл недоступен (исчез, заблокирован и т.д.)
    """
    try:
        return int(os.path.getctime(file_path))
    except (FileNotFoundError, OSError, PermissionError):
        return None


def is_valid_file(filename: str) -> bool:
    """Проверить, подходит ли файл для обработки."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in FILE_EXTENSIONS


def safe_walk(root_folder: str):
    """
    Безопасный обход директории.
    Пропускает недоступные папки без падения.
    """
    try:
        for root, dirs, files in os.walk(root_folder):
            # Фильтруем только нужные файлы
            pdf_files = [f for f in files if is_valid_file(f)]
            yield root, pdf_files
    except (FileNotFoundError, OSError, PermissionError) as e:
        logger.warning(f"Не удалось просканировать {root_folder}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ КЛАСС МОНИТОРА
# ═══════════════════════════════════════════════════════════════════════════════

class FolderMonitor:
    """Монитор папок для отслеживания новых PDF-файлов."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.stats = {
            'scans': 0,
            'files_found': 0,
            'files_added': 0,
            'errors': 0,
        }

    def process_file(self, file_path: str, filename: str) -> None:
        """Обработать один файл."""
        # Получаем время создания (файл может уже исчезнуть)
        created_at = safe_get_ctime(file_path)
        if created_at is None:
            # Файл исчез — это нормально, просто пропускаем
            return

        self.stats['files_found'] += 1

        # Проверяем, записан ли уже сегодня
        try:
            if self.db.file_exists_today(filename):
                return
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки в БД: {e}")
            self.stats['errors'] += 1
            return

        # Определяем оборудование
        equipment = get_equipment(file_path)

        # Вставляем в БД
        if self.db.insert_file(filename, created_at, equipment):
            self.stats['files_added'] += 1
            logger.info(f"✓ Добавлен: {filename} [{equipment}]")

    def scan_folder(self, root_folder: str) -> None:
        """Просканировать одну корневую папку и все подпапки."""
        for root, files in safe_walk(root_folder):
            for filename in files:
                file_path = os.path.join(root, filename)

                try:
                    self.process_file(file_path, filename)
                except Exception as e:
                    # Ловим любые неожиданные ошибки
                    logger.error(f"Ошибка обработки {file_path}: {e}")
                    self.stats['errors'] += 1

                # Небольшая пауза для снижения нагрузки на сеть
                time.sleep(FILE_DELAY)

    def scan_all(self) -> None:
        """Просканировать все корневые папки."""
        self.stats['scans'] += 1

        for folder in ROOT_FOLDERS:
            # Проверяем доступность папки перед сканированием
            if not os.path.exists(folder):
                logger.warning(f"Папка недоступна: {folder}")
                continue

            self.scan_folder(folder)

    def run(self) -> None:
        """Запустить бесконечный цикл мониторинга."""
        logger.info("=" * 60)
        logger.info("ЗАПУСК МОНИТОРА ПАПОК")
        logger.info("=" * 60)
        logger.info(f"Мониторинг {len(ROOT_FOLDERS)} папок:")
        for folder in ROOT_FOLDERS:
            logger.info(f"  • {folder}")
        logger.info("=" * 60)

        while True:
            try:
                self.scan_all()
                time.sleep(SCAN_INTERVAL)

            except sqlite3.Error as e:
                logger.error(f"Ошибка БД: {e}. Переподключение...")
                self.stats['errors'] += 1
                try:
                    self.db.reconnect()
                except Exception as reconnect_error:
                    logger.error(f"Не удалось переподключиться: {reconnect_error}")
                    time.sleep(5)

            except KeyboardInterrupt:
                logger.info("Остановка по запросу пользователя (Ctrl+C)")
                break

            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
                self.stats['errors'] += 1
                time.sleep(5)

        self.print_stats()

    def print_stats(self) -> None:
        """Вывести статистику работы."""
        logger.info("=" * 60)
        logger.info("СТАТИСТИКА")
        logger.info(f"  Сканирований: {self.stats['scans']}")
        logger.info(f"  Файлов найдено: {self.stats['files_found']}")
        logger.info(f"  Файлов добавлено: {self.stats['files_added']}")
        logger.info(f"  Ошибок: {self.stats['errors']}")
        logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Главная функция."""
    db = DatabaseManager(DB_PATH)

    try:
        db.connect()
        monitor = FolderMonitor(db)
        monitor.run()
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()