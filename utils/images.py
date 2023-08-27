import os

class Images:
    def __init__(self) -> None:
        self.images = self.get_images()
        
    def get_images(self) -> list:
        """Get the list of images from the images folder"""
        images = []
        for f in os.listdir(os.path.join(os.path.dirname(__file__), '../static/thumbs')):
            if f.endswith('.jpg'):
                images.append(Image(f))
        return images

class Image:
    def __init__(self, image: str) -> None:
        self.image = image
        self.data = self.get_data()
        
    def get_data(self) -> dict:
        """Get the image data, base64 encoded"""
        with open(os.path.join(os.path.dirname(__file__), '../static/thumbs/' + self.image), 'rb') as f:
            data = f.read()
        return data