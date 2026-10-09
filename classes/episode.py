import re
from datetime import datetime
from classes.episodeguests import EpisodeGuests
from classes.episodenumber import EpisodeNumber

class Episode:
    def __init__(self, id, title, url, description, thumb, published_date, duration):
        self.id = id
        self.title = title
        self.url = url
        self.description = description
        self.thumb = thumb
        self.published_date = published_date
        self.duration = duration
        self.number = EpisodeNumber(self.title).number
        self.formatted_date = self.format_date()
        self.formatted_description = self.format_description()
        self.guest = EpisodeGuests(self.title, self.number).guests
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'thumb': self.thumb,
            'duration': self.duration,
            'number': self.number,
            'formatted_date': self.formatted_date,
            'formatted_description': self.formatted_description,
            'guest': self.guest
        }
    
    def format_date(self):
        return datetime.strptime(self.published_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
    
    def format_description(self):
        return re.sub(r'(https?://\S+)', r'<a href="\1">\1</a>', self.description).replace('\r\n', '<br />').replace('\n', '<br />')