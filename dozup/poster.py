# -*- coding: UTF-8 -*-


import requests


class DozupPoster(object):
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()

    def post(self, file_name, stream):
        response = self.session.post(self.url, stream)
        return True
