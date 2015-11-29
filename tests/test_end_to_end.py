# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

"""Tests for the system as a whole."""

import os
import shutil
import tempfile
import unittest

import httpretty

from dozup.cli import main


class EndToEndTestMixin(object):
    def create_a_file(self, relative_path, content=''):
        os.makedirs(os.path.join(self.dir_path, os.path.dirname(relative_path)))
        with open(os.path.join(self.dir_path, relative_path), 'wb') as strm:
            strm.write(content)
    given_a_file = create_a_file

    def then_exit_code_should_denote_success(self, exit_code):
        self.assertFalse(exit_code)
        # Python convention for returning 0,
        # which is Unix convention for nothing went wrong.

    def then_exit_code_should_denote_error(self, exit_code):
        self.assertTrue(exit_code)
        # Python convention for returning nonzero,
        # which is Unix convention for something did go wrong.

    def then_should_post_to_server(self, content):
        self.assertTrue(httpretty.has_request(), 'Expected HTTP POST to %s' % self.endpoint_url)
        self.assertEqual(b'POST', httpretty.last_request().method)
        self.assertEqual(content, httpretty.last_request().body)
        self.assertEqual(self.endpoint_path, httpretty.last_request().path)

    def then_file_should_be_moved_to_done(self, file_name):
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, 'todo', file_name)))
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, 'done', file_name)))

    def then_file_should_be_left_in_todo(self, file_name):
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, 'todo', file_name)))
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, 'done', file_name)))


class EndToEndSuccessTests(EndToEndTestMixin, unittest.TestCase):
    endpoint_path = b'/path/to/endpoint.quux'
    endpoint_url = b'http://api.example.com' + endpoint_path
    status_code = 202
    content_type = b'text/plain'
    content = 'OK'

    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    # Tests

    @httpretty.activate
    def test_post_one(self):
        httpretty.register_uri(
            httpretty.POST, self.endpoint_url,
            status=self.status_code,
            content_type=self.content_type,
            body=self.content)
        self.given_a_file('todo/hello.txt', b'this is the message content')

        exit_code = main([self.dir_path, self.endpoint_url])

        self.then_should_post_to_server(b'this is the message content')
        self.then_exit_code_should_denote_success(exit_code)
        self.then_file_should_be_moved_to_done('hello.txt')


class EndToEndFailTests(EndToEndTestMixin, unittest.TestCase):
    endpoint_path = b'/path/to/endpoint.quux'
    endpoint_url = b'http://api.example.com' + endpoint_path
    status_code = 503
    content_type = b'text/plain'
    content = 'Nope'

    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    @httpretty.activate
    def test_fails_to_post_one(self, content='{"success":true}', content_type=None):
        httpretty.register_uri(
            httpretty.POST, self.endpoint_url,
            status=self.status_code,
            content_type=(content_type or self.content_type),
            body=(content or self.content))
        self.given_a_file('todo/hello.txt', b'spiffy paloo')

        exit_code = main([self.dir_path, self.endpoint_url])

        self.then_should_post_to_server(b'spiffy paloo')
        self.then_exit_code_should_denote_error(exit_code)
        self.then_file_should_be_left_in_todo('hello.txt')
