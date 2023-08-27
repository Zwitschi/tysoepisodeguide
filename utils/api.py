import os
import requests
from dotenv import load_dotenv

class API:
    def __init__(self, task: str, video_id: str = None, next_page: str = None):
        self.task = task
        self.video_id = video_id
        self.url = 'https://www.googleapis.com/youtube/v3/'
        self.channel_id = 'UCYCGsNTvYxfkPkfQopRMP7w'
        self.next_page = next_page
        self.api_key = os.getenv('API_KEY')
        self.url = self.build_url()
        self.data = self.api_call()
        
    def api_call(self) -> dict:
        """Make an API call to the YouTube API"""
        res = requests.get(self.url)
        if res.status_code != 200:
            print('Error: ' + str(res.status_code) + ' - ' + res.content.decode('utf-8'))
            return
        return res.json()
    
    def build_url(self) -> str:
        videos_url = self.url + 'search?part=snippet&channelId=' + self.channel_id + '&maxResults=50&order=date&type=video&key=' + self.api_key
        channel_url = self.url + 'channels?part=snippet,contentDetails&id=' + self.channel_id + '&key=' + self.api_key
        if self.task == 'videos':
            return videos_url
        elif self.task == 'channel':
            return channel_url
        elif self.task == 'video_detail':
            video_detail_url = self.url + 'videos?part=snippet,contentDetails&id=' + self.video_id + '&key=' + self.api_key
            return video_detail_url
        elif self.task == 'details':
            detail_url = self.url + 'videos?part=contentDetails&id=' + self.video_id + '&key=' + self.api_key
            return detail_url
        elif self.task == 'video':
            video_url = self.url + 'videos?part=snippet&id=' + self.video_id + '&key=' + self.api_key
            return video_url
        elif self.task == 'videos_next':
            next_url = self.url + 'search?part=snippet&channelId=' + self.channel_id + '&maxResults=50&order=date&type=video&key=' + self.api_key + '&pageToken=' + self.next_page
            return next_url
