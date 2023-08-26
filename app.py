from datetime import datetime
from flask import Flask, render_template, url_for, request
from classes.episode import Episode
from utils.database import read_videos, read_video
from setup import update_db, guest_list, load_about_content, load_license_content

# static file constants
CSS_FILE = 'style.css'
ICON = 'TYSO_icon.png'
LOGO = 'TYSO_logo_1400x1400.jpg'

# Flask app
app = Flask(__name__)

# Functions
def override_render_template(template, **kwargs):
    "Override the render_template function to add the css_file parameter"
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
    return override_render_template(
        'guests.html', 
        guests=guest_list()
    )

@app.route('/guest/<guest_name>')
def guest(guest_name):
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
    return override_render_template(
        'about.html',
        about=load_about_content()
    )

@app.route('/LICENSE')
def license():
    return override_render_template(
        'about.html',
        about=load_license_content()
    )

@app.route('/update')
def update():
    update_db()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return override_render_template(
        'about.html',
        about='<h1>Update complete</h1><p>Database updated at {}</p>'.format(timestamp)
    )

# special route for favicon.ico in /static
@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='favicon.ico')
    
if __name__ == '__main__':
    # Run the app
    app.run()