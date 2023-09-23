import os
import sys
import markdown
from datetime import datetime
from classes.episode import Episode
from classes.channel import Channel
from classes.database import Database, Channels, Videos
from classes.thumbnail import Thumbnail
from utils.api import API
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

def get_youtube_video_ids() -> list:
    """Get the video ids from the channel via API call"""
    api = API('videos')
    items = api.data['items']
    video_ids = []
    for item in items:
        video_id = item['id']['videoId']
        if video_id not in video_ids:
            video_ids.append(video_id)

    while api.data['nextPageToken']:
        newapi = API('videos_next', next_page=api.data['nextPageToken'])
        next_page_res_json = newapi.data
        next_page_items = next_page_res_json['items']
        next_page_video_ids = [item['id']['videoId'] for item in next_page_items]
        video_ids.extend(next_page_video_ids)
        # check if another page exists
        if 'nextPageToken' not in next_page_res_json:
            break
        else:
            api.data['nextPageToken'] = next_page_res_json['nextPageToken']
    return video_ids

def check_thumbnails() -> None:
    # get all videos from db
    videos = Videos.read()
    # check if thumbnail is saved in file system
    for video in videos:
        video_id = video[0]
        thumbnail_format = video[4].split('.')[-1]
        thumbnail_path = os.path.join(BASE_DIR, 'static', 'thumbs', video_id + '.' + thumbnail_format)
        if not os.path.exists(thumbnail_path):
            t = Thumbnail(video[4], thumbnail_path)
            t.download()
            t.resize()
        else:
            t = Thumbnail(video[4], thumbnail_path)
            t.resize()

def get_youtube_video(video_id: str) -> dict:
    """Get video and its details from the YouTube API"""
    api = API('video_detail', video_id)
    res_json = api.data
    thumbnail = res_json['items'][0]['snippet']['thumbnails']['high']['url']
    thumbnail_format = thumbnail.split('.')[-1]
    thumbnail_path = os.path.join(BASE_DIR, 'static', 'thumbs', video_id + '.' + thumbnail_format)
    Thumbnail(thumbnail, thumbnail_path).download()
    sleep_with_delay(1)
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
    api = API('details', video_id)
    # read page info
    pagedata = api.data
    # check if there are any results, if not, abort
    if len(pagedata['items']) == 0:
        return
    # get the video duration
    video_duration['duration'] = pagedata['items'][0]['contentDetails']['duration']
    return video_duration

def get_episode_yt(video_id: str) -> dict:
    """Get the details of the episode from the Youtube API via video id"""
    # Get the video url from the video id
    api = API('video_detail', video_id)
    # read page info
    res = api.data
    # check if there are any results, if not, abort
    if len(res['items']) == 0:
        return {}
    # Check if video is an episode
    if not is_episode(
        res['items'][0]['snippet']['title'], 
        parse_duration(res['items'][0]['contentDetails']['duration'])
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
        'duration' : parse_duration(res['items'][0]['contentDetails']['duration']),
        'number' : get_episode_number(res['items'][0]['snippet']['title'])
    }
    # Return the video detail
    return episode

def get_channel_details(channel_id: str) -> dict:
    """Query the YouTube API for the channel details"""
    api = API('channel')
    res_json = api.data
    return {
        'id': channel_id,
        'title': res_json['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/channel/' + channel_id,
        'last_updated': datetime.now().timestamp()
    }

def check_video_id(video_id: str) -> bool:
    """
    Check if the video id is already in database.

    If video id is not in database, get the video details from youtube API and save.
    If video id is in database, check if video details are saved in database.
    If only video id is present, get the video details from youtube API and update database.
    """
    video = Videos.read(video_id)
    if video:
        # check if video details have been saved yet
        if video[1] == None:
            # get video info
            video = get_youtube_video(video_id)
            Videos.update(video)
        elif video[7] == '0' and is_episode(video[1], video[6]):
            # get episode number from title
            number = get_episode_number(video[1])
            # update episode number
            Videos.update_number(video_id, number)
        return True
    else:
        # get video info
        video = get_youtube_video(video_id)
        Videos.insert(video)
        print('New video: ' + video['title'])
        return False

def handle_episode_detail(episode: dict) -> None:
    """Handle the episode detail"""
    # create episode object
    ep = Episode(episode['id'], episode['title'], episode['url'], episode['description'], episode['thumb'], episode['published_date'], episode['duration'])
    # check if episode is in db
    row = Videos.read(episode['id'])
    # if episode is in db, check if details are up to date
    if row is not None:
        if is_episode(row[1], row[6]):
            # create episode object from db
            dbep = Episode(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            # if details are not up to date, update
            if ep.title != dbep.title or ep.url != dbep.url or ep.description != dbep.description or ep.number != dbep.number:
                Videos.update(episode)

def update_db(force: bool = False) -> None:
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the video ids from the channel id.
    Get the episode details from the video ids.
    Update the database with the episode details if needed.
    """
    # Check if channel details are up to date
    channel_details = Channels.read()

    # If there is no record yet, query youtube API and save details
    if channel_details is None:
        channel_details = get_channel_details('UCYCGsNTvYxfkPkfQopRMP7w')
        Channels.insert(channel_details)
   
    # create channel object
    c = Channel('UCYCGsNTvYxfkPkfQopRMP7w')
    
    # check if channel was updated in the last 24 hours
    if c.check_channel_update_db() == False or force == True:
        # channel was not updated in the last 24 hours, get videos from youtube API
        print('Getting videos from YouTube API')
        video_ids = get_youtube_video_ids()
        # update channel last updated
        c.set_last_updated(datetime.now().timestamp())
        c.update_channel_db()
    else:
        # channel was updated in the last 24 hours, get videos from db
        print('Getting videos from database')
        video_ids = Videos.read_ids()
    
    # Get the episode details from the video ids
    for video_id in video_ids:
        # check if video is in db:
        video = Videos.read(video_id)
        
        if video:
            # check if video details have been saved yet
            if video[1] == None:
                # get video info
                video = get_youtube_video(video_id)
                Videos.update(video)
            elif video[7] == '0' and is_episode(video[1], video[6]):
                # get episode number from title
                number = get_episode_number(video[1])
                # update episode number
                Videos.update_number(video_id, number)
            # read video detail from db
            video_detail = {'id': video[0], 'title': video[1], 'url': video[2], 'description': video[3], 'thumb': video[4], 'published_date': video[5], 'duration': video[6], 'number': video[7]}
            handle_episode_detail(video_detail)
            
        else:
            # get video info
            video = get_youtube_video(video_id)
            print('New video: ' + video['title'])
            # get video detail from youtube API
            video_detail = get_episode_yt(video_id)
            if video_detail != {}:
                Videos.insert(video_detail)
                handle_episode_detail(video_detail)
                
def action_from_arguments(*args) -> None:
    """
    Check the command line arguments and execute the appropriate function
    
    Accepts arguments: install, update, force, thumbnails
    Default is 'update'
    """
    action = 'update'
    force = False
    if len(args) == 0:
        action = 'update'
    elif len(args) == 1:
        if args[0] == 'install':
            action = 'install'
        elif args[0] == 'update':
            action = 'update'
        elif args[0] == 'force':
            action = 'update'
            force = True
        elif args[0] == 'thumbnails':
            action = 'thumbnails'
    elif len(args) == 2:
        if args[0] == 'update' and args[1] == 'force':
            action = 'update'
            force = True
    else:
        print('Usage: python setup.py [install|update [force]|force|thumbnails]')
        sys.exit(1)
    return action, force
                
def main(*args):
    """
    Main function
    """
    # check command line arguments
    action, force = action_from_arguments(*args)
    # execute action
    if action == 'install':
        # install database
        Database.install()
        # update database
        update_db(force)
    elif action == 'update':
        # check if database is installed
        if not Database.check_install():
            Database.install()
        # update database
        update_db(force)
    elif action == 'thumbnails':
        # check thumbnails
        check_thumbnails()
    else:
        print('Usage: python setup.py [install|update [force]|force|thumbnails]')
        sys.exit(1)
    # exit
    sys.exit(0)

if __name__ == '__main__':
    main(*sys.argv[1:])