from typing import Optional
import os
import sys
import markdown
from datetime import datetime
from classes.episode import Episode
from classes.channel import Channel
from classes.database import Database, Channels, Videos
from classes.thumbnail import Thumbnail
from utils.parsing import parse_duration, is_episode, get_episode_number
from utils.youtube import YouTubeClient, get_client

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')
CHANNEL_ID = 'UCYCGsNTvYxfkPkfQopRMP7w'


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


def get_channel_details(channel_id: str) -> dict:
    """Query the YouTube API for the channel details."""
    yt = get_client()
    request = yt.youtube.channels().list(part='snippet', id=channel_id)
    response = yt.execute_with_quota(request, cost=YouTubeClient.COST_READ)
    snippet = response['items'][0]['snippet']
    return {
        'id': channel_id,
        'title': snippet['title'],
        'url': 'https://www.youtube.com/channel/' + channel_id,
        'last_updated': datetime.now().timestamp()
    }


def _playlist_item_meta(item: dict) -> Optional[dict]:
    """Extract video metadata from a playlistItems response item.

    Returns None for private/deleted entries or entries missing a publish date.
    """
    snippet = item.get('snippet', {})
    video_id = item.get('contentDetails', {}).get('videoId')
    title = snippet.get('title', '')
    published_at = snippet.get('publishedAt')
    if not video_id or not published_at or title in ('Private video', 'Deleted video'):
        return None
    return {'video_id': video_id, 'title': title, 'published_at': published_at}


def _detail_to_episode(detail: dict) -> Optional[dict]:
    """Convert a videos().list() detail item into an episode dict, or None."""
    snippet = detail.get('snippet', {})
    video_id = detail.get('id')
    title = snippet.get('title', '')
    duration = parse_duration(detail.get(
        'contentDetails', {}).get('duration', 'PT0S'))
    if not is_episode(title, duration):
        return None
    return {
        'id': video_id,
        'title': title,
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'description': snippet.get('description', ''),
        'thumb': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
        'published_date': snippet.get('publishedAt', ''),
        'duration': duration,
        'number': get_episode_number(title),
    }


def _download_thumbnail(episode: dict) -> None:
    """Download the thumbnail for an episode if it is not already cached."""
    thumb_url = episode.get('thumb')
    if not thumb_url:
        return
    thumbnail_format = thumb_url.split('.')[-1]
    thumbnail_path = os.path.join(
        BASE_DIR, 'static', 'thumbs', episode['id'] + '.' + thumbnail_format)
    if not os.path.exists(thumbnail_path):
        Thumbnail(thumb_url, thumbnail_path).download()


def fetch_video(video_id: str) -> dict:
    """Fetch full metadata for a single video and download its thumbnail."""
    yt = get_client()
    detail = yt.get_videos_details(
        [video_id], part='snippet,contentDetails').get(video_id)
    if not detail:
        return {}
    episode = _detail_to_episode(detail)
    if episode:
        _download_thumbnail(episode)
        return episode
    snippet = detail.get('snippet', {})
    return {
        'id': video_id,
        'title': snippet.get('title', ''),
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'description': snippet.get('description', ''),
        'thumb': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
        'published_date': snippet.get('publishedAt', ''),
        'duration': parse_duration(detail.get('contentDetails', {}).get('duration', 'PT0S')),
        'number': 0,
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
    if not channel_details:
        channel_details = get_channel_details(channel_id)
        channels_obj.insert(channel_details)
        yield 'Channel details saved to database'


def process_existing_video(video_row):
    """Process a video row from DB and yield progress messages."""
    v = Videos()
    # video_row is the DB row tuple
    if video_row[1] is None:
        video = fetch_video(video_row[0])
        if video:
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


def update_db(force: bool = False):
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the new video items from the channel uploads playlist.
    Batch fetch the episode details and update the database.
    """
    # Make this function a generator yielding progress messages so callers can
    # stream updates to clients.
    yield '[' + get_now_str() + '] Update started'

    # Ensure the channel row exists
    channels = Channels()
    yield from check_and_store_channel_details(channels, CHANNEL_ID)

    channel = Channel(CHANNEL_ID)
    v = Videos()
    known_ids = set(v.read_ids())

    if force or not channel.check_channel_update_db():
        yield 'Getting videos from YouTube API'
        yt = get_client()
        # Incremental: stop at the first already-known video (playlistItems are
        # newest first). Full (force): enumerate the entire uploads playlist.
        items = yt.get_channel_video_items(
            CHANNEL_ID, stop_at_known_ids=None if force else known_ids)

        new_metas = []
        for item in items:
            meta = _playlist_item_meta(item)
            if meta and meta['video_id'] not in known_ids:
                new_metas.append(meta)
        yield f'Found {len(new_metas)} new video(s)'

        # Batch fetch details for all new videos (50 ids per API call)
        new_ids = [m['video_id'] for m in new_metas]
        details = yt.get_videos_details(new_ids, part='snippet,contentDetails')

        for meta in new_metas:
            detail = details.get(meta['video_id'])
            episode = _detail_to_episode(detail) if detail else None
            if episode is None:
                yield f"Not an episode: {meta['title']}"
                continue
            if v.read(episode['id']) is None:
                _download_thumbnail(episode)
                v.insert(episode)
                yield 'Video details saved to database: ' + episode['title']
            msg = handle_episode_detail(episode)
            if msg:
                yield msg

        channel.set_last_updated(datetime.now().timestamp())
        channel.update_channel_db()
        yield 'Channel updated in database'
    else:
        yield 'Channel was updated within the last 24 hours, using local data'

    # Re-verify existing rows locally (fill NULL titles, re-derive numbers)
    for video_id in v.read_ids():
        row = v.read(video_id)
        if row:
            yield from process_existing_video(row)

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
