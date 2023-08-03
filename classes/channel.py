"""
Class for youtube channel info

"""
from datetime import datetime

class Channel:
    def __init__(self, channel_id, title, url, last_updated):
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
    
    def check_channel_update(self):
        """
        Check if the channel has been updated since last update
        """
        # get last updated
        last_updated = datetime.strptime(self.last_updated, '%Y-%m-%d')
        # get today
        today = datetime.today()
        # check if last updated is before today
        if last_updated < today:
            return True
        else:
            return False
        
    def update_channel(self, last_updated):
        """
        Update the channel
        """
        self.last_updated = last_updated

    