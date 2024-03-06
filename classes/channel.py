"""
Class for youtube channel info

"""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')

class Channel:
    def __init__(self, channel_id, title=None, url=None, last_updated=None):
        self.channel_id = channel_id
        self.title = title
        self.url = url
        self.last_updated = last_updated

    def __str__(self):
        return self.title + ' ' + self.url + ' ' + self.last_updated
    
    def to_dict(self):
        return {
            'channel_id': self.channel_id,
            'title': self.title,
            'url': self.url,
            'last_updated': self.last_updated
        }
    
    def set_last_updated(self, last_updated):
        self.last_updated = last_updated

    def read_channel_db(self, channel_id):
        """"
        Read channel from database

        Args:
            channel_id (str): channel id
            
        Returns:
            list: channel details
        """
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
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

    def check_channel_update_db(self):
        """
        Check if the channel was updated in the last 24 hours

        Returns:
            bool: True if updated in the last 24 hours, False otherwise
        """
        now = datetime.now().timestamp()
        db_channel = self.read_channel_db(self.channel_id)
        if db_channel:
            last_update = float(db_channel['last_updated'])
            if now - last_update < 86400:
                return True
            else:
                return False
                
    def update_channel_db(self):
        """
        Update the channel in the database
        """
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('UPDATE channels SET last_updated = ? WHERE id = ?', (self.last_updated, self.channel_id))
        conn.commit()
        conn.close()
    