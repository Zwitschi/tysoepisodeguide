import os
from datetime import datetime
from flask import Flask, render_template, url_for, request
from classes.episode import Episode
from utils.database import read_videos, read_video, update_db
from setup import guest_list, load_about_content, load_license_content

API_KEY = os.getenv('API_KEY')
API_URL = 'https://www.googleapis.com/youtube/v3/'
BASE_DIR = os.getcwd()
CSS_FILE = 'style.css'
ICON = 'TYSO_icon.png'
LOGO = 'TYSO_logo_1400x1400.jpg'

app = Flask(__name__)

# Functions
def override_render_template(template, **kwargs):
    """
    Override the render_template function to add the css_file parameter
    """
    return render_template(
        template, 
        css_file=url_for('static', filename=CSS_FILE), 
        icon=url_for('static', filename=ICON),
        logo=url_for('static', filename=LOGO),
        **kwargs
        )

# Routes
@app.route('/')
def index():
    order = 'ASC'
    reverse = 'DESC'
    # get sort order from request args (if present)
    if 'sort' in request.args:
        order = request.args.get('sort', order, type = str)
    # only allow ASC or DESC
    if order not in ['ASC', 'DESC']:
        order = 'ASC'
    # create empty list for episodes
    episodes = []
    # get episodes from database
    for e in read_videos(order=order):
        # create Episode object from database record and append to episodes list
        episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]))
    # render the template
    return override_render_template(
        'index.html', 
        episodes=episodes, 
        order=reverse if order == 'ASC' else 'ASC'
    )

@app.route('/<episode_id>')
def episode(episode_id):
    e = read_video(episode_id)
    return override_render_template(
        'episode.html', 
        episode=Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]).to_dict()
    )

@app.route('/guests')
def guests():
    """ 
    Guests page

    list of dicts with guest names and links to their episodes
    """
    return override_render_template(
        'guests.html', 
        guests=guest_list()
    )

@app.route('/guest/<guest_name>')
def guest(guest_name):
    """ 
    Guest page

    list of dicts with guest names and links to their episodes
    """
    order = 'ASC'
    reverse = 'DESC'
    # get sort order from request args (if present)
    if 'sort' in request.args:
        order = request.args.get('sort', order, type = str)
    guest = [g for g in guest_list(order=order) if g.name == guest_name][0]
    return override_render_template(
        'guest.html', 
        guest=guest,
        order=reverse if order == 'ASC' else 'ASC'
    )

@app.route('/about')
def about():
    """
    About page

    Static page with information about this project
    """
    return override_render_template(
        'about.html',
        about=load_about_content()
    )

@app.route('/update')
def update():
    """
    Update database
    
    Checks channel and if necessary youtube API to update database
    """
    update_db()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return override_render_template(
        'about.html',
        about='Database updated at {}'.format(timestamp)
    )

@app.route('/LICENSE')
def license():
    """
    License page
    
    Static page with license information
    """
    return override_render_template(
        'about.html',
        about=load_license_content()
    )

# special route for favicon.ico in /static
@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='favicon.ico')
    
if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)