# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import io
import json
import shutil
import tempfile
import unittest

import httpretty

from dozup import DozupPoster, DozupError


class PosterTestMixin(unittest.TestCase):
    status_code = 202
    endpoint_uri = 'http://example.com/drop/'
    content_type = 'application/json'
    content = json.dumps({'status': 'OK'})

    def setUp(self):
        super(PosterTestMixin, self).setUp()
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')
        self.poster = DozupPoster('http://example.com/drop/')

    def tearDown(self):
        shutil.rmtree(self.dir_path)
        super(PosterTestMixin, self).tearDown()

    def given_server_endpoint(self, content=None, content_type=None):
        httpretty.register_uri(
            httpretty.POST, self.endpoint_uri,
            status=self.status_code,
            content_type=(content_type or self.content_type),
            body=(content or self.content))

    def when_posting(self, file_name='name_of_file.txt', file_content=b'content of file'):
        strm = io.BytesIO(file_content)
        self.result = self.poster.post(file_name, strm)

    def then_error_should_be(self, expected):
        self.assertFalse(self.result)
        self.assertEqual(DozupError(self.status_code, expected), self.poster.errors[-1])


class PosterCreatedTests(PosterTestMixin, unittest.TestCase):
    status_code = 201

    @httpretty.activate
    def test_post_one_file(self):
        self.given_server_endpoint()

        self.when_posting(file_content=b'this is the message content')

        self.assertTrue(self.result)
        self.assertEqual(b'this is the message content', httpretty.last_request().body)
        self.assertEqual(b'POST', httpretty.last_request().method)
        self.assertEqual(b'/drop/', httpretty.last_request().path)


class PosterOKTests(PosterCreatedTests):
    status_code = 201


class PosterAcceptedTests(PosterCreatedTests):
    status_code = 202


class PosterUnreadyTests(PosterTestMixin, unittest.TestCase):
    status_code = 503
    status_reason = 'Service Unavailable'
    content_type = 'application/json'

    @httpretty.activate
    def test_retains_plain_text_error_message(self):
        self.given_server_endpoint('Sorry!', 'text/plain')

        self.when_posting()

        self.then_error_should_be('Sorry!')

    @httpretty.activate
    def test_retains_json_error_string(self):
        self.given_server_endpoint('{"error": "Not today, thank you!"}')

        self.when_posting()

        self.then_error_should_be('Not today, thank you!')

    @httpretty.activate
    def test_retains_json_error_object(self):
        self.given_server_endpoint('{"errors": [{"message": "Not today, thank you!"}]}')

        self.when_posting()

        self.then_error_should_be({"message": "Not today, thank you!"})

    @httpretty.activate
    def test_synthesizes_error_message_from_status_code_if_it_must(self):
        self.given_server_endpoint('{"flange": "heliotrope"}')

        self.when_posting()

        self.then_error_should_be(self.status_reason)


class PosterNotFoundTests(PosterUnreadyTests):
    status_code = 404
    status_reason = 'Not Found'


class PosterForbiddenTests(PosterUnreadyTests):
    status_code = 403
    status_reason = 'Forbidden'


class PosterInternalServerErrorTests(PosterUnreadyTests):
    status_code = 500
    status_reason = 'Internal Server Error'


class HalPosterUnreadyTests(PosterUnreadyTests):
    content_type = 'application/hal+json'
