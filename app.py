from flask_sitemapper import Sitemapper
from datetime import datetime
import json
import math
import os
from flask import Flask, render_template, request, Response
from classes.database import Videos
from classes.episode import Episode
from classes.guestlist import Guestlist
from setup import update_db, update_db_collect, load_content
import threading
import time


# page sizes available in the pagination selector
PAGE_SIZES = [25, 50, 100, 500, 1000]
PAGE_SIZE_DEFAULT = 25


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


def set_view_mode(request):
    # initialize view mode with empty string
    view = ''
    # get view mode from request args if present
    if 'view' in request.args:
        view = request.args.get('view', view, type=str)
    # only allow 'table' or 'thumbs'
    if view not in ['table', 'thumbs']:
        view = 'table'
    return view


def set_limit(request, default=0):
    # initialize limit with default
    limit = default
    # get limit from request args if present
    if 'limit' in request.args:
        limit = request.args.get('limit', limit, type=int)
    return max(limit, 0)


def set_offset(request):
    # initialize offset with 0
    offset = 0
    # get offset from request args if present
    if 'offset' in request.args:
        offset = request.args.get('offset', offset, type=int)
    return max(offset, 0)


def set_page(request):
    # current page number (1-based)
    page = request.args.get('page', 1, type=int)
    return max(page, 1)


def set_per_page(request):
    # number of episodes per page
    per_page = request.args.get('per_page', PAGE_SIZE_DEFAULT, type=int)
    if per_page not in PAGE_SIZES:
        per_page = PAGE_SIZE_DEFAULT
    return per_page


def paginate(items, page, per_page):
    """Slice `items` into a page and return pagination metadata."""
    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), total_pages)
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'start': start + 1 if total else 0,
        'end': end,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

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
    if not e:
        return None
    return Episode(e[0], e[1], e[2], e[3], e[4], e[5], e[6])


def get_guest_list():
    guest_list = []
    # get Guestlist object
    g = Guestlist(order='ASC')
    # get list of guests
    for guest in g.guests:
        guest_list.append(guest.name)
    return guest_list


def json_response(data, status=200):
    """Serialize data as a JSON response with the proper content type."""
    return Response(json.dumps(data), mimetype='application/json', status=status)


# Global variables
DB_LAST_MODIFIED = db_last_modified()


# Routes

@sitemapper.include(lastmod=DB_LAST_MODIFIED, changefreq='weekly', priority=0.8)
@app.route('/')
def index():
    display = set_view_mode(request)
    order = sort_order(request)
    page = set_page(request)
    per_page = set_per_page(request)
    # get episodes from database
    episodes = get_videos(order)
    pagination = paginate(episodes, page, per_page)
    # render the template
    return render_template(
        'index.html',
        episodes=pagination['items'],
        order=order,
        display=display,
        pagination=pagination
    )


@sitemapper.include(url_variables={'episode_id': get_episode_list()})
@app.route('/episode/<episode_id>')
def episode(episode_id):
    ep = get_episode(episode_id)
    if ep is None:
        return 'Episode not found', 404
    return render_template(
        'episode.html',
        episode=ep
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
    page = set_page(request)
    per_page = set_per_page(request)
    guest = [g for g in Guestlist(
        order=order).guests if g.name == guest_name][0]
    pagination = paginate(guest.episodes, page, per_page)
    return render_template(
        'guest.html',
        guest=guest,
        order=order,
        episodes=pagination['items'],
        pagination=pagination
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


# JSON API

@app.route('/api/episodes')
def api_episodes():
    """List episodes (optionally sorted, limited, and offset for pagination)."""
    order = sort_order(request)
    limit = set_limit(request, default=20)
    offset = set_offset(request)
    episodes = get_videos(order)
    total = len(episodes)
    end = offset + limit if limit > 0 else len(episodes)
    return json_response({
        'count': total,
        'offset': offset,
        'limit': limit,
        'episodes': [e.to_dict() for e in episodes[offset:end]],
    })


@app.route('/api/episodes/<episode_id>')
def api_episode(episode_id):
    """Return a single episode by video id."""
    ep = get_episode(episode_id)
    if ep is None:
        return json_response({'error': 'Episode not found'}, 404)
    return json_response(ep.to_dict())


@app.route('/api/guests')
def api_guests():
    """List all guests with their episode counts."""
    order = sort_order(request)
    guests = Guestlist(order).guests
    return json_response({
        'count': len(guests),
        'guests': [{'name': g.name, 'episode_count': len(g.episodes)} for g in guests],
    })


@app.route('/api/guests/<guest_name>')
def api_guest(guest_name):
    """Return a single guest and the list of their episodes."""
    order = sort_order(request)
    matches = [g for g in Guestlist(order).guests if g.name == guest_name]
    if not matches:
        return json_response({'error': 'Guest not found'}, 404)
    guest = matches[0]
    return json_response({
        'name': guest.name,
        'episodes': [e.to_dict() for e in guest.episodes],
    })


@app.route("/sitemap.xml")
def sitemap():
    return sitemapper.generate()


# Run the app
if __name__ == '__main__':
    # Run the app
    app.run()
