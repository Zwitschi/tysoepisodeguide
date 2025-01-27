class EpisodeGuests:
    def __init__(self, title, number) -> None:
        self.title = title
        self.number = number
        self.guests = []
        self.get_guests()

    def sleepover_series(self):
        text = 'The Sleepover Series:'
        if text in self.title:
            self.title = self.title.split(text)[0]

    def uncle_bob(self):
        if 'Uncle Bob' in self.title:
            self.title = self.title.replace(
                '(feat. Uncle Bob)', ' + Uncle Bob')

    def clean_by_split(self, spliton):
        if spliton in self.title:
            title_parts = self.title.split(spliton)
            if len(title_parts) > 1:
                self.title = title_parts[0]

    def clean_by_mapping(self):
        title_mappings = {
            'Are You Garbage': 'Kevin James Ryan + Henry Foley',
            'Chad and JT': 'Chad Kroeger + JT Parr',
            'Erik Griffin & The Glassman Family': 'Erik Griffin + Mom + Dad',
            'Erik Griffin 11.0': 'Erik Griffin',
            'Harland Willams': 'Harland Williams',
            'Howie Mandel meets The Family': 'Howie Mandel + Mom + Dad',
            'Jon Dewalt': 'Jon DeWalt',
            'Sarah-Violet & Charles': 'Sarah-Violet Bliss + Charles Rogers',
            'The "AS WEE SEE IT" Episode': 'Sue Ann Pien + Albert Rutecki',
            'Sunday Football w/ The Glassmans': 'Mom + Dad + Uncle Bob + Grandma Gloria',
            'The Glassman Family': 'Mom + Dad',
            'The Vegas Dads 2.0 + Adam Ray': 'Dad + Cousin Teddy + Marc + Adam Ray',
            'The Vegas Dads': 'Dad + Cousin Teddy + Marc',
            'Nobodies': 'Hugh Davidson + Larry Dorf + Rachel Ramras',
            '@whitneycummings': 'Whitney Cummings',
            'Rick Glassman Deciphers Cosmic Wonders (w/ Mathematician)': 'Ashley Christine',
            'Santa Claus 3.0 | Adam Ray': 'Adam Ray',
            'Santa Claus 2.0 | Adam Ray': 'Adam Ray',
            'Sona Movsesian 6.0 [RICK* NEEDS A FRIEND]': 'Sona Movsesian',
        }
        for keyword, replacement in title_mappings.items():
            if keyword in self.title:
                self.title = replacement

    def clean_by_list_replace(self):
        remove_list = [
            f' - #{self.number}',
            f'- #{self.number}',
            f' #{self.number}',
            f' {self.number}',
            f' -#{self.number}',
            f'-#{self.number}',
            f'#{self.number}',
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

        for r in remove_list:
            self.title = self.title.replace(r, '')

    def clean_title(self):
        self.clean_by_mapping()
        self.sleepover_series()
        self.uncle_bob()
        self.clean_by_split('(')
        self.clean_by_split('[')
        self.clean_by_split(' aka')
        self.clean_by_split(' -')

        # Remove trailing spaces
        self.title = self.title.rstrip()

        self.clean_by_list_replace()

        # Remove numbers of appearance (1.0, 2.0, etc)
        for n in range(1, 50):
            self.title = self.title.replace(f'{n}.0', '')

        # Remove extra spaces
        self.title = ' '.join(self.title.split())

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
