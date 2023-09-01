from datetime import datetime
import json
import os
from flask import Flask, render_template, request
from classes.episode import Episode
from utils.database import read_videos, read_video
from utils.images import Images
from setup import update_db, guest_list, load_about_content, load_license_content
## add gzip compression
from flask_compress import Compress

# Flask app
app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
Compress(app)

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
    return render_template(
        'index.html', 
        episodes=episodes, 
        order=reverse if order == 'ASC' else 'ASC'
    )

@app.route('/episode/<episode_id>')
def episode(episode_id):
    e = read_video(episode_id)
    return render_template(
        'episode.html', 
        episode=Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]).to_dict()
    )

@app.route('/guests')
def guests():
    return render_template(
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
    return render_template(
        'guest.html', 
        guest=guest,
        order=reverse if order == 'ASC' else 'ASC'
    )
    
@app.route('/about')
def about():
    return render_template(
        'about.html',
        about=load_about_content()
    )

@app.route('/LICENSE')
def license():
    return render_template(
        'about.html',
        about=load_license_content()
    )

@app.route('/update')
def update():
    update_db()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        'about.html',
        about='<h1>Update complete</h1><p>Database updated at {}</p>'.format(timestamp)
    )

@app.route('/images')
def images():
    # load all images from the images folder
    images = os.listdir(os.path.join(os.path.dirname(__file__), 'static/thumbs'))
    for i, image in enumerate(images):
        # get the relative path to the image
        images[i] = '/thumbs/' + image
    return json.dumps(images)

@app.route('/images/<image_name>')
def image(image_name):
    # load all images from the images folder in base64 format
    images = os.listdir(os.path.join(os.path.dirname(__file__), 'static/thumbs'))
    for image in images:
        if image_name == image.image:
            return image.data
    return None

# Run the app    
if __name__ == '__main__':
    # Run the app
    app.run()