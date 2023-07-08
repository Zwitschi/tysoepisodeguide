import os
import sqlite3

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')

def main():
    # create db folder if not exists
    if not os.path.exists(os.path.join(BASE_DIR, 'db')):
        os.makedirs(os.path.join(BASE_DIR, 'db'))

    if not os.path.isfile(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            last_updated TEXT
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY, 
            title TEXT, 
            url TEXT, 
            description TEXT, 
            thumb TEXT, 
            published_date TEXT, 
            duration INTEGER, 
            number TEXT 
        )
        ''')
        conn.commit()
        conn.close()

    from setuptools import setup, find_packages

    setup(
        name='tysoepisodeguide',
        version='0.1',
        packages=find_packages(),
        install_requires=[
            "requests",
            "Flask",
            "markdown",
            "python-dotenv"
        ]
    )

if __name__ == '__main__':
    main()