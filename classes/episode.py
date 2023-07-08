"""
Episode class

This class is used to create an episode object. It has the following attributes:
    - id: string
    - title: string
    - url: string
    - description: string
    - thumb: string
    - published_date: string
    - duration: int
    - number: int
    - formatted_date: string
    - formatted_description: string
    - guest: list of strings
"""
import re
from datetime import datetime

class Episode:
    def __init__(self, id, title, url, description, thumb, published_date, duration, number):
        self.id = id
        self.title = title
        self.url = url
        self.description = description
        self.thumb = thumb
        self.published_date = published_date
        self.duration = duration
        self.number = number
        self.formatted_date = self.format_date()
        self.formatted_description = self.format_description()
        self.guest = self.get_guest()

    def __str__(self):
        return str(self.number) + ' ' + self.title + ' ' + self.url + ' ' + self.published_date + ' ' + str(self.duration)
    
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
    
    def clean_title(self):
        """
        Clean the title from known information
        """
        # get title
        title = self.title

        if 'Uncle Bob' in title:
            title = 'Uncle Bob + ' + title
        if 'Are You Garbage' in title:
            title = 'Kevin James Ryan + Henry Foley'
        if 'Chad and JT' in title:
            title = 'Chad Kroeger + JT Parr'
        if 'Howie Mandel meets The Family' in title:
            title = 'Howie Mandel + Mom + Dad'
        if 'Sarah-Violet & Charles' in title:
            title = 'Sarah-Violet Bliss + Charles Rogers'
        if 'The "AS WEE SEE IT" Episode' in title:
            title = 'Sue Ann Pien + Albert Rutecki'
        if 'Sunday Football w/ The Glassmans' in title:
            title = 'Mom + Dad + Uncle Bob + Grandma Gloria'
        if 'The Glassman Family' in title:
            title = title.replace('The Glassman Family', 'Mom + Dad')
        if 'The Vegas Dads 2.0 + Adam Ray' in title:
            title = 'Dad + Cousin Teddy + Marc + Adam Ray'
        if 'The Vegas Dads' in title:
            title = 'Dad + Cousin Teddy + Marc'
        if 'JON DEWALT' in title.upper():
            title = 'Jon DeWalt'
        if 'Nobodies' in title:
            title = 'Hugh Davidson + Larry Dorf + Rachel Ramras'

        if ' - The Sleepover Series:' in title:
            title = title.split(' - The Sleepover Series:')[0]
        if '(' in title:
            title = title.split('(')[0]
        while title.endswith(' '):
            title = title[:-1]

        # list of known text to remove from title
        remove_list = [
            ' - #'+str(self.number),
            '- #'+str(self.number),
            ' #'+str(self.number),
            ' '+str(self.number),
            ' -#'+str(self.number),
            '-#'+str(self.number),
            '#'+str(self.number),
            str(self.number),
            ' UNCENSORED',
            'on TYSO w/ Rick Glassman - ',
            'on TYSO - ',
            'on TYSO -',
            'on TYSO',
            'on Take Your Shoes Off',
            'on TYSO w/ Rick Glassman',
            'w/ Rick Glassman - ',
            'w/ Rick Glassman',
            ' w/ The Glassmans - ',
            ' w/ The Glassmans -',
            '50th EPISODE!!',
            '- on TYSO -',
            '- on TYSO',
            ' in NY'
        ]
        
        # remove text from title
        for r in remove_list:
            if r in title:
                title = title.replace(r, '')
        n=1
        while n<99:
            title = title.replace(str(n)+'.0', '')
            n+=1

        # remove extra spaces
        while '  ' in title:
            title = title.replace('  ', ' ')

        return title
    
    def get_guest(self):
        # create a list of guests
        guests = []

        title = self.clean_title()
        title = title.replace(' & ', ' + ')
        title = title.replace(' and ', ' + ')
        title = title.replace(' AND ', ' + ')
        # split title on each character in spliton
        if ' + ' in title:
            # split title on spliton character
            guest_split = title.split(' + ')
            # check if any other spliton is in any element of guest_split
            for g in guest_split:
                guests.append(g.strip())

        # if no + or & in title, add title to guests list
        if len(guests) == 0:
            guests.append(title.strip())
        
        return guests

    def format_description(self):
        return re.sub(r'(https?://\S+)', r'<a href="\1">\1</a>', self.description).replace('\r\n', '<br />').replace('\n', '<br />')
    
    def format_date(self):
        return datetime.strptime(self.published_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
    