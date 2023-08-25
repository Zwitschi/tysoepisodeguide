import os
import sys
import markdown
from time import sleep
from datetime import datetime
from classes.episode import Episode
from classes.channel import Channel
from classes.guest import Guest
from utils.api import api_call, build_url
from utils.database import read_channel, insert_channel, read_video, insert_video, update_video, read_videos, read_video_ids, install
from utils.parsing import parse_duration, is_episode, get_episode_number
from utils.timing import sleep_with_delay

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')

def load_about_content() -> str:
    """Load ABOUT.md and README.md files and convert markdown to html"""
    with open('ABOUT.md', 'r') as f:
        about = f.read()
    with open('README.md', 'r') as f:
        readme = f.read()
    return markdown.markdown(about) + '\n' + markdown.markdown(readme)

def load_license_content() -> str:
    """Load LICENSE markdown file and return html string"""
    with open('LICENSE', 'r') as f:
        license = f.read()
        return markdown.markdown(license)

def guest_list(order: str = 'ASC') -> list:
    """Create the list of guests for the guests page"""
    # create a list of episodes
    episodes = []

    # get all videos from db
    videos = read_videos()
    
    # add episodes to list
    for e in videos:
        episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]))
    
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

def get_youtube_video_ids() -> list:
    """Get the video ids from the channel via API call"""
    channel_url = build_url('channel')
    res_json = api_call(channel_url)
    items = res_json['items']
    video_ids = [item['id']['videoId'] for item in items]
    next_page_token = res_json['nextPageToken']
    sleep_with_delay(2)
    while next_page_token:
        next_page_url = channel_url + '&pageToken=' + next_page_token
        next_page_res_json = api_call(next_page_url)
        next_page_items = next_page_res_json['items']
        next_page_video_ids = [item['id']['videoId'] for item in next_page_items]
        video_ids.extend(next_page_video_ids)
        # check if another page exists
        if 'nextPageToken' not in next_page_res_json:
            break
        else:
            next_page_token = next_page_res_json['nextPageToken']
            sleep_with_delay(2)
    return video_ids

def get_youtube_video(video_id: str) -> dict:
    """Get video and its details from the YouTube API"""
    video_url = build_url('video_detail', video_id)
    res_json = api_call(video_url)
    return {
        'id': video_id,
        'title': res_json['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/watch?v=' + video_id,
        'description': res_json['items'][0]['snippet']['description'],
        'thumb': res_json['items'][0]['snippet']['thumbnails']['high']['url'],
        'published_date': res_json['items'][0]['snippet']['publishedAt'],
        'duration': parse_duration(res_json['items'][0]['contentDetails']['duration']),
        'number': 0
    }    

def get_video_duration(video_id: str) -> dict:
    """Get the video duration from the video id"""
    # Create a video duration dictionary
    video_duration = {}
    # Get the video url from the video id
    video_url = build_url('details', video_id)
    # read page info
    pagedata = api_call(video_url)
    # check if there are any results, if not, abort
    if len(pagedata['items']) == 0:
        print('Error: no video found for id ' + video_id)
        return
    # get the video duration
    video_duration['duration'] = pagedata['items'][0]['contentDetails']['duration']
    return video_duration

def get_episode_yt(video_id: str) -> dict:
    """Get the details of the episode from the Youtube API via video id"""
    # Get the video url from the video id
    video_url = build_url('video', video_id)
    # read page info
    res = api_call(video_url)
    # check if there are any results, if not, abort
    if len(res['items']) == 0:
        print('Error: no video found for id ' + video_id)
        return {}
    # Check if video is an episode
    if not is_episode(
        res['items'][0]['snippet']['title'], 
        parse_duration(res['items'][0]['contentDetails']['duration']['duration'])
    ):
        return {}
    # Create a video detail dictionary
    episode = {
        'id' : video_id,
        'title' : res['items'][0]['snippet']['title'],
        'url' : 'https://www.youtube.com/watch?v=' + video_id,
        'description' : res['items'][0]['snippet']['description'],
        'thumb' : res['items'][0]['snippet']['thumbnails']['high']['url'],
        'published_date' : res['items'][0]['snippet']['publishedAt'],
        'duration' : parse_duration(res['items'][0]['contentDetails']['duration']['duration']),
        'number' : get_episode_number(res['items'][0]['snippet']['title'])
    }
    # Return the video detail
    return episode

def check_video_id(video_id: str) -> bool:
    """
    Check if the video id is already in database.

    If video id is not in database, get the video details from youtube API and save.
    If video id is in database, check if video details are saved in database.
    If only video id is present, get the video details from youtube API and update database.
    """
    video = read_video(video_id)
    if video:
        # check if video details have been saved yet
        if video[1] == None:
            # get video info
            video = get_youtube_video(video_id)
            update_video(video)
            sleep(2)
        return True
    else:
        # get video info
        video = get_youtube_video(video_id)
        insert_video(video)
        print('New video: ' + video['title'])
        sleep(2)
        return False

def get_video_ids(force_update:bool=False) -> list:
    """
    Get the video ids from the channel.
    If channel was updated in the last 24 hours, read video ids from db.
    If not, get video ids from youtube API and save in db.
    """
    # create channel object
    c = Channel('UCYCGsNTvYxfkPkfQopRMP7w')
    # check if channel was updated in the last 24 hours
    if c.check_channel_update_db() == False or force_update == True:
        # channel was not updated in the last 24 hours, get videos from youtube API
        print('Getting videos from YouTube API')
        video_ids = get_youtube_video_ids()
        if video_ids == None:
            print('No videos found')
            return
        for video_id in video_ids:
            # check if video is already in db
            check_video_id(video_id)
        # update channel last updated
        c.set_last_updated(datetime.now().timestamp())
        c.update_channel_db()
    else:
        # channel was updated in the last 24 hours, get videos from db
        print('Getting videos from database')
        video_ids = read_video_ids()
        if video_ids == None:
            print('No videos found')
            return
        # check if video details are saved in db
        for video_id in video_ids:
            check_video_id(video_id)
    return video_ids

def get_channel_details(channel_id: str) -> dict:
    """Query the YouTube API for the channel details"""
    channel_url = build_url('channel_detail', channel_id)
    res_json = api_call(channel_url)
    return {
        'id': channel_id,
        'title': res_json['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/channel/' + channel_id,
        'last_updated': datetime.now().timestamp()
    }

def get_episodes(video_ids: list) -> list:
    """Get the details of the episodes from the video ids."""
    episode_details = []
    for video_id in video_ids:
        # check if video is in db:
        row = read_video(video_id)
        if row is not None:
            # read video detail from db
            video_detail = {'id': row[0], 'title': row[1], 'url': row[2], 'description': row[3], 'thumb': row[4], 'published_date': row[5], 'duration': row[6], 'number': row[7]}
        else:
            # get video detail from youtube API
            print('New video: ' + video_id)
            video_detail = get_episode_yt(video_id)
            if video_detail != {}:
                insert_video(video_detail)
        if video_detail != {}:
            episode_details.append(video_detail)
    return episode_details

def update_db() -> None:
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the video ids from the channel id.
    Get the episode details from the video ids.
    Update the database with the episode details if needed.
    """
    # Check if channel details are up to date
    channel_details = read_channel()

    # If there is no record yet, query youtube API and save details
    if channel_details is None:
        print('New channel details')
        channel_details = get_channel_details('UCYCGsNTvYxfkPkfQopRMP7w')
        insert_channel('UCYCGsNTvYxfkPkfQopRMP7w')
    
    # Get the video ids from the channel id
    video_ids = get_video_ids()

    # print the number of videos found
    print(str(len(video_ids)) + ' videos found')
    
    # Get the episode details from the video ids
    episode_details = get_episodes(video_ids)

    # print the number of episodes found
    print(str(len(episode_details)) + ' episodes found')

    for e in episode_details:
        # create episode object
        ep = Episode(e['id'], e['title'], e['url'], e['description'], e['thumb'], e['published_date'], e['duration'], e['number'])
        # check if episode is in db
        row = read_video(e['id'])
        # if episode is not in db, insert
        if row is None:
            insert_video(e)
        # if episode is in db, check if details are up to date
        else:
            dbep = Episode(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
            # if details are not up to date, update
            if ep.title != dbep.title or ep.url != dbep.url or ep.description != dbep.description or ep.number != dbep.number:
                update_video(e)
                
def main(*args):
    """Main function
    
    Accepts arguments: 'install' or 'update'
    Default is 'update'
    """
    if len(args) == 0:
        update_db()
    elif len(args) == 1:
        if args[0] == 'install':
            install()
        elif args[0] == 'update':
            update_db()
    else:
        print('Usage: python setup.py [install|update]')
        sys.exit(1)

if __name__ == '__main__':
    main(*sys.argv[1:])