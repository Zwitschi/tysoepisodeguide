import os
import sqlite3

class Database:
    def __init__(self) -> None:
        self.BASE_DIR = os.getcwd()
        self.DB_FILE = os.path.join(self.BASE_DIR, 'db', 'tysodb.db')
        self.connection = sqlite3.connect(self.DB_FILE)
        self.install()
        
    def create_tables(self) -> None:
        """Calls create functions for Channels and Videos"""
        Channels().create()
        Videos().create()
        
    def create_db(self) -> None:
        """Create database file"""
        c = self.connection.cursor()
        c.execute('''SELECT * FROM sqlite_master WHERE type='table' ''')
        self.connection.close()
        
    def install(self) -> None:
        """Install the database and create the tables if needed."""
        if not os.path.exists(os.path.join(self.BASE_DIR, 'db')):
            os.makedirs(os.path.join(self.BASE_DIR, 'db'))
        if not os.path.exists(self.DB_FILE):
            self.create_tables()
            
    def check_install(self) -> bool:
        """Check if database is installed"""
        if os.path.exists(self.DB_FILE):
            return True
        else:
            return False
    
class Channels(Database):
    def __init__(self) -> None:
        super().__init__()
        
    def create(self) -> None:
        """
        Create channel table

        Args:
            channel (dict): channel details
        """
        c = self.connection.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            last_updated TEXT
        )
        ''')
        self.connection.commit()
        self.connection.close()
        
    def insert(self, channel: dict) -> None:
        """
        Insert channel into database

        Args:
            channel (dict): channel details
        """
        c = self.connection.cursor()
        c.execute('INSERT INTO channels (id, title, url, last_updated) VALUES (?, ?, ?, ?)', (channel['id'], channel['title'], channel['url'], channel['last_updated']))
        self.connection.commit()
        self.connection.close()

    def read(self) -> dict:
        """"Read channel from database"""
        c = self.connection.cursor()
        c.execute("SELECT * FROM channels WHERE id = 'UCYCGsNTvYxfkPkfQopRMP7w'")
        row = c.fetchone()
        self.connection.close()
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
        
class Videos(Database):
    def __init__(self) -> None:
        super().__init__()
        self.create()
        
    def create(self) -> None:
        """Create videos table in database"""
        c = self.connection.cursor()
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
        self.connection.commit()
        self.connection.close()
    
    def insert(self, video: dict) -> None:
        """Insert video into database"""
        c = self.connection.cursor()
        c.execute('INSERT INTO videos (id, title, url, description, thumb, published_date, duration, number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (video['id'], video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number']))
        self.connection.commit()
        self.connection.close()
    
    def update(self, video: dict) -> None:
        """Update video in database"""
        c = self.connection.cursor()
        c.execute('UPDATE videos SET title = ?, url = ?, description = ?, thumb = ?, published_date = ?, duration = ?, number = ? WHERE id = ?', (video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number'], video['id']))
        self.connection.commit()
        self.connection.close()
        
    def update_number(self, video_id: str, number: str) -> None:
        """Update video number in database"""
        c = self.connection.cursor()
        c.execute('UPDATE videos SET number = ? WHERE id = ?', (number, video_id))
        self.connection.commit()
        self.connection.close()
        
    def read_ids(self) -> list:
        """Read all video ids from database"""
        c = self.connection.cursor()
        c.execute('SELECT id FROM videos')
        rows = c.fetchall()
        rows = [r[0] for r in rows]
        self.connection.close()
        return rows
    
    def read(self, video_id: str) -> list:
        """Read video from database"""
        c = self.connection.cursor()
        c.execute("SELECT * FROM videos WHERE id = '" + video_id + "'")
        row = c.fetchone()
        self.connection.close()
        return row

    def read_videos(self, order='ASC'):
        """
        Read all episode videos from database

        Arguements:
            order (str): order to sort videos by. Default is ASC, can be DESC

        Returns:
            list: list of videos
        """
        c = self.connection.cursor()
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
        self.connection.close()
        return rows