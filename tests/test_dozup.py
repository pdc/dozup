# -*- coding: UTF-8 -*-

import os
import shutil
import tempfile
import unittest

from dozup import DozupQueue


class DozupQueueTests(unittest.TestCase):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_finds_toplevel_file(self):
        dozup_queue = DozupQueue(self.dir_path)
        self.given_a_file('todo/florg.txt')

        file_path = dozup_queue.find_file()

        self.assertEqual('florg.txt', file_path)

    def test_finds_file_in_subdir(self):
        dozup_queue = DozupQueue(self.dir_path)
        self.given_a_file('todo/bananafrappe/eagle-claww.txt')

        file_path = dozup_queue.find_file()

        self.assertEqual('bananafrappe/eagle-claww.txt', file_path)

    def test_moves_file_to_doing_folder_when_claimed(self):
        dozup_queue = DozupQueue(self.dir_path)
        self.given_a_file('todo/bananafrappe/eagle-claww.txt')

        file_path = dozup_queue.claim_file()

        self.assertEqual('bananafrappe/eagle-claww.txt', file_path)
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, "doing", file_path)))
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, "todo", file_path)))

    def given_a_file(self, relative_path, content=''):
        os.makedirs(os.path.join(self.dir_path, os.path.dirname(relative_path)))
        with open(os.path.join(self.dir_path, relative_path), 'wb') as strm:
            strm.write(content)
