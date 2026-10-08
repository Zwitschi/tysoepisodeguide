"""
YouTube API class
"""
import os
import requests
from datetime import datetime

API_URL = 'https://www.googleapis.com/youtube/v3/'
# load API_KEY from .env
API_KEY = os.getenv('API_KEY')

class YouTubeAPI:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_channel_id(self, channel_name):
        request = self.youtube.channels().list(
            part='id',
            forUsername=channel_name
        )
        response = request.execute()
        return response['items'][0]['id']

    def get_channel_videos(self, channel_id):
        request = self.youtube.search().list(
            part='snippet',
            channelId=channel_id,
            maxResults=50,
            order='date',
            type='video'
        )
        response = request.execute()
        return response['items']
    
    def get_channel_details(channel_id):
        """
        Query the YouTube API for the channel details

        Args:
            channel_id: string, the id of the channel
            
        Returns:
            dict: the channel details
        """
        channel_url = API_URL + 'channels?part=snippet,contentDetails&id=' + channel_id + '&key=' + API_KEY
        res_json = api_call(channel_url)
        channel = {
            'id': channel_id,
            'title': res_json['items'][0]['snippet']['title'],
            'url': 'https://www.youtube.com/channel/' + channel_id,
            'last_updated': datetime.now().timestamp()
        }
        return channel

    def get_video_details(self, video_id):
        request = self.youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response = request.execute()
        return response['items'][0]

    def get_video_duration(self, video_id):
        request = self.youtube.videos().list(
            part='contentDetails',
            id=video_id
        )
        response = request.execute()
        return response['items'][0]['contentDetails']['duration']

def build(url, version, developerKey):
    """
    Build API url

    Args:
        url: string, the base url
        version: string, the API version
        developerKey: string, the API key
        
    Returns:
        string: the API url
    """
    if url=='youtube':
        url = 'https://www.googleapis.com/youtube'
    return url + '/' + version + '?key=' + developerKey

def api_call(url):
    """
    Make an API call to the YouTube API

    Args:
        url: string, the url to call

    Returns:
        dict: the response from the API
    """
    response = requests.get(url)
    if response.status_code != 200:
        print('Error: ' + str(response.status_code) + ' - ' + response.content.decode('utf-8'))
        return
    res_json = response.json()
    return res_json