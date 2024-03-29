from datetime import datetime
import json
import os
from flask import Flask, render_template, request
from classes.database import Videos
from classes.episode import Episode
from classes.guestlist import Guestlist
from setup import update_db, load_content
## add gzip compression
from flask_compress import Compress

# Flask app
app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
Compress(app)

## helper function for sort order
def sort_order(request):
    # initialize sort order with empty string
    order = ''
    # get sort order from request args if present
    if 'sort' in request.args:
        order = request.args.get('sort', order, type = str)
    # only allow ASC or DESC
    if order not in ['ASC', 'DESC']:
        order = 'ASC'
    reverse = 'DESC'
    order = reverse if order == 'DESC' else 'ASC'
    return order

# Routes
@app.route('/')
def index():
    order = sort_order(request)
    # create empty list for episodes
    episodes = []
    # get episodes from database
    v = Videos()
    for e in v.read_videos(order=order):
        # create Episode object from database record and append to episodes list
        episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6]))
    # render the template
    return render_template(
        'index.html', 
        episodes=episodes, 
        order=order
    )

@app.route('/episode/<episode_id>')
def episode(episode_id):
    v = Videos()
    video_id = episode_id
    e = v.read(video_id=video_id)
    return render_template(
        'episode.html', 
        episode=Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6]).to_dict()
    )

@app.route('/guests')
def guests():
    order = sort_order(request)
    return render_template(
        'guests.html', 
        guests=Guestlist(order).guests
    )

@app.route('/guest/<guest_name>')
def guest(guest_name):
    order = sort_order(request)
    guest = [g for g in Guestlist(order=order).guests if g.name == guest_name][0]
    return render_template(
        'guest.html', 
        guest=guest,
        order=order
    )
    
@app.route('/about')
def about():
    return render_template(
        'about.html',
        about=load_content('about')
    )

@app.route('/LICENSE')
def license():
    return render_template(
        'about.html',
        about=load_content('license')
    )

@app.route('/update')
def update():
    ret_str = update_db()
    update = '<h1>Update complete</h1>'
    for line in ret_str.split('\n'):
        update += '<pre>' + line + '</pre>\n'
    return render_template(
        'about.html',
        content=update
    )

# routes for images
@app.route('/images')
def images():
    # load all images from the images folder
    images = os.listdir(os.path.join(os.path.dirname(__file__), 'static/thumbs'))
    for i, image in enumerate(images):
        # get the relative path to the image
        images[i] = '/thumbs/' + image
    return json.dumps(images)

# Run the app    
if __name__ == '__main__':
    # Run the app
    app.run()