from flask_sitemapper import Sitemapper
from datetime import datetime
import json
import os
from flask import Flask, render_template, request, Response
from classes.database import Videos
from classes.episode import Episode
from classes.guestlist import Guestlist
from setup import update_db, update_db_collect, load_content
import threading
import time

# Singleton update runner state
# _update_lock: protects starting/stopping the update
_update_lock = threading.Lock()
# _update_running: True when an update is in progress
_update_running = False
# _update_messages: list of strings produced so far
_update_messages = []
# _update_condition: notify waiting stream clients of new messages
_update_condition = threading.Condition()


def _run_update_in_background(force=False):
    """Run update_db generator in a background thread and populate the shared message list."""
    global _update_running, _update_messages
    try:
        for msg in update_db(force=force):
            with _update_condition:
                _update_messages.append(msg)
                _update_condition.notify_all()
        # final message(s) appended by generator
    except Exception as e:
        with _update_condition:
            _update_messages.append(f"[error] {e}")
            _update_condition.notify_all()
    finally:
        with _update_condition:
            _update_running = False
            _update_condition.notify_all()

# add gzip compression
# from flask_compress import Compress


# add site map

# init Flask app
app = Flask(__name__, static_url_path='',
            static_folder='static', template_folder='templates')

# enable gzip compression
# Compress(app)

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
    dbpath = os.path.join(os.path.dirname(__file__), 'db')
    dbfile = os.path.join(dbpath, 'tysodb.db')
    if not os.path.exists(dbfile):
        return '1970-01-01'
    # get the last modified date of the database
    last_modified = os.path.getmtime(dbfile)
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
    display = 'table'
    display = 'thumbs'
    order = sort_order(request)
    # get episodes from database
    episodes = get_videos(order)
    # render the template
    return render_template(
        'index.html',
        episodes=episodes,
        order=order,
        display=display
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
    # Render the update page; the page's JS will connect to /update/stream to receive live updates
    return render_template('update.html')


@app.route('/update/stream')
def update_stream():
    # Stream Server-Sent Events (SSE) from a singleton background update runner.
    global _update_running

    # Start the update in background if not running
    with _update_lock:
        if not _update_running:
            _update_running = True
            _update_messages.clear()
            thread = threading.Thread(target=_run_update_in_background, kwargs={
                                      'force': False}, daemon=True)
            thread.start()

    def event_stream():
        # First, send all cached messages so far
        last_index = 0
        with _update_condition:
            # send existing messages
            while last_index < len(_update_messages):
                msg = _update_messages[last_index]
                last_index += 1
                yield f"data: {msg}\n\n"

            # then wait for new messages and stream them as they arrive
            while True:
                # wait for a notification
                _update_condition.wait()
                # stream any new messages
                while last_index < len(_update_messages):
                    msg = _update_messages[last_index]
                    last_index += 1
                    yield f"data: {msg}\n\n"
                # if no update running and no new messages, close the stream
                if not _update_running:
                    break

    return Response(event_stream(), mimetype='text/event-stream')


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
