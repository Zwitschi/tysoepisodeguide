from classes.database import Videos
from classes.episode import Episode
from classes.guest import Guest

class Guestlist:
    def __init__(self, order) -> None:
        self.order = order
        self.guests = self.guest_list()
    
    def guest_list(order: str = 'ASC') -> list:
        """Create the list of guests for the guests page"""
        # create a list of episodes
        episodes = []

        # get all videos from db
        videos = Videos.read_videos()
        
        # add episodes to list
        for e in videos:
            episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6]))
        
        # create a list of unique guest names
        guest_names = []

        # find all guests in all episodes
        for e in episodes:
            # get the episode guest(s)
            ep_guest = e.guest
            # if more than one guest, split guests into list
            if len(ep_guest) > 1:
                for gn in ep_guest:
                    gn = gn.strip()
                    if gn not in guest_names:
                        guest_names.append(gn)
            else:
                gn = ep_guest[0].strip()
                if gn not in guest_names:
                    guest_names.append(gn)

        # sort guests by name
        guest_names.sort(key=lambda x: x)

        # create a list of guests
        guests = []

        # add episodes to guests
        for gn in guest_names:
            g = Guest(gn)
            g.episodes = [e for e in episodes if gn in e.guest]
            # if sort order is 'DESC', reverse episode list
            if order == 'DESC':
                g.episodes.reverse()
            guests.append(g)
        return guests