import requests
from PIL import Image

class Thumbnail:
    def __init__(self, thumbnail_url: str, thumbnail_path: str) -> None:
        self.thumbnail_url = thumbnail_url
        self.thumbnail_path = thumbnail_path

    def download(self) -> None:
        """Download the thumbnail from the url and save it to the path"""
        response = requests.get(self.thumbnail_url)
        if response.status_code == 200:
            with open(self.thumbnail_path, 'wb') as f:
                f.write(response.content)
            self.resize()

    def resize(self) -> None:
        """Resize the thumbnail to 200px width"""
        image = Image.open(self.thumbnail_path)
        dimensions = image.size
        if dimensions[0] > 200:
            ratio = 200 / dimensions[0]
            new_height = int(dimensions[1] * ratio)
            image = image.resize((200, new_height))
            image.save(self.thumbnail_path)