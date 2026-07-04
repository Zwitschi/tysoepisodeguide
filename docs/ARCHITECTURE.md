# Architecture — TYSO Episode Guide

## High-Level Architecture

The application follows a **three-layer architecture**:

```
┌──────────────────────────────────────────────────────┐
│                 Presentation Layer                   │
│     Flask App (app.py) + Jinja2 Templates            │
│     Routes, SSE streaming, sitemap generation        │
├──────────────────────────────────────────────────────┤
│                 Domain / Business Layer              │
│     Classes (episode.py, guest.py, channel.py, ...)  │
│     Setup logic (setup.py) — fetch, parse, update    │
├──────────────────────────────────────────────────────┤
│                 Data Access Layer                    │
│     Database (database.py) — SQLite CRUD             │
│     YouTube API (api.py, youtubeapi.py) — API calls  │
└──────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Web Layer (`app.py`)

The Flask application defines the following routes:

| Route                   | Template       | Description                                                               |
| ----------------------- | -------------- | ------------------------------------------------------------------------- |
| `/`                     | `index.html`   | Episode list, supports `?sort=ASC/DESC`, `?view=table/thumbs`, `?limit=N` |
| `/episode/<episode_id>` | `episode.html` | Single episode detail with embedded YouTube player                        |
| `/guests`               | `guests.html`  | List of all guests with their episode numbers                             |
| `/guest/<guest_name>`   | `guest.html`   | Single guest detail with all their episodes                               |
| `/about`                | `about.html`   | Renders `ABOUT.md` + `README.md` as HTML                                  |
| `/LICENSE`              | `about.html`   | Renders `LICENSE` as HTML                                                 |
| `/update`               | `update.html`  | Database update page (triggers SSE stream)                                |
| `/update/stream`        | —              | SSE endpoint streaming live update progress                               |
| `/images`               | —              | Returns JSON list of thumbnail file paths                                 |
| `/sitemap.xml`          | —              | Auto-generated sitemap via `flask_sitemapper`                             |

**Key Design Patterns in app.py:**

- **Helper functions** extract query parameters: `sort_order()`, `set_view_mode()`, `set_limit()` normalize user input from URL query strings.
- **SSE Streaming**: The `/update/stream` route uses a background thread with `threading.Thread`, `threading.Lock`, and `threading.Condition` to run the database update while streaming progress messages as Server-Sent Events. The `event_stream()` generator yields messages in SSE `data:` format.
- **Singleton update runner**: Global variables `_update_lock`, `_update_running`, `_update_messages`, and `_update_condition` ensure only one update runs at a time and all connected clients receive the same stream of messages.

### 2. Setup / Data Collection Layer (`setup.py`)

This module orchestrates the full data collection pipeline:

```
update_db(force=False)
    │
    ├── check_and_store_channel_details()
    │   └── Ensures channel metadata exists in DB
    │
    ├── get_video_ids(channel, force)
    │   └── get_youtube_video_ids()
    │       └── Calls YouTube Search API, paginates through results
    │
    └── For each video_id:
        ├── process_existing_video(row)
        │   └── Update DB if details changed, fill episode numbers
        └── process_new_video(video_id)
            ├── get_youtube_video() — fetch basic metadata
            └── get_episode_yt() — fetch details, check if it's an episode
```

**Generator pattern**: `update_db()` is a Python generator that `yield`s progress messages. This allows both synchronous callers (`update_db_collect()` → returns a string) and asynchronous SSE consumers (via the background thread) to use the same function.

**Key functions:**

| Function                          | Description                                                           |
| --------------------------------- | --------------------------------------------------------------------- |
| `load_content(content)`           | Loads Markdown files and converts them to HTML                        |
| `get_youtube_video_ids()`         | Fetches all video IDs from the channel via paginated API calls        |
| `get_youtube_video(video_id)`     | Downloads thumbnail for a single video, returns basic metadata        |
| `get_episode_yt(video_id)`        | Fetches full episode details if the video is identified as an episode |
| `get_channel_details(channel_id)` | Fetches YouTube channel metadata                                      |
| `handle_episode_detail(episode)`  | Compares episode data with DB and updates if changed                  |
| `check_thumbnails()`              | Ensures all thumbnails are downloaded and resized                     |
| `update_db(force)`                | Main update orchestrator (generator)                                  |
| `update_db_collect(force)`        | Wrapper that collects generator output into a string                  |
| `action_from_arguments(*args)`    | CLI argument parser for `setup.py`                                    |

### 3. Core Data Model Classes (`classes/`)

#### `Channel` (`channel.py`)

Represents a YouTube channel. Stores channel ID, title, URL, and last-updated timestamp.

- `read_channel_db(channel_id)` — reads channel from SQLite
- `check_channel_update_db()` — returns `True` if channel was updated within the last 24 hours
- `update_channel_db()` — persists the `last_updated` timestamp

#### `Database` (`database.py`) — Data Access Layer

Manages SQLite connections and provides CRUD operations.

**`Database` (base class):**

- Initializes the `db/` directory and database file
- `install()` — creates DB directory and tables if missing
- `check_install()` — verifies database existence

**`Channels` (extends `Database`):**

- `create()` — creates the `channels` table
- `insert(channel)` — inserts a channel row
- `read()` — reads the TYSO channel (hardcoded ID)

**`Videos` (extends `Database`):**

- `create()` — creates the `videos` table
- `insert(video)` — inserts a video row
- `update(video)` — updates a video row by ID
- `update_number(video_id, number)` — updates only the episode number
- `read(video_id)` — reads a single video by ID
- `read_ids()` — returns all video IDs
- `read_videos(order)` — returns all episode videos (filters out non-episode content like "Best of" compilations, shorts, and specific excluded titles)

**Security note**: The `read()` method uses string concatenation for the SQL query (`WHERE id = '` + video_id + `'`) rather than parameterized queries. This is a SQL injection risk if `video_id` comes from an untrusted source.

#### `Episode` (`episode.py`)

A rich domain object representing a podcast episode. Created from database rows.

- Parses the episode number from the title via `EpisodeNumber`
- Extracts guest names from the title via `EpisodeGuests`
- Formats the publish date from ISO 8601 to `YYYY-MM-DD`
- Formats the description by converting URLs to clickable links and line breaks to `<br />` tags

Properties:

- `id`, `title`, `url`, `description`, `thumb`, `published_date`, `duration`
- `number` — parsed episode number
- `formatted_date` — human-readable date
- `formatted_description` — HTML-enhanced description
- `guest` — list of guest names

#### `Video` (`video.py`)

A simpler model for raw YouTube video data. Contains the same core fields as `Episode` but without the parsing/number/guest logic.

#### `EpisodeNumber` (`episodenumber.py`)

Extracts episode numbers from video titles. Handles multiple formats:

- Standard: `Title #123` → `123`
- Balcony Series: regex extraction of number patterns
- Special cases: `50th` episode, `BEST OF`, `PATREON UNLOCKED`, `Shorts`
- Supports decimal numbers: `#100.5` → `100.5`
- Title cleanup: strips `)`, `!`, replaces `pt` with `.`

#### `EpisodeGuests` (`episodeguests.py`)

Extracts guest names from episode titles using a multi-step cleaning pipeline:

1. **`clean_by_mapping()`** — exact keyword-to-replacement mappings for known guests (e.g., `"Are You Garbage"` → `"Kevin James Ryan + Henry Foley"`)
2. **`sleepover_series()`** — strips "The Sleepover Series:" prefix
3. **`uncle_bob()`** — normalizes "(feat. Uncle Bob)" format
4. **`clean_by_split()`** — splits title on `(`, `[`, ` aka`, ` -` and takes the first part
5. **`clean_by_list_replace()`** — removes known patterns like episode numbers, "UNCENSORED", "on TYSO", "w/ Rick Glassman", etc.
6. Removes version numbers (1.0, 2.0, etc.)
7. The cleaned title becomes the guest name(s), split by `+`

#### `Guest` (`guest.py`)

Simple domain object for a podcast guest.

- `name` — guest's display name
- `episodes` — list of `Episode` objects they appear in
- `add_episode(episode)` — adds an episode to their list (no duplicates)

#### `Guestlist` (`guestlist.py`)

Builds the complete guest index from the database.

- Reads all videos from the database
- Creates `Episode` objects and extracts guest names
- Collects unique guest names across all episodes
- Sorts alphabetically
- Creates `Guest` objects with their associated episodes
- Supports ascending/descending sort order

#### `Thumbnail` (`thumbnail.py`)

Handles downloading and resizing YouTube video thumbnails.

- `download()` — fetches the thumbnail from the URL and saves it locally, then resizes
- `resize()` — resizes the image to 400px width while maintaining aspect ratio (uses Pillow)

#### `YouTubeAPI` (`youtubeapi.py`)

A wrapper around the Google API Python client with an HTTP fallback.

- Tries to use `googleapiclient.discovery.build()` if available
- Falls back to direct HTTP requests via `requests.get()` if the library is not installed
- Provides methods: `get_channel_id()`, `get_channel_videos()`, `get_channel_details()`, `get_video_details()`, `get_video_duration()`

### 4. Utility Modules (`utils/`)

#### `API` (`api.py`)

A lower-level HTTP API client that builds YouTube API URLs and makes requests.

- Constructs URLs for different task types: `videos`, `channel`, `video_detail`, `details`, `video`, `videos_next`
- Uses the API key from the `API_KEY` environment variable
- Returns parsed JSON responses

#### `Parsing` (`parsing.py`)

Pure functions for parsing YouTube data:

- `parse_duration(duration)` — converts ISO 8601 duration (e.g., `PT1H5M30S`) to total seconds (integer)
- `is_episode(episode_title, duration)` — returns `True` if the video is a full episode (duration > 1200s AND title contains "Take Your Shoes Off" or "TYSO")
- `get_episode_number(video_title)` — extracts episode number string from title (handles `#N`, Balcony Series, special cases)

#### `Timing` (`timing.py`)

- `sleep_with_delay(seconds)` — simple wrapper around `time.sleep()` to add delays between API calls (respecting rate limits)

#### `Images` (`images.py`)

- Scans the `static/thumbs/` directory for `.jpg` files
- Returns `Image` objects containing filename and base64-encoded binary data

### 5. Templates (`templates/`)

The templates use **Jinja2** with template inheritance:

- **`_base.html`** — root layout with `<html>`, `<head>`, `<body>`, navigation, content block, and footer
- **`_head.html`** — common `<head>` elements (Bootstrap CDN, meta tags, etc.)
- **`_nav.html`** — navigation bar with links to Home, Guests, About, Update
- **`index.html`** — two display modes: table view (with thumbnail, episode number, title, guest) and thumbnail grid view
- **`episode.html`** — full episode page with embedded YouTube iframe, metadata, and formatted description
- **`guests.html`** — alphabetical guest list table with episode links
- **`guest.html`** — single guest page with sorted episode list
- **`about.html`** — renders Markdown content as HTML
- **`update.html`** — triggers and displays SSE stream from `/update/stream`

---

## Data Flow Diagrams

### Database Update Flow

```
setup.py update_db(force=False)
    │
    ├── yield "[timestamp] Update started"
    │
    ├── check_and_store_channel_details(channels, channel_id)
    │   ├── Read channel from DB
    │   └── If not found: fetch from YouTube API → insert into DB
    │
    ├── get_video_ids(channel, force)
    │   ├── Check 24-hour cache (skip API if recently updated, unless force=True)
    │   ├── get_youtube_video_ids() — paginated API call
    │   └── Return list of video IDs
    │
    └── For each video_id:
        ├── [Already in DB?]
        │   ├── Yes → process_existing_video(row)
        │   │   ├── Update metadata if changed
        │   │   └── Fill episode number if missing
        │   └── No → process_new_video(video_id)
        │       ├── get_youtube_video() — download thumbnail
        │       ├── get_episode_yt() — fetch details, check if episode
        │       └── If episode: insert into DB
        │
        └── yield "[timestamp] Update finished"
```

### Request Serving Flow

```
Browser Request → Flask Route → Helper Functions → Database Query → Domain Objects → Template Rendering → HTML Response

Example: /episode/abc123
    │
    ├── route: episode(episode_id)
    ├── get_episode(episode_id)
    │   ├── Videos().read(video_id) → SQLite query
    │   └── Episode(row) → parse number, guests, format date/description
    └── render_template('episode.html', episode=...)
```

---

## Design Patterns Used

| Pattern             | Where                                                            | Description                                                       |
| ------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Generator**       | `setup.py` — `update_db()`                                       | Yields progress messages; consumed both synchronously and via SSE |
| **Singleton**       | `app.py` — global `_update_running`                              | Ensures only one DB update runs at a time                         |
| **Template Method** | `database.py` — `Database` base + `Channels`/`Videos` subclasses | Shared DB setup, specialized CRUD per table                       |
| **Strategy**        | `youtubeapi.py` — fallback logic                                 | Tries google client first, falls back to HTTP                     |
| **Pipeline**        | `episodeguests.py` — `clean_title()`                             | Multi-step title cleaning pipeline                                |
| **Data Mapper**     | `database.py` — `Videos`/`Channels`                              | Maps database rows to Python dicts                                |

---

## Configuration

- **API Key**: Set the `API_KEY` environment variable (or in a `.env` file) with a YouTube Data API v3 key.
- **Channel ID**: Hardcoded as `UCYCGsNTvYxfkPkfQopRMP7w` (Rick Glassman's channel) in `setup.py`, `utils/api.py`, and `classes/database.py`.
- **Database path**: `db/tysodb.db` relative to the project root.
- **Thumbnail size**: Resized to 400px width (defined in `classes/thumbnail.py`).

---

## Security Considerations

1. **SQL Injection**: The `Videos.read()` method uses string concatenation for the WHERE clause. In the current context, `video_id` values come from the YouTube API or URL parameters. For production, consider using parameterized queries.
2. **API Key**: The YouTube API key is read from an environment variable and used in URL query strings. Ensure the `.env` file is not tracked in version control.
3. **SSRF**: The thumbnail downloader fetches URLs from the YouTube API response — low risk since the source is trusted.
