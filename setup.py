from typing import Optional
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


def load_content(content) -> str:
    """Load markdown file and convert markdown to html"""
    if content == 'about':
        with open('ABOUT.md', 'r') as f:
            about = f.read()
        with open('README.md', 'r') as f:
            readme = f.read()
        return markdown.markdown(about) + '\n' + markdown.markdown(readme)
    elif content == 'license':
        with open('LICENSE', 'r') as f:
            license = f.read()
        return markdown.markdown(license)
    return ''


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
        next_page_video_ids = [item['id']['videoId']
                               for item in next_page_items]
        video_ids.extend(next_page_video_ids)
        # check if another page exists
        if 'nextPageToken' not in next_page_res_json:
            break
        else:
            api.data['nextPageToken'] = next_page_res_json['nextPageToken']
    return video_ids


def check_thumbnails() -> None:
    # get all videos from db
    v = Videos()
    videos = v.read_videos()
    # check if thumbnail is saved in file system
    for video in videos:
        video_id = video[0]
        thumbnail_format = video[4].split('.')[-1]
        thumbnail_path = os.path.join(
            BASE_DIR, 'static', 'thumbs', video_id + '.' + thumbnail_format)
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
    thumbnail_path = os.path.join(
        BASE_DIR, 'static', 'thumbs', video_id + '.' + thumbnail_format)
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


def get_video_duration(video_id: str) -> Optional[dict]:
    """Get the video duration from the video id"""
    # Create a video duration dictionary
    video_duration = {}
    # Get the video url from the video id
    api = API('details', video_id)
    # read page info
    pagedata = api.data
    # check if there are any results, if not, abort
    if len(pagedata['items']) == 0:
        return None
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
        'id': video_id,
        'title': res['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/watch?v=' + video_id,
        'description': res['items'][0]['snippet']['description'],
        'thumb': res['items'][0]['snippet']['thumbnails']['high']['url'],
        'published_date': res['items'][0]['snippet']['publishedAt'],
        'duration': parse_duration(res['items'][0]['contentDetails']['duration']),
        'number': get_episode_number(res['items'][0]['snippet']['title'])
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


def handle_episode_detail(episode: dict) -> str:
    """Handle the episode detail"""
    msg = ''
    ret_str = ''
    # create episode object
    ep = Episode(episode['id'], episode['title'], episode['url'], episode['description'],
                 episode['thumb'], episode['published_date'], episode['duration'])
    # check if episode is in db
    v = Videos()
    row = v.read(episode['id'])
    # if episode is in db, check if details are up to date
    if row is not None:
        if is_episode(row[1], row[6]):
            # create episode object from db
            dbep = Episode(row[0], row[1], row[2],
                           row[3], row[4], row[5], row[6])
            # if details are not up to date, update
            if ep.title != dbep.title or ep.url != dbep.url or ep.description != dbep.description or ep.number != dbep.number:
                v.update(episode)
                msg = 'Video details updated: ' + episode['title']
                ret_str += msg + '\n'
    return ret_str


def get_now_str() -> str:
    """Get the current date and time as a string"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def check_and_store_channel_details(channels_obj, channel_id):
    """Ensure channel row exists in DB; yield a message if we insert."""
    channel_details = channels_obj.read()
    if channel_details['id'] is None:
        channel_details = get_channel_details(channel_id)
        channels_obj.insert(channel_details)
        yield 'Channel details saved to database'


def get_video_ids(channel_obj, force_flag: bool):
    """Yield progress messages and return the list of video ids.

    Uses `yield` for messages and returns the video_ids via StopIteration value.
    """
    if channel_obj.check_channel_update_db() == False or force_flag == True:
        yield 'Getting videos from YouTube API'
        video_ids = get_youtube_video_ids()
        channel_obj.set_last_updated(datetime.now().timestamp())
        channel_obj.update_channel_db()
        yield 'Videos saved to database'
        return video_ids
    else:
        v = Videos()
        return v.read_ids()


def process_existing_video(video_row):
    """Process a video row from DB and yield progress messages."""
    v = Videos()
    # video_row is the DB row tuple
    if video_row[1] is None:
        video = get_youtube_video(video_row[0])
        v.update(video)
        yield 'Video details updated in database'
    elif video_row[7] == '0' and is_episode(video_row[1], video_row[6]):
        number = get_episode_number(video_row[1])
        v.update_number(video_row[0], number)
    # read video detail from db (fresh)
    video_detail = {
        'id': video_row[0],
        'title': video_row[1],
        'url': video_row[2],
        'description': video_row[3],
        'thumb': video_row[4],
        'published_date': video_row[5],
        'duration': video_row[6],
        'number': video_row[7],
    }
    yield f"Handling episode detail for: {video_detail['title']}"
    msg = handle_episode_detail(video_detail)
    if msg:
        yield msg


def process_new_video(video_id):
    """Handle a video id that's not in DB yet: fetch, maybe insert, and yield messages."""
    v = Videos()
    video = get_youtube_video(video_id)
    yield f"New video: {video['title']}"
    video_detail = get_episode_yt(video_id)
    if video_detail != {}:
        # only insert if not present (protect against races)
        if v.read(video_detail['id']) is None:
            v.insert(video_detail)
            yield 'Video details saved to database'
        msg = handle_episode_detail(video_detail)
        if msg:
            yield msg


def update_db(force: bool = False):
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the video ids from the channel id.
    Get the episode details from the video ids.
    Update the database with the episode details if needed.
    """
    # Make this function a generator yielding progress messages so callers can
    # stream updates to clients.
    msg = '[' + get_now_str() + '] Update started'
    yield msg
    # Helper subgenerators to keep code small and testable

    # perform work using the helpers
    channels = Channels()
    yield from check_and_store_channel_details(channels, 'UCYCGsNTvYxfkPkfQopRMP7w')

    channel = Channel('UCYCGsNTvYxfkPkfQopRMP7w')
    # get video ids (subgenerator returns list)
    video_ids = yield from get_video_ids(channel, force)

    for video_id in video_ids:
        v = Videos()
        row = v.read(video_id)
        if row:
            yield from process_existing_video(row)
        else:
            yield from process_new_video(video_id)

    yield '[' + get_now_str() + '] Update finished'


def update_db_collect(force: bool = False) -> str:
    """Compatibility wrapper for callers that expect a single string return.

    This collects all yielded messages and returns a newline-separated string.
    """
    parts = []
    for m in update_db(force=force):
        parts.append(m)
    return '\n'.join(parts) + '\n'


def action_from_arguments(*args) -> tuple[str, bool]:
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
        print(
            'Usage: python setup.py [install|update [force]|force|thumbnails]')
        sys.exit(1)
    return action, force


def main(*args):
    """
    Main function
    """
    # check command line arguments
    action, force = action_from_arguments(*args)
    db = Database()
    # execute action
    if action == 'install':
        # install database
        db.install()
        # update database (CLI callers expect a collected string)
        update_db_collect(force)
    elif action == 'update':
        # check if database is installed
        if not db.check_install():
            db.install()
        # update database (CLI callers expect a collected string)
        update_db_collect(force)
    elif action == 'thumbnails':
        # check thumbnails
        check_thumbnails()
    else:
        print(
            'Usage: python setup.py [install|update [force]|force|thumbnails]')
        sys.exit(1)
    # exit
    sys.exit(0)


if __name__ == '__main__':
    main(*sys.argv[1:])
