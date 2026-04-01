class Runtime():
    def __init__(self, request):
        self._request = request

    def get_request(self):
        return self._request
