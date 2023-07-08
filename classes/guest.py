"""
Guest class

This class is used to create a guest object. It has the following attributes:
    - name: string
    - episodes: list of Episode objects
"""
class Guest:
    def __init__(self, name, episodes=None):
        self.name = name
        self.episodes = episodes

    def __str__(self):
        return self.name
    
    def get_episodes(self):
        return self.episodes
    
    def add_episode(self, episode):
        if episode not in self.episodes:
            self.episodes.append(episode)

