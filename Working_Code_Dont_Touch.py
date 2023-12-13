import os
import sqlite3
import time
from datetime import datetime
import pytz

# TODO
"""D:\#Adrenaline\Loop\venv\Scripts\python.exe D:\#Adrenaline\Loop\Working_Code_Dont_Touch.py 
Traceback (most recent call last):
  File "D:\#Adrenaline\Loop\Working_Code_Dont_Touch.py", line 96, in <module>
    conn.commit()
sqlite3.OperationalError: database is locked

Process finished with exit code 1"""



# Connect to the database
conn = sqlite3.connect(r'D:\###TASKS\newproject\politext_tasks\db.sqlite3')
c = conn.cursor()

# List of folders to scan
folders = [r'\\192.168.1.45\#spoolfolder\100 LPI CMYK',  # AURORA  100 LPI CMYK
           r'\\192.168.1.45\#spoolfolder\150 lpi CMYK',  # AURORA  150 LPI CMYK
           r'\\192.168.1.45\#spoolfolder\175 ipi CMYK',  # AURORA  175 LPI CMYK
           r'\\192.168.1.45\#spoolfolder\175 ipi MONO',  # AURORA  175 LPI MONO
           r'\\192.168.1.45\#spoolfolder\175 lpi CMYK NOT OVER',  # AURORA  175 LPI CMYK NOT OVER

           r'\\192.168.1.41\d\spood folder\cmyk 100',  # BLUE 100 LPI CMYK
           r'\\192.168.1.41\d\spood folder\cmyk 175',  # BLUE 175 LPI CMYK
           r'\\192.168.1.41\d\spood folder\CMYK 175 NOT OVER',  # BLUE 175 LPI CMYK NOT OVER
           r'\\192.168.1.41\d\spood folder\monochrome 100',  # BLUE 100 LPI MONO
           r'\\192.168.1.41\d\spood folder\monochrome 175',  # BLUE 175 LPI MONO

           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 100',  # GREEN 100 LPI CMYK
           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 150',  # GREEN 150 LPI CMYK
           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175',  # GREEN 175 LPI CMYK
           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175',  # GREEN 175 LPI CMYK
           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175 NOT OVER',  # GREEN 175 LPI CMYK
           r'\\192.168.1.38\e\SPOOL FOLDER\MONOCHROME 100',  # GREEN 100 LPI MONO
           r'\\192.168.1.38\e\SPOOL FOLDER\MONOCHROME 175',  # GREEN 175 LPI MONO

           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\100_CMYK',  # TERMAL 100 LPI CMYK
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\100_MONO',  # TERMAL 100 LPI MONO
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_CMYK',  # TERMAL 175 LPI CMYK
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_CMYK_NOTOVER',  # TERMAL 175 LPI CMYK NOTOVER
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_MONO',  # TERMAL 175 LPI MONO
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\200_LPI',  # TERMAL 200 LPI CMYK
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_CMYK',  # TERMAL 175 LPI CMYK PANCH
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_CMYK_NOTOVER',  # TERMAL 175 LPI CMYK PANCH NOTOVER
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_MONO',  # TERMAL 175 LPI MONO PANCH
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\M_PUNCH_CMYK_175',  # TERMAL 175 LPI CMYK PANCH
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\M_PUNCH_MONO_175',  # TERMAL 175 LPI MONO PANCH

           ]

# Folder equipment mapping
folder_equipment_mapping = {
    r'\\192.168.1.41': 'BLUE',
    r'\\192.168.1.38': 'GREEN',
    r'\\192.168.1.45': 'AURORA',
    r'\\192.168.1.85': 'TERMAL',

    # Add other folders and their mappings here
}

"""
Надо сделать так чтобы итерировались только файлы с расширением .pdf
И чтобы в базу данных записывалось время создания файла, а не время записи в базу данных
"""


while True:
    for folder in folders:
        for root, dirs, files in os.walk(folder):

            for file in files:
                if not file.endswith(".pdf"):
                    continue

                file_path = os.path.join(root, file)

                # Попробуйте получить время создания файла
                try:
                    created_at = int(os.path.getctime(file_path))
                except FileNotFoundError:
                    # Обработка ошибки
                    continue

                # Check if the file has already been recorded in the database within the last 2 minutes
                current_time = int(time.time())
                two_minutes_ago = current_time - 1200
                c.execute("SELECT created_at FROM tasks_politext_tabletask WHERE file_name = ? AND created_at > ?",
                          (file, two_minutes_ago))
                existing_files = c.fetchall()

                if not existing_files:
                    # Insert the file into the database
                    add_date_time = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d %H:%M:%S')
                    stage = 'На выводе'
                    c.execute(
                        "INSERT INTO tasks_politext_tabletask (file_name, created_at, add_date_time, stage) VALUES (?, ?, ?, ?)",
                        (file, created_at, add_date_time, stage))
                    conn.commit()

                    # Get the folder equipment
                    folder_name = os.path.dirname(file_path)
                    equipment = None
                    for folder, folder_equipment in folder_equipment_mapping.items():
                        if folder_name.startswith(folder):
                            equipment = folder_equipment
                            break

                    # Update the equipment column in the database
                    c.execute("UPDATE tasks_politext_tabletask SET equipment = ? WHERE file_name = ?",
                              (equipment, file))
                    conn.commit()

                # Wait for 1 second before scanning again
            time.sleep(0.1)


# while True:
#     for folder in folders:
#         for root, dirs, files in os.walk(folder):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 created_at = int(os.path.getctime(file_path))

# while True:
#     for folder in folders:
#         for root, dirs, files in os.walk(folder):
#
#             for file in files:
#                 file_path = os.path.join(root, file)
#
#                 # Попробуйте получить время создания файла
#                 try:
#                     created_at = int(os.path.getctime(file_path))
#                 except FileNotFoundError:
#                     # Обработка ошибки
#                     continue
#
#                 # Check if the file has already been recorded in the database within the last 2 minutes
#                 current_time = int(time.time())
#                 two_minutes_ago = current_time - 1200
#                 c.execute("SELECT created_at FROM tasks_politext_tabletask WHERE file_name = ? AND created_at > ?",
#                           (file, two_minutes_ago))
#                 existing_files = c.fetchall()
#
#                 if not existing_files:
#                     # Insert the file into the database
#                     add_date_time = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d %H:%M:%S')
#                     stage = 'На выводе'
#                     c.execute(
#                         "INSERT INTO tasks_politext_tabletask (file_name, created_at, add_date_time, stage) VALUES (?, ?, ?, ?)",
#                         (file, created_at, add_date_time, stage))
#                     conn.commit()
#
#                     # Get the folder equipment
#                     folder_name = os.path.dirname(file_path)
#                     equipment = None
#                     for folder, folder_equipment in folder_equipment_mapping.items():
#                         if folder_name.startswith(folder):
#                             equipment = folder_equipment
#                             break
#
#                     # Update the equipment column in the database
#                     c.execute("UPDATE tasks_politext_tabletask SET equipment = ? WHERE file_name = ?",
#                               (equipment, file))
#                     conn.commit()
#
#                 # Wait for 1 second before scanning again
#             time.sleep(0.1)

# 29-08-2023 // 12:08
# Скрипт

#
# import os
# import sqlite3
# import time
# from datetime import datetime
#
# # Connect to the database
# conn = sqlite3.connect(r'D:\###TASKS\newproject\politext_tasks\db.sqlite3')
# c = conn.cursor()
#
# # List of folders to scan
# folders = [r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175',
#            r'\\192.168.1.41\d\spood folder\cmyk 175',созданный_at = datetime.fromtimestamp(os.path.getctime(file_path), pytz.timezone('Азия/Ташкент'))
#            r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_CMYK',
#            r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_CMYK',
#            ]
#
# while True:
#     for folder in folders:
#         for root, dirs, files in os.walk(folder):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 created_at = int(os.path.getctime(file_path))
#
#                 # Check if the file has already been recorded in the database within the last 2 minutes
#
#                 current_time = int(time.time())
#                 two_minutes_ago = current_time - 1200
#                 c.execute("SELECT created_at FROM tasks_politext_tabletask WHERE file_name = ? AND created_at > ?",
#                           (file, two_minutes_ago))
#                 existing_files = c.fetchall()
#
#                 if not existing_files:
#                     # Insert the file into the database
#                     add_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     stage = 'На выводе'
#                     c.execute(
#                         "INSERT INTO tasks_politext_tabletask (file_name, created_at, add_date_time, stage) VALUES (?, ?, ?, ?)",
#                         (file, created_at, add_date_time, stage))
#                     conn.commit()
#
#             # Wait for 1 second before scanning again
#             time.sleep(1)
