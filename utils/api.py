import os
import requests

API_URL = 'https://www.googleapis.com/youtube/v3/'
CHANNELID = 'UCYCGsNTvYxfkPkfQopRMP7w'
API_KEY = os.getenv('API_KEY')

def api_call(url: str) -> dict:
    """Make an API call to the YouTube API"""
    res = requests.get(url)
    if res.status_code != 200:
        print('Error: ' + str(res.status_code) + ' - ' + res.content.decode('utf-8'))
        return
    return res.json()

def build_video_url(task: str, video_id: str) -> str:
    video_detail_url = API_URL + 'videos?part=snippet,contentDetails&id=' + video_id + '&key=' + API_KEY
    detail_url = API_URL + 'videos?part=contentDetails&id=' + video_id + '&key=' + API_KEY
    video_url = API_URL + 'videos?part=snippet&id=' + video_id + '&key=' + API_KEY
    if task == 'video_detail':
        return video_detail_url
    elif task == 'details':
        return detail_url
    elif task == 'video':
        return video_url

def build_url(task: str) -> str:
    videos_url = API_URL + 'search?part=snippet&channelId=' + CHANNELID + '&maxResults=50&order=date&type=video&key=' + API_KEY
    channel_url = API_URL + 'channels?part=snippet,contentDetails&id=' + CHANNELID + '&key=' + API_KEY
    if task == 'videos':
        return videos_url
    elif task == 'channel':
        return channel_url