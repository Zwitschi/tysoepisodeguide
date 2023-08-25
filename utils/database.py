import os
import sqlite3

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')

def read_videos(order='ASC'):
    """
    Read all episode videos from database

    Arguements:
        order (str): order to sort videos by. Default is ASC, can be DESC

    Returns:
        list: list of videos
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql = '''
    SELECT * FROM videos 
    WHERE duration > 1600 
    AND title NOT LIKE "%Rick Glassman & Esther Povitsky Have a Time%" 
    AND title NOT LIKE "%Playing some Magic: The Gathering%"
    AND title NOT LIKE "%Magic the Gathering LIVE from Marshall Rug Gallery%"
    and title NOT LIKE "%Take Your Shoes Off - BEST OF %"
    ORDER BY published_date ''' + order + ''';
    '''
    c.execute(sql)
    rows = c.fetchall()
    conn.close()
    return rows

def insert_channel(channel):
    """
    Insert channel into database

    Args:
        channel (dict): channel details
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO channels (id, title, url, last_updated) VALUES (?, ?, ?, ?)', (channel['id'], channel['title'], channel['url'], channel['last_updated']))
    conn.commit()
    conn.close()

def read_channel() -> dict:
    """"Read channel from database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE id = 'UCYCGsNTvYxfkPkfQopRMP7w'")
    row = c.fetchone()
    conn.close()
    # transform row into dict
    if row:
        channel = {
            'id': row[0],
            'title': row[1],
            'url': row[2],
            'last_updated': row[3]
        }
        return channel
    else:
        return None
    
def insert_video(video: dict) -> None:
    """Insert video into database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO videos (id, title, url, description, thumb, published_date, duration, number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (video['id'], video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number']))
    conn.commit()
    conn.close()

def update_video(video: dict) -> None:
    """Update video in database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE videos SET title = ?, url = ?, description = ?, thumb = ?, published_date = ?, duration = ?, number = ? WHERE id = ?', (video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number'], video['id']))
    conn.commit()
    conn.close()

def read_video_ids() -> list:
    """Read all video ids from database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM videos')
    rows = c.fetchall()
    # only 1 item in each row, transform to list
    rows = [r[0] for r in rows]
    conn.close()
    return rows

def read_video(video_id: str) -> list:
    """Read video from database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE id = '" + video_id + "'")
    row = c.fetchone()
    conn.close()
    return row

def create_db() -> None:
    """Create database file"""
    print('Creating db file')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT * FROM sqlite_master WHERE type='table' ''')
    tables = c.fetchall()
    print('Found ' + str(len(tables)) + ' tables')
    conn.close()
              
def create_tables() -> None:
    """Create database tables"""
    create_db()    
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
    print('Creating channels table')
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
    print('Creating videos table')
    conn.commit()
    conn.close()

def install() -> None:
    """
    Install the database and create the tables if needed.
    """
    # bit to check if installation has been done before
    is_installed = False
    # create db folder if not exists
    if not os.path.exists(os.path.join(BASE_DIR, 'db')):
        # create db folder
        print('Creating db folder')
        os.makedirs(os.path.join(BASE_DIR, 'db'))
    else:
        is_installed = True
        
    if not os.path.exists(DB_FILE):
        create_tables()
        print('Database created')
    else:
        is_installed = True
    
    if is_installed:
        print('Installation complete')