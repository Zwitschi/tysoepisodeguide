class EpisodeGuests:
    def __init__(self, title, number) -> None:
        self.title = title
        self.number = number
        self.guests = []
        self.get_guests()

    def clean_title(self):
        """
        Clean the title from known information
        """
        if 'Uncle Bob' in self.title:
            self.title = 'Uncle Bob + ' + self.title
        if 'Are You Garbage' in self.title:
            self.title = 'Kevin James Ryan + Henry Foley'
        if 'Chad and JT' in self.title:
            self.title = 'Chad Kroeger + JT Parr'
        if 'Howie Mandel meets The Family' in self.title:
            self.title = 'Howie Mandel + Mom + Dad'
        if 'Sarah-Violet & Charles' in self.title:
            self.title = 'Sarah-Violet Bliss + Charles Rogers'
        if 'The "AS WEE SEE IT" Episode' in self.title:
            self.title = 'Sue Ann Pien + Albert Rutecki'
        if 'Sunday Football w/ The Glassmans' in self.title:
            self.title = 'Mom + Dad + Uncle Bob + Grandma Gloria'
        if 'The Glassman Family' in self.title:
            self.title = self.title.replace('The Glassman Family', 'Mom + Dad')
        if 'The Vegas Dads 2.0 + Adam Ray' in self.title:
            self.title = 'Dad + Cousin Teddy + Marc + Adam Ray'
        if 'The Vegas Dads' in self.title:
            self.title = 'Dad + Cousin Teddy + Marc'
        if 'JON DEWALT' in self.title.upper():
            self.title = 'Jon DeWalt'
        if 'Nobodies' in self.title:
            self.title = 'Hugh Davidson + Larry Dorf + Rachel Ramras'
        if '@whitneycummings' in self.title:
            self.title = 'Whitney Cummings'
        if ' - The Sleepover Series:' in self.title:
            self.title = self.title.split(' - The Sleepover Series:')[0]
        if '(' in self.title:
            self.title = self.title.split('(')[0]
        if ' aka' in self.title:
            self.title = self.title.split(' aka')[0]
        # remove trailing spaces
        while self.title.endswith(' '):
            self.title = self.title[:-1]

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
            if r in self.title:
                self.title = self.title.replace(r, '')
        
        for n in range(1,50):
            if str(n)+'.0' in self.title:
                self.title = self.title.replace(str(n)+'.0', '')
                
        # remove extra spaces
        while '  ' in self.title:
            self.title = self.title.replace('  ', ' ')
            
        and_list = [' & ', ' and ', ' AND ']
        for a in and_list:
            self.title = self.title.replace(a, ' + ')
    
    def get_guests(self):
        # create a list of guests
        self.clean_title()
        # split title on each character in spliton
        if ' + ' in self.title:
            # split title on spliton character
            guest_split = self.title.split(' + ')
            # check if any other spliton is in any element of guest_split
            for g in guest_split:
                self.guests.append(g.strip())
        # if no + or & in title, add title to guests list
        if len(self.guests) == 0:
            self.guests.append(self.title.strip())