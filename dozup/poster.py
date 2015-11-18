# -*- coding: UTF-8 -*-


import requests


SUCCESSFUL_CODES = requests.codes.ok, requests.codes.created, requests.codes.accepted


class DozupError(object):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __eq__(self, other):
        if not hasattr(other, 'status_code') or not hasattr(other, 'message'):
            return NotImplemented
        return other.status_code == self.status_code and other.message == self.message

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return 'DozupError(%r, %r)' % (self.status_code, self.message)

    def __str__(self):
        return '%d (%s)' % (self.status_code, self.message)


class DozupPoster(object):
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.errors = []

    def post(self, file_name, stream):
        response = self.session.post(self.url, stream)
        if response.status_code in SUCCESSFUL_CODES:
            return True
        if response.headers.get('Content-Type') == 'text/plain':
            self.errors.append(DozupError(response.status_code, response.text))
        if response.headers.get('Content-Type') == 'application/json':
            obj = response.json()
            if 'error' in obj:
                msg = obj['error']
            else:
                msg = response.text()
            self.errors.append(DozupError(response.status_code, msg))
        return False
