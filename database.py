import logging
import sqlite3
from sqlite3 import Error

from config import inbox_path

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filename = 'bot.log', encoding = 'UTF-8', datefmt = '%Y-%m-%d %H:%M:%S')

def create_connection():
    """Create a database connection to the SQLite database"""
    try:
        conn = sqlite3.connect('bot_settings.db')
        return conn
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def init_database():
    """Create the settings table if it doesn't exist"""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS chat_settings
                (chat_id INTEGER PRIMARY KEY,
                 notes_folder TEXT NOT NULL)
            ''')
            conn.commit()
        except Error as e:
            logging.error(f"Error creating table: {e}")
        finally:
            conn.close()

def set_notes_folder(chat_id, folder_path) -> str:
    # Save to database
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO chat_settings (chat_id, notes_folder)
                VALUES (?, ?)
            ''', (chat_id, folder_path))
            conn.commit()
            result = f"Notes folder for {chat_id} set to: {folder_path}"
            logging.info(result)
        except Error as e:
            result = f"Error saving settings for for {chat_id}: {e}"
            logging.error(result)
        finally:
            conn.close()
            return result

def get_notes_folder(chat_id) -> str:
    conn = create_connection()
    folder_path = ""
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute('SELECT notes_folder FROM chat_settings WHERE chat_id = ?', 
                    (chat_id,))
            row = c.fetchone()
            if row:
                folder_path = row[0]
        except Error as e:
            logging.error(f"Database error: {e}")
        finally:
            conn.close()
    return folder_path

init_database()