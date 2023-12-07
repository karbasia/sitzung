from django.core.cache import cache
from O365.utils import BaseTokenBackend

class DjangoCacheTokenBackend(BaseTokenBackend):

    def __init__(self):
        super().__init__()
        self.token_key = 'token'

    def load_token(self):
        token = cache.get(self.token_key)
        if token:
            token = self.token_constructor(self.serializer.loads(token))
        return token
    
    def save_token(self):
        if self.token is None:
            raise ValueError('You have to set the "token" first.')

        cache.set(self.token_key, self.serializer.dumps(self.token), 3600)

        return True
    
    def delete_token(self):
        cache.delete(self.token_key)
        return True
    
    def check_token(self):
        return cache.get(self.token_key) is not None