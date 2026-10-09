# TODO — Integrate youtube-notify update logic into tysoepisodeguide YouTube fetching

## Goal

Replace the current, quota-expensive YouTube fetching in `setup.py` with the
efficient patterns from `youtube-notify` (`app/youtube.py` + `app/__init__.py`),
while keeping the existing episode/guest business logic (filtering, episode
numbers, thumbnails, SSE update stream) intact.

## What youtube-notify's update function does (techniques to adopt)

From `/home/zwitschi/Documents/02-Projects/30-TYSO/youtube-notify`:

1. **Uploads playlist enumeration** — `get_channel_all_videos()` paginates
   `playlistItems.list(part="snippet,contentDetails", playlistId="UU…")` instead
   of `search.list`. Cost: **1 quota unit per 50 videos** (vs 100 per search page)
   and it is not capped by the ~500 result search ceiling.
2. **Batch video details** — `get_videos_details(video_ids, part="contentDetails")`
   fetches details in batches of **50 IDs per `videos.list` call** (1 unit/batch).
3. **Incremental "latest only" path** — `sync_channel_latest()` / `check_for_new_videos()`
   only query videos published after the last known video, tracked via a
   `latest_channel_video` table.
4. **Token bucket rate limiter** — `TokenBucket` (10,000 units/day, refilled over
   86400s) with `execute_with_quota()` wrapping every API call.
5. **Official client** — `googleapiclient.discovery.build('youtube', 'v3', …)`.

## Current tysoepisodeguide problems (in `setup.py`)

- `get_youtube_video_ids()` uses `search.list` via raw `requests` (`utils/api.py`)
  and throws away the snippets (keeps only IDs).
- Every new video triggers **2× `videos.list` calls** (`get_youtube_video()` and
  `get_episode_yt()`) plus a `sleep_with_delay(1)` — even for Shorts/clips that are
  never inserted.
- Thumbnails are downloaded for **all** new videos before the `is_episode` filter
  runs (wasted downloads for non-episodes).
- No batching, no quota awareness, no incremental path (re-fetches everything after
  24 h or with `--force`).
- Two parallel API implementations: `utils/api.py` (raw `requests`, used) and
  `classes/youtubeapi.py` (googleapiclient, effectively unused).

Estimated quota for a full sync of ~400 videos: **~1,600+ units today vs ~20 units**
with the new approach.

## Design decisions (proposed)

- **Primary client:** `googleapiclient.discovery` (already in `requirements.txt`),
  API key from env `API_KEY` (never hardcode — note `youtube-notify` hardcodes one,
  we will not copy that).
- **Full sync (`force=True`)**: enumerate the entire uploads playlist.
- **Incremental sync (default)**: enumerate playlistItems newest-first and **stop at
  the first video ID already in the DB** (playlistItems are newest-first, so
  everything older is known). No extra tracking table needed — reuse
  `channels.last_updated` and existing video IDs.
- **Batch details** in groups of 50; apply `is_episode()` + `get_episode_number()`
  once per video from the batch result.
- **Download thumbnails only for episodes that are actually inserted** (drop the
  per-video `sleep_with_delay`; the rate limiter replaces it).
- Keep `update_db()` a generator so the SSE `/update/stream` flow in `app.py`
  keeps working unchanged.

## Implementation steps

### Phase 1 — New YouTube client module: `utils/youtube.py`

- [x] Add `TokenBucket` (capacity 10,000, refill 10,000/86400s, thread-safe).
- [x] Add `YouTubeClient` wrapping `googleapiclient.discovery`:
  - [x] `get_channel_uploads_playlist_id(channel_id)`.
  - [x] `get_channel_video_items(channel_id, stop_at_known_ids=None, max_total=None)` — paginated `playlistItems.list`, newest-first, optional early stop.
  - [x] `get_videos_details(video_ids, part='snippet,contentDetails')` — batches of 50.
  - [x] `execute_with_quota(request, cost)` wrapper + `check_yt_return()` guard.
- [x] Lazy `get_client()` singleton + clear error when `API_KEY` is missing (the app
      still imports/starts without a key).

### Phase 2 — Rewrite `setup.py` fetch helpers

- [x] Replaced `get_youtube_video_ids()` / `get_youtube_video()` / `get_episode_yt()` /
      `get_video_duration()` with `_playlist_item_meta()`, `_detail_to_episode()`,
      `_download_thumbnail()`, `fetch_video()`.
- [x] Batch detail fetch (50 IDs/call) + single episode-building code path.
- [x] `is_episode()` applied before thumbnail download; Shorts/clips skipped without
      download or DB insert.
- [x] Removed per-video `sleep_with_delay(1)`.

### Phase 3 — `update_db()` flow

- [x] `update_db(force=False)`:
  - `force=True` → full uploads-playlist enumeration.
  - `force=False` → incremental (stop at first known video ID).
- [x] Kept `check_and_store_channel_details()` + update `channels.last_updated`.
- [x] Preserved `process_existing_video()` behaviour (fill NULL titles, re-derive
      `number == '0'` rows).

### Phase 4 — Cleanup & docs

- [x] `utils/api.py` / `utils/timing.py` no longer used by the update flow
      (left in place, documented as legacy).
- [x] `classes/youtubeapi.py` left as legacy (documented).
- [x] Updated `docs/ARCHITECTURE.md` + `docs/README.md`.
- [x] `google-api-python-client` confirmed in `requirements.txt`.

### Phase 5 — Verify

- [x] `py_compile` passes for `setup.py` and `utils/youtube.py`.
- [x] Import test: `setup` imports without `API_KEY`; `get_client()` raises a clear error.
- [x] `update_db()` generator starts and yields the first progress message.
- [ ] (Optional, needs API key) Live dry-run of `update_db(force=False)` against the API.

## Decisions (confirmed)

1. Scope: **both full-load refactor and incremental (non-force) path**.
2. Rate limiter: **include the TokenBucket quota limiter**.
3. Client: **googleapiclient primary, drop the raw `requests` fallback**.
4. Docs: **update `docs/ARCHITECTURE.md` + `docs/README.md` in the same change**.
