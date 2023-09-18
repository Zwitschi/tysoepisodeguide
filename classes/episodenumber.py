import re

class EpisodeNumber:
    def __init__(self, title):
        self.number = 0
        self.title = title
        self.get_episode_number()
        
    def get_episode_number(self):
        """
        Get the episode number from the video title

        Arguments:
            self: the episode object
        
        Returns:
            int: the episode number
        """
        # exceptions
        exceptions = [
            'best of',
            'patreon unlocked',
            'replenish',
            'shorts'
        ]
        if '#' not in self.title and 'Balcony Series' in self.title:
            # try to get the episode number from the title with regex, only consider numbers and . 
            self.number = re.findall(r'[\d\.]+', self.title)
            if len(self.number) > 0:
                self.number = self.number[0]
        elif '#' not in self.title and '50th' in self.title:
            self.number = 50
        elif any(x in self.title.lower() for x in exceptions):
            self.number = 0
        elif '#' not in self.title:
            self.number = 0
        else:
            # Get the episode number from title, split at '#' character to find the episode number
            self.number = self.title.split('#')[1]
            # additional checks on episode number, remove ')', '!' and replace ' pt ' with '.'
            self.number = self.number.replace(')','')
            self.number = self.number.replace('!','')
            self.number = self.number.replace(' pt ','.')    
            # shorten
            self.number = self.number.split(' ')[0]
            
        if self.number == 0 or self.number == 50:
            return
        elif '.' in self.number:
            # if number contains a '.' then cast as float
            self.number = float(self.number)
        else:
            self.number = int(self.number)