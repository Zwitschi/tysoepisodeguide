import os
import re
import sqlite3
import requests
import markdown
import dotenv
from classes.episode import Episode
from classes.guest import Guest

from time import sleep
from datetime import datetime
from flask import Flask, render_template, url_for

# Constants
API_URL = 'https://www.googleapis.com/youtube/v3/'
STATIC_DIR = 'static/'

BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'db', 'tysodb.db')

# create db folder if not exists
if not os.path.exists(os.path.join(BASE_DIR, 'db')):
    os.makedirs(os.path.join(BASE_DIR, 'db'))

dotenv.load_dotenv()

# load API_KEY from .env
API_KEY = os.getenv('API_KEY')

app = Flask(__name__)

CSS_FILE = 'style.css'
ICON = 'TYSO_icon.png'
LOGO = 'TYSO_logo_1400x1400.jpg'

# Routes
@app.route('/')
def index():
    episodes = []
    for e in read_videos():
        episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]))        
    return render_template(
        'index.html', 
        episodes=episodes, 
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO)
    )

@app.route('/<episode_id>')
def episode(episode_id):
    e = read_video(episode_id)
    return render_template(
        'episode.html', 
        episode=Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]).to_dict(),
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO)
    )

@app.route('/guests')
def guests():
    """ 
    Guests page
    list of dicts with guest names and links to their episodes
    """
    return render_template(
        'guests.html', 
        guests=guest_list(),
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO)
    )

@app.route('/guest/<guest_name>')
def guest(guest_name):
    """ 
    Guest page
    list of dicts with guest names and links to their episodes
    """
    guest = [g for g in guest_list() if g.name == guest_name][0]
    return render_template(
        'guest.html', 
        guest=guest,
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO)
    )

@app.route('/about')
def about():
    """
    About page
    Static page with information about this project
    """
    return render_template(
        'about.html',
        about=load_about_content(),
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO)
    )
    
@app.route('/setup')
def setup_app():
    # try if the db file exists
    if os.path.isfile(DB_FILE):
        return
    # use the init() function to setup the application at first run
    init()
    return


# page functions

def load_about_content():
    """
    Load ABOUT.md and README.md files and convert markdown to html

    Returns:
        str: html string
    """
    html = ""
    with open('ABOUT.md', 'r') as f:
        about = f.read()
        html = markdown.markdown(about)
    
    with open('README.md', 'r') as f:
        readme = f.read()
        html += markdown.markdown(readme)

    return html

def guest_list():
    """ 
    Create the list of guests for the guests page

    Returns:
        list: list of Guest objects
    """
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
        guests.append(g)
    return guests

# database functions

def create_tables():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        last_updated TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id TEXT PRIMARY KEY, 
        title TEXT, 
        url TEXT, 
        description TEXT, 
        thumb TEXT, 
        published_date TEXT, 
        duration INTEGER, 
        number TEXT 
    )
    ''')
    conn.commit()
    conn.close()

def insert_channel(channel):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO channels (id, title, url, last_updated) VALUES (?, ?, ?, ?)', (channel['id'], channel['title'], channel['url'], channel['last_updated']))
    conn.commit()
    conn.close()

def read_channel(channel_id):
    """"
    Read channel from database

    Args:
        channel_id (str): channel id
        
    Returns:
        list: channel details
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
    row = c.fetchone()
    conn.close()
    # transform row into dict
    if row:
        channel = {
            'id': row[0],
            'title': row[1],
            'url': row[2],
            'last_updated': row[3]
        }
        return channel
    else:
        return None

def update_channel(channel):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE channels SET last_updated = ? WHERE id = ?', (channel['last_updated'], channel['id']))
    conn.commit()
    conn.close()

def check_channel_update(channelid):
    """
    Check if the channel was updated in the last 24 hours

    Args:
        channelid (str): channel id

    Returns:
        bool: True if updated in the last 24 hours, False otherwise
    """
    now = datetime.now().timestamp()
    channel = read_channel(channelid)
    if channel:
        last_update = float(channel['last_updated'])
        if now - last_update < 86400:
            return True
        else:
            return False

def insert_video(video):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO videos (id, title, url, description, thumb, published_date, duration, number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (video['id'], video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number']))
    conn.commit()
    conn.close()

def read_video(video_id):
    """
    Read video from database

    Args:
        video_id (str): video id
        
    Returns:
        list: video details
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_video(video):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE videos
        SET title = ?, url = ?, description = ?, thumb = ?, published_date = ?, duration = ?, number = ?
        WHERE id = ?
    ''', (video['title'], video['url'], video['description'], video['thumb'], video['published_date'], video['duration'], video['number'], video['id']))
    conn.commit()
    conn.close()

def delete_video(video_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM videos WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()

def read_video_ids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM videos')
    rows = c.fetchall()
    conn.close()
    return rows

def read_videos():
    """
    Read all episode videos from database

    Returns:
        list: list of videos
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    SELECT * FROM videos 
    WHERE duration > 1600 
    AND title NOT LIKE "%Rick Glassman & Esther Povitsky Have a Time%" 
    AND title NOT LIKE "%Playing some Magic: The Gathering%"
    AND title NOT LIKE "%Magic the Gathering LIVE from Marshall Rug Gallery%"
    and title NOT LIKE "%Take Your Shoes Off - BEST OF %"
    ORDER BY published_date
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

# youtube functions

def api_call(url):
    """
    Make an API call to the YouTube API

    Args:
        url: string, the url to call

    Returns:
        dict: the response from the API
    """
    response = requests.get(url)
    if response.status_code != 200:
        print('Error: ' + str(response.status_code) + ' - ' + response.content.decode('utf-8'))
        return
    res_json = response.json()
    return res_json

def get_channel_details(channel_id):
    """
    Query the YouTube API for the channel details

    Args:
        channel_id: string, the id of the channel
        
    Returns:
        dict: the channel details
    """
    channel_url = API_URL + 'channels?part=snippet,contentDetails&id=' + channel_id + '&key=' + API_KEY
    res_json = api_call(channel_url)
    channel = {
        'id': channel_id,
        'title': res_json['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/channel/' + channel_id,
        'last_updated': datetime.now().timestamp()
    }
    return channel

def get_youtube_video(video_id):
    """
    Get video and its details from the YouTube API

    Args:
        video_id: string, the id of the video

    Returns:
        dict: the video details
    """
    video_url = API_URL + 'videos?part=snippet,contentDetails&id=' + video_id + '&key=' + API_KEY
    res_json = api_call(video_url)
    video = {
        'id': video_id,
        'title': res_json['items'][0]['snippet']['title'],
        'url': 'https://www.youtube.com/watch?v=' + video_id,
        'description': res_json['items'][0]['snippet']['description'],
        'thumb': res_json['items'][0]['snippet']['thumbnails']['high']['url'],
        'published_date': res_json['items'][0]['snippet']['publishedAt'],
        'duration': parse_duration(res_json['items'][0]['contentDetails']['duration']),
        'number': 0
    }
    return video

def get_youtube_video_ids(channelid):
    """
    Get the video ids from the channel via API call

    Args:
        channelid (str): channel id

    Returns:
        list: list of video ids
    """
    channel_url = API_URL + 'search?part=snippet&channelId=' + channelid + '&maxResults=50&order=date&type=video&key=' + API_KEY
    res_json = api_call(channel_url)
    items = res_json['items']
    video_ids = [item['id']['videoId'] for item in items]
    next_page_token = res_json['nextPageToken']
    sleep(2)
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
            sleep(2)
    return video_ids

def check_video_id(video_id):
    """
    Check if the video id is already in database.
    If not, get the video details from youtube API and save in database.
    If it is, check if video details are saved in database.
    If only id is present, get the video details from youtube API and update row in database.
    """
    video = read_video(video_id)
    if video:
        # check if video details have been saved yet
        if video[1] == None:
            # get video info
            video = get_youtube_video(video_id)
            update_video(video)
            print('Video updated in db')
            sleep(2)
    else:
        # get video info
        video = get_youtube_video(video_id)
        insert_video(video)
        print('Video inserted into db: ' + video['title'])

def get_episode_number(video_title):
    """
    Get the episode number from the video title

    Arguments:
        video_title -- the title of the video

    Returns:
        episode_number -- the episode number
    """
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
        # if number contains a '.' then cast as decimal
    
    if episode_number == 0 or episode_number == 50:
        return episode_number
    elif '.' in episode_number:
        episode_number = float(episode_number)
    else:
        episode_number = int(episode_number)
    return episode_number

def get_video_duration(video_id):
    """
    Get the video duration from the video id

    Arguments:
        video_id -- the id of the video

    Returns:
        video_duration -- a dictionary containing the video duration
    """
    # Create a video duration dictionary
    video_duration = {}
    # Get the video url from the video id
    video_url = API_URL + 'videos?part=contentDetails&id=' + video_id + '&key=' + API_KEY
    # read page info
    pagedata = api_call(video_url)
    # check if there are any results, if not, abort
    if len(pagedata['items']) == 0:
        print('Error: no video found')
        return
    # get the video duration
    video_duration['duration'] = pagedata['items'][0]['contentDetails']['duration']
    return video_duration

def parse_duration(duration):
    """
    Get the duration in seconds from the duration string
    Time is formatted as an ISO 8601 string, e.g. PT1H5M30S
    PT stands for Time Duration

    Arguments:
        duration -- the duration string

    Returns:
        duration_seconds -- the duration in seconds
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
    duration_seconds = int(duration_seconds)
    return duration_seconds

def is_episode(episode_title, duration=0):
    """
    Filter video for full episodes of Take Your Shoes Off

    Arguments:
        video_detail {dict} -- video details

    Returns:
        bool -- True if video is a full episode of Take Your Shoes Off
    """
    if duration > 1600 and ('Take Your Shoes Off' in episode_title or 'TYSO' in episode_title):
        return True
    else:
        return False
    
def get_episode_yt(video_id):
    """
    Get the details of the episode from the Youtube API via video id

    Arguments:
        video_id -- the id of the video

    Returns:
        episode -- a dictionary containing the episode details
    """
    # Get the video url from the video id
    video_url = API_URL + 'videos?part=snippet&id=' + video_id + '&key=' + API_KEY
    # read page info
    res = api_call(video_url)
    # check if there are any results, if not, abort
    if len(res['items']) == 0:
        print('Error: no video found')
        return {}
    # Check if video is an episode
    if not is_episode(res['items'][0]['snippet']['title'], parse_duration(res['items'][0]['contentDetails']['duration']['duration'])):
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
    
def get_video_ids(channelid):
    """
    Get the video ids from the channel.
    If channel was updated in the last 24 hours, read video ids from db.
    If not, get video ids from youtube API and save in db.

    Arguments:
        channelid -- the id of the channel
        
    Returns:
        video_ids -- list of video ids
    """
    if check_channel_update(channelid) == True:
        # channel was updated in the last 24 hours, read videos from db
        video_ids = read_video_ids()
    else:
        video_ids = get_youtube_video_ids(channelid)
        
        if video_ids == None:
            print('No videos found')
            return
        
        for video_id in video_ids:
            # check if video is already in db
            check_video_id(video_id)
        # update channel last updated
        channel = {
            'id': channelid,
            'last_updated': datetime.now().timestamp()
        }
        update_channel(channel)
    return video_ids

def check_channel(channelid):
    """
    Check channel details for updates.
    Read channel details and check if new videos are available.
    If new videos are available, update the channel details.
    Return True if channel details were updated, False if not.

    Arguments:
        channelid -- the id of the channel

    Returns:
        bool -- True if channel details were updated, False if not
    """
    # Get the channel details
    channel_details = read_channel(channelid)
    # If there is no record yet, query youtube API and save details
    if channel_details is None:
        channel_details = get_channel_details(channelid)
        insert_channel(channel_details)
        return True
    # Return False if channel details were not updated
    return False
    
def init():
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the video ids from the channel id.
    Get the episode details from the video ids.
    Update the database with the episode details if needed.    
    """
    # create the database tables
    create_tables()

    channelid = 'UCYCGsNTvYxfkPkfQopRMP7w'

    # Check if channel details are up to date
    check_channel(channelid)
    
    # Get the video ids from the channel id
    video_ids = get_video_ids(channelid)
    
    # Get the episode details from the video ids
    episode_details = []
    
    for video_id in video_ids:
        # check if video is in db:
        row = read_video(video_id[0])
        if row is not None:
            # read video detail from db
            video_detail = {'id': row[0], 'title': row[1], 'url': row[2], 'description': row[3], 'thumb': row[4], 'published_date': row[5], 'duration': row[6], 'number': row[7]}
        else:
            video_detail = get_episode_yt(video_id[0])
            if video_detail != {}:
                insert_video(video_detail)
    if video_detail != {}:
        episode_details.append(video_detail)

    for e in episode_details:
        ep = Episode(e['id'], e['title'], e['url'], e['description'], e['thumb'], e['published_date'], e['duration'], e['number'])
        row = read_video(e['id'])
        if row is None:
            insert_video(e)
        else:
            dbep = Episode(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
            if ep.title != dbep.title or ep.url != dbep.url or ep.description != dbep.description:
                update_video(e)
    
if __name__ == '__main__':
    # Initialise the database
    init()
    
    # Run the app
    app.run()