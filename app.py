from datetime import datetime
import json
import os
from flask import Flask, render_template, request
from classes.database import Videos
from classes.episode import Episode
from classes.guestlist import Guestlist
from setup import update_db, load_content

# add gzip compression
from flask_compress import Compress

# add site map
from flask_sitemapper import Sitemapper

# init Flask app
app = Flask(__name__, static_url_path='',
            static_folder='static', template_folder='templates')

# enable gzip compression
Compress(app)

# create sitemapper object
sitemapper = Sitemapper()

# add sitemap routes
sitemapper.init_app(app)

# Helper functions
# helper function for sort order


def sort_order(request):
    # initialize sort order with empty string
    order = ''
    # get sort order from request args if present
    if 'sort' in request.args:
        order = request.args.get('sort', order, type=str)
    # only allow ASC or DESC
    if order not in ['ASC', 'DESC']:
        order = 'ASC'
    reverse = 'DESC'
    order = reverse if order == 'DESC' else 'ASC'
    return order

# helper function for database last modified date


def db_last_modified():
    # get the last modified date of the database
    last_modified = os.path.getmtime('db/tysodb.db')
    # convert the last modified date to a datetime object
    last_modified = datetime.fromtimestamp(last_modified)
    return last_modified.strftime('%Y-%m-%d')

# Functions


def get_videos(order='ASC'):
    # get episodes from database
    v = Videos()
    # create empty list for episodes
    episodes = []
    for e in v.read_videos(order=order):
        # create Episode object from database record and append to episodes list
        episodes.append(Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6]))
    return episodes


def get_episode_list():
    v = Videos()
    episode_list = []
    for e in v.read_videos():
        episode_list.append(e[0])
    return episode_list


def get_episode(episode_id):
    v = Videos()
    e = v.read(video_id=episode_id)
    return Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6])


def get_guest_list():
    guest_list = []
    # get Guestlist object
    g = Guestlist(order='ASC')
    # get list of guests
    for guest in g.guests:
        guest_list.append(guest.name)
    return guest_list


# Global variables
DB_LAST_MODIFIED = db_last_modified()


# Routes

@sitemapper.include(lastmod=DB_LAST_MODIFIED, changefreq='weekly', priority=0.8)
@app.route('/')
def index():
    order = sort_order(request)
    # get episodes from database
    episodes = get_videos(order)
    # render the template
    return render_template(
        'index.html',
        episodes=episodes,
        order=order
    )


@sitemapper.include(url_variables={'episode_id': get_episode_list()})
@app.route('/episode/<episode_id>')
def episode(episode_id):
    return render_template(
        'episode.html',
        episode=get_episode(episode_id)
    )


@sitemapper.include(lastmod=DB_LAST_MODIFIED)
@app.route('/guests')
def guests():
    order = sort_order(request)
    return render_template(
        'guests.html',
        guests=Guestlist(order).guests
    )


@sitemapper.include(url_variables={'guest_name': get_guest_list()})
@app.route('/guest/<guest_name>')
def guest(guest_name):
    order = sort_order(request)
    guest = [g for g in Guestlist(
        order=order).guests if g.name == guest_name][0]
    return render_template(
        'guest.html',
        guest=guest,
        order=order
    )


@sitemapper.include(lastmod=DB_LAST_MODIFIED)
@app.route('/about')
def about():
    return render_template(
        'about.html',
        about=load_content('about')
    )


@sitemapper.include(lastmod=DB_LAST_MODIFIED)
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


@sitemapper.include(lastmod=DB_LAST_MODIFIED)
@app.route('/images')
def images():
    # load all images from the images folder
    images = os.listdir(os.path.join(
        os.path.dirname(__file__), 'static/thumbs'))
    for i, image in enumerate(images):
        # get the relative path to the image
        images[i] = '/thumbs/' + image
    return json.dumps(images)


@app.route("/sitemap.xml")
def sitemap():
    return sitemapper.generate()


# Run the app
if __name__ == '__main__':
    # Run the app
    app.run()
