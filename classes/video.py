"""
Class for youtube video info

"""
import re
from datetime import datetime

class Video:
    """Video class

    id TEXT PRIMARY KEY, 
    title TEXT, 
    url TEXT, 
    description TEXT, 
    thumb TEXT, 
    published_date TEXT, 
    duration INTEGER, 
    number TEXT
    
    """
    def __init__(self, id, title, url, description, thumb, published_date, duration):
        self.id = id
        self.title = title
        self.url = url
        self.description = description
        self.thumb = thumb
        self.published_date = published_date
        self.duration = duration

    def __str__(self):
        return self.title + ' ' + self.url + ' ' + self.published_date + ' ' + str(self.duration)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'thumb': self.thumb,
            'duration': self.duration
        }
    
    def format_date(self):
        """
        Format the date
        """
        # get date
        date = self.published_date
        # format date
        formatted_date = datetime.strptime(date, '%Y-%m-%d')
        # return formatted date
        return formatted_date.strftime('%d %b %Y')
