# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import io
import json
import shutil
import tempfile
import unittest

import httpretty

from dozup import DozupPoster, DozupError


class PosterTests(unittest.TestCase):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    @httpretty.activate
    def test_post_one_file(self):
        httpretty.register_uri(
            httpretty.POST, 'http://example.com/drop/',
            status=202,
            content_type='application/json',
            body=json.dumps({'status': 'OK'}))
        self.poster = DozupPoster('http://example.com/drop/')
        strm = io.BytesIO(b'this is a message')

        result = self.poster.post('banko.txt', strm)

        self.assertTrue(result)
        self.assertEqual(b'this is a message', httpretty.last_request().body)
        self.assertEqual(b'POST', httpretty.last_request().method)
        self.assertEqual(b'/drop/', httpretty.last_request().path)

    @httpretty.activate
    def test_retains_plain_text_error_message(self):
        httpretty.register_uri(
            httpretty.POST, 'http://example.com/drop/',
            status=503,
            content_type='text/plain',
            body='Sorry!')
        self.poster = DozupPoster('http://example.com/drop/')
        strm = io.BytesIO(b'this is a message')

        result = self.poster.post('banko.txt', strm)

        self.assertFalse(result)
        self.assertEqual(DozupError(503, 'Sorry!'), self.poster.errors[-1])

    @httpretty.activate
    def test_retains_json_error_string(self):
        httpretty.register_uri(
            httpretty.POST, 'http://example.com/drop/',
            status=503,
            content_type='application/json',
            body='{"error": "Not today, thank you!"}')
        self.poster = DozupPoster('http://example.com/drop/')
        strm = io.BytesIO(b'this is a message')

        result = self.poster.post('banko.txt', strm)

        self.assertFalse(result)
        self.assertEqual(DozupError(503, 'Not today, thank you!'), self.poster.errors[-1])
