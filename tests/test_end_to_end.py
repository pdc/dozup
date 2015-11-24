# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

"""Tests for the system as a whole."""

import os
import shutil
import tempfile
import unittest

import httpretty

from dozup.cli import main


class EndToEndTests(unittest.TestCase):
    endpoint_path = b'/path/to/endpoint.quux'
    endpoint_url = b'http://api.example.com' + endpoint_path
    status_code = 202
    content_type = b'text/plain'
    content = 'OK'

    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    @httpretty.activate
    def test_post_one(self, content='{"success":true}', content_type=None):
        httpretty.register_uri(
            httpretty.POST, self.endpoint_url,
            status=self.status_code,
            content_type=(content_type or self.content_type),
            body=(content or self.content))
        self.given_a_file('todo/hello.txt', b'this is the message content')

        status = main([self.dir_path, self.endpoint_url])

        self.assertFalse(status)  # Unix convention for nothing went wrong

        # Did post as expected.
        self.assertTrue(httpretty.has_request(), 'Expected HTTP POST to %s' % self.endpoint_url)
        self.assertEqual(b'this is the message content', httpretty.last_request().body)
        self.assertEqual(b'POST', httpretty.last_request().method)
        self.assertEqual(self.endpoint_path, httpretty.last_request().path)

        # File was filed away.
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, 'done/hello.txt')))

    def create_a_file(self, relative_path, content=''):
        os.makedirs(os.path.join(self.dir_path, os.path.dirname(relative_path)))
        with open(os.path.join(self.dir_path, relative_path), 'wb') as strm:
            strm.write(content)
    given_a_file = create_a_file
