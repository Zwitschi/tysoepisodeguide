"""YouTube API client with quota-aware rate limiting.

Ported from the youtube-notify project (app/youtube.py) and adapted for the
tysoepisodeguide update flow. Uses the official googleapiclient.discovery
client with the API key read from the API_KEY environment variable.
"""
import os
import threading
import time
from typing import Optional

import googleapiclient.discovery

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
API_KEY = os.getenv('API_KEY')


class TokenBucket:
    """Token bucket rate limiter for YouTube API quota.

    Default capacity of 10,000 units with a refill rate of 10,000 units per
    86400 seconds, matching the standard daily quota.
    """

    def __init__(self, capacity: float = 10000.0, refill_rate: float = 10000.0 / 86400.0):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens +
                          (now - self.last_refill) * self.refill_rate)
        self.last_refill = now

    def acquire(self, tokens: float = 1.0, block: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire `tokens` from the bucket, sleeping if necessary."""
        start = time.monotonic()
        while True:
            with self.lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                if not block:
                    return False
                missing = tokens - self.tokens
                wait = missing / self.refill_rate
            if timeout is not None and (time.monotonic() - start) + wait > timeout:
                return False
            time.sleep(min(wait, 1.0))


_default_rate_limiter = TokenBucket()


class YouTubeClient:
    """Quota-aware wrapper around the YouTube Data API v3 client."""

    COST_SEARCH = 100
    COST_READ = 1

    def __init__(self, api_key: Optional[str] = API_KEY, rate_limiter: Optional[TokenBucket] = None):
        if not api_key:
            raise ValueError('API_KEY environment variable is not set')
        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, developerKey=api_key, cache_discovery=False)
        self.rate_limiter = rate_limiter if rate_limiter is not None else _default_rate_limiter
        self._api_lock = threading.Lock()

    def execute_with_quota(self, request, cost: int = COST_READ):
        """Execute a google-api request after acquiring quota tokens."""
        self.rate_limiter.acquire(cost)
        with self._api_lock:
            return request.execute()

    @staticmethod
    def check_yt_return(response) -> bool:
        """Return True if the API response is valid and non-empty."""
        if 'error' in response:
            print('YouTube API error:', response['error'])
            return False
        if response['pageInfo']['totalResults'] == 0:
            return False
        return True

    def get_channel_uploads_playlist_id(self, channel_id: str):
        """Return the uploads playlist id ('UU…') for a channel id ('UC…')."""
        request = self.youtube.channels().list(part='contentDetails', id=channel_id)
        response = self.execute_with_quota(request, cost=self.COST_READ)
        if self.check_yt_return(response):
            related = response['items'][0].get(
                'contentDetails', {}).get('relatedPlaylists', {})
            uploads = related.get('uploads')
            if uploads:
                return uploads
        if channel_id.startswith('UC'):
            return 'UU' + channel_id[2:]
        return None

    def get_channel_video_items(self, channel_id: str, stop_at_known_ids=None, max_total=None):
        """Enumerate channel videos via the uploads playlist (newest first).

        Each page of 50 items costs 1 quota unit. If `stop_at_known_ids` is
        provided, pagination stops as soon as a known video id is encountered
        (all older videos are assumed known).
        """
        playlist_id = self.get_channel_uploads_playlist_id(channel_id)
        if not playlist_id:
            return []
        known = set(stop_at_known_ids or [])
        items = []
        page_token = None
        while True:
            request = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token)
            response = self.execute_with_quota(request, cost=self.COST_READ)
            if not self.check_yt_return(response):
                break
            for item in response.get('items', []):
                video_id = item.get('contentDetails', {}).get('videoId')
                if video_id and video_id in known:
                    return items
                items.append(item)
                if max_total is not None and len(items) >= max_total:
                    return items
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        return items

    def get_videos_details(self, video_ids, part='snippet,contentDetails') -> dict:
        """Batch fetch video details (50 ids per call), keyed by video id."""
        if not video_ids:
            return {}
        details = {}
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            request = self.youtube.videos().list(part=part, id=','.join(batch))
            response = self.execute_with_quota(request, cost=self.COST_READ)
            if self.check_yt_return(response):
                for item in response.get('items', []):
                    details[item['id']] = item
        return details


_client = None
_client_lock = threading.Lock()


def get_client() -> YouTubeClient:
    """Return the shared (lazily created) YouTube client."""
    global _client
    with _client_lock:
        if _client is None:
            _client = YouTubeClient()
        return _client
