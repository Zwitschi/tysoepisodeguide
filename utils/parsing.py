import re

def parse_duration(duration: str) -> int:
    """
    Get the duration in seconds from the duration string
    Time is formatted as an ISO 8601 string, e.g. PT1H5M30S
    PT stands for Time Duration
    """
    # Create a duration seconds variable
    duration_seconds = 0
    duration = duration.replace('PT','')
    duration_hours = 0
    duration_minutes = 0
    duration_seconds = 0
    if 'H' in duration:
        duration_hours = int(duration.split('H')[0])
        duration = duration.split('H')[1]
    if 'M' in duration:
        duration_minutes = int(duration.split('M')[0])
        duration = duration.split('M')[1]
    if 'S' in duration:
        duration_seconds = int(duration.split('S')[0])
    duration_seconds = duration_hours * 3600 + duration_minutes * 60 + duration_seconds
    # check if is integer
    if duration_seconds != int(duration_seconds):
        print('Error: duration is not an integer')
        return
    # check if duration is greater than 0
    if duration_seconds < 0:
        print('Error: duration is less than 0')
        return
    # Return the duration in seconds
    return int(duration_seconds)

def is_episode(episode_title: str, duration: int):
    """Filter video for full episodes of Take Your Shoes Off"""
    if duration > 1600 and ('Take Your Shoes Off' in episode_title or 'TYSO' in episode_title):
        return True
    else:
        return False

def get_episode_number(video_title: str) -> int:
    """Get the episode number from the video title"""
    # Create an episode number variable
    episode_number = 0
    # exceptions
    if not '#' in video_title and 'Balcony Series' in video_title:
        # try to get the episode number from the title with regex, only consider numbers and . 
        episode_number = re.findall(r'[\d\.]+', video_title)
        if len(episode_number) > 0:
            episode_number = episode_number[0]
    elif '#' not in video_title and '50th' in video_title:
        episode_number = 50
    elif 'BEST OF' in video_title or 'PATREON UNLOCKED' in video_title:
        return 0
    else:
        # Get the episode number from title, split at '#' character to find the episode number
        episode_number = video_title.split('#')[1]
        # additional checks on episode number, remove ')', '!' and replace ' pt ' with '.'
        episode_number = episode_number.replace(')','')
        episode_number = episode_number.replace('!','')
        episode_number = episode_number.replace(' pt ','.')    
        # shorten
        episode_number = episode_number.split(' ')[0]
    if episode_number == 0 or episode_number == 50:
        return episode_number
    elif '.' in episode_number:
        # if number contains a '.' then cast as float
        episode_number = float(episode_number)
    else:
        episode_number = int(episode_number)
    return episode_number