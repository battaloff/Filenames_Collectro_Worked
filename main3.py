import os
import sqlite3
import time

# Connect to the database
conn = sqlite3.connect('files.db')
c = conn.cursor()

# Create the table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS files
             (filename TEXT UNIQUE, created_at INTEGER)''')

# List of folders to scan
folders = [r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175',
           r'\\192.168.1.41\d\spood folder\cmyk 175',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_CMYK',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_CMYK',
           r'\\192.168.1.45\#spoolfolder\175 ipi CMYK',
           r'\\192.168.1.38\e\SPOOL FOLDER\MONOCHROME 175',
           r'\\192.168.1.38\e\SPOOL FOLDER\CMYK 175 NOT OVER',
           r'\\192.168.1.41\d\spood folder\monochrome 175',
           r'\\192.168.1.41\d\spood folder\CMYK 175 NOT OVER',
           r'\\192.168.1.45\#spoolfolder\175 ipi MONO',
           r'\\192.168.1.45\#spoolfolder\175 lpi CMYK NOT OVER',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_MONO',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\175_CMYK_NOTOVER',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_MONO',
           r'\\192.168.1.85\d\#HOTFOLDER_HARLEQ\P_175_CMYK_NOTOVER',
           ]

while True:
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                created_at = int(os.path.getctime(file_path))

                # Check if the file has already been recorded in the database within the last 2 minutes
                current_time = int(time.time())
                two_minutes_ago = current_time - 120

                try:
                    # Insert the file into the database
                    c.execute("INSERT INTO files VALUES (?, ?)", (file, created_at))
                    conn.commit()
                except sqlite3.IntegrityError:
                    # Ignore the error if the file already exists in the database
                    pass

    # Wait for 1 minute before scanning again
    time.sleep(1)
