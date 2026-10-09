# TYSO Episode Guide — Documentation Overview

## Project Description

The **TYSO Episode Guide** is a web application that generates and displays an episode guide for the _Take Your Shoes Off_ podcast with Rick Glassman. It fetches video data from [Rick Glassman's YouTube Channel](https://www.youtube.com/@rickglassman) using the [YouTube Data API v3](https://developers.google.com/youtube/v3), stores the information in a local SQLite database, and serves it via a Flask web application.

The live site is available at [https://tysoepisodeguide.azurewebsites.net/](https://tysoepisodeguide.azurewebsites.net/).

---

## Project Structure

```
tysoepisodeguide/
├── app.py                  # Flask web application — routes, views, SSE streaming
├── setup.py                # Database setup, YouTube API data fetching, update orchestration
├── ABOUT.md                # About page content (Markdown)
├── README.md               # Project README (also rendered on /about)
├── LICENSE                 # MIT License (rendered on /LICENSE)
├── requirements.txt        # Python dependencies
├── classes/                # Core data model classes
│   ├── __init__.py         # Empty
│   ├── channel.py          # Channel model — YouTube channel metadata
│   ├── database.py         # Database abstraction — SQLite connection, CRUD for channels & videos
│   ├── episode.py          # Episode model — single podcast episode representation
│   ├── episodeguests.py    # EpisodeGuests — guest name extraction from episode titles
│   ├── episodenumber.py    # EpisodeNumber — episode number extraction from titles
│   ├── guest.py            # Guest model — single guest with episode list
│   ├── guestlist.py        # Guestlist — builds the full guest list from all episodes
│   ├── thumbnail.py        # Thumbnail — download and resize YouTube thumbnails
│   ├── video.py            # Video model — raw YouTube video data representation
│   └── youtubeapi.py       # YouTubeAPI — wrapper around googleapiclient with HTTP fallback
├── utils/                  # Utility modules
│   ├── __init__.py         # Empty
│   ├── api.py              # API — low-level YouTube API URL builder and HTTP caller
│   ├── images.py           # Images — image file listing and base64 encoding
│   ├── parsing.py          # Parsing — duration parsing, episode detection, number extraction
│   └── timing.py           # Timing — sleep/delay helper
├── db/                     # SQLite database directory (created at runtime)
│   └── tysodb.db           # The SQLite database file
├── static/                 # Static assets served by Flask
│   ├── css/style.css       # Stylesheet
│   ├── img/                # Image assets
│   ├── js/preloader.js     # JavaScript preloader
│   └── thumbs/             # Downloaded and resized video thumbnails
├── templates/              # Jinja2 HTML templates
│   ├── _base.html          # Base layout template
│   ├── _head.html          # HTML <head> partial
│   ├── _nav.html           # Navigation bar partial
│   ├── index.html          # Home page — episode list (table or thumbnail view)
│   ├── episode.html        # Single episode detail page
│   ├── guests.html         # All guests listing page
│   ├── guest.html          # Single guest detail page
│   ├── about.html          # About / License page
│   └── update.html         # Database update page with SSE progress
└── tyso/                   # Python virtual environment
```

---

## Key Dependencies

| Package                    | Purpose                                                      |
| -------------------------- | ------------------------------------------------------------ |
| `flask`                    | Web framework                                                |
| `flask_sitemapper`         | Automatic sitemap.xml generation                             |
| `google-api-python-client` | Official Google API client (optional — HTTP fallback exists) |
| `gunicorn`                 | Production WSGI server                                       |
| `markdown`                 | Convert Markdown files to HTML for the About page            |
| `pillow`                   | Image resizing for thumbnails                                |
| `requests`                 | HTTP requests for YouTube API (fallback)                     |

---

## Data Flow Overview

1. **Data Collection** (`setup.py`): Queries the YouTube Data API for all videos from Rick Glassman's channel, filters for full episodes, extracts metadata (title, description, duration, thumbnails, episode numbers, guest names), and stores everything in a SQLite database.
2. **Data Serving** (`app.py`): A Flask application reads from the SQLite database and renders Jinja2 templates to display episodes, guests, and details.
3. **Live Updates**: The `/update` page uses Server-Sent Events (SSE) to stream real-time progress while the database is being refreshed from the YouTube API.

---

## Database Schema

The SQLite database (`db/tysodb.db`) contains two tables:

### `channels`

| Column         | Type      | Description                   |
| -------------- | --------- | ----------------------------- |
| `id`           | TEXT (PK) | YouTube channel ID            |
| `title`        | TEXT      | Channel display name          |
| `url`          | TEXT      | Channel URL                   |
| `last_updated` | TEXT      | Unix timestamp of last update |

### `videos`

| Column           | Type      | Description                                              |
| ---------------- | --------- | -------------------------------------------------------- |
| `id`             | TEXT (PK) | YouTube video ID                                         |
| `title`          | TEXT      | Video title                                              |
| `url`            | TEXT      | YouTube video URL                                        |
| `description`    | TEXT      | Video description                                        |
| `thumb`          | TEXT      | Thumbnail URL                                            |
| `published_date` | TEXT      | ISO 8601 publish date                                    |
| `duration`       | INTEGER   | Duration in seconds                                      |
| `number`         | TEXT      | Episode number (string to support decimals like "100.5") |
