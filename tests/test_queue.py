# -*- coding: UTF-8 -*-

import errno
import os
import shutil
import tempfile
import unittest
import zipfile

from mock import patch

from dozup import DozupQueue


class OSTests(unittest.TestCase):
    # The intent here is to check that my stubbing of OS functions is realistic!
    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_raises_oserror_when_moving_nonexistent_file(self):
        self.given_queued_file()
        self.given_claimed_file()

        with self.assertRaises(OSError):
            self.when_claiming_file()

    def test_raises_oserror_with_errno_eexist(self):
        self.given_queued_file()
        self.given_claimed_file()

        try:
            self.when_claiming_file()
        except OSError, err:
            self.assertEqual(errno.EEXIST, err.errno)

    def given_queued_file(self):
        os.makedirs(os.path.join(self.dir_path, 'todo'))
        self.file_path = os.path.join(self.dir_path, 'todo', 'world.txt')
        with open(self.file_path, 'wb') as strm:
            strm.write('CONTENT')

    def when_claiming_file(self):
        os.makedirs(os.path.join(self.dir_path, 'doing'))
        self.new_path = os.path.join(self.dir_path, 'doing', 'world.txt')
        os.rename(self.file_path, self.new_path)
    given_claimed_file = when_claiming_file


class DozupQueueTests(unittest.TestCase):
    def setUp(self):
        self.dir_path = tempfile.mkdtemp('.test', 'DozupQueueTests.')
        self.dozup_queue = DozupQueue(self.dir_path)

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_returns_a_false_value_when_no_file(self):
        file_path = self.dozup_queue.find_file()

        self.assertFalse(file_path)

    def test_finds_toplevel_file(self):
        self.given_a_file('todo/florg.txt')

        file_path = self.dozup_queue.find_file()

        self.assertEqual('florg.txt', file_path)

    def test_finds_file_in_subdir(self):
        self.given_a_file('todo/bananafrappe/eagle-claww.txt')

        file_path = self.dozup_queue.find_file()

        self.assertEqual('bananafrappe/eagle-claww.txt', file_path)

    def test_moves_file_to_doing_folder_when_claimed(self):
        self.given_a_file('todo/bananafrappe/eagle-claww.txt')

        self.when_claiming_file()

        self.assertEqual('bananafrappe/eagle-claww.txt', self.file_path)
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, "doing", self.file_path)))
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, "todo", self.file_path)))

    def test_retries_if_file_it_wants_to_claim_is_snatched_away(self):
        self.given_a_file('todo/bananafrappe/eagle-claww.txt')

        self.when_claiming_file_but_a_concurrent_thread_snatches_the_first_away()

        self.assertEqual('lemonsundae/sock.txt', self.file_path)
        self.then_file_should_be_claimed(self.file_path)

    def test_yields_file_names_and_streams_from_files(self):
        self.given_a_file('todo/foo/bar.txt', 'content of bar')
        self.given_a_zip_archive('todo/b/ar000001.zip', [
            ('ar000001/bee.txt', 'forst'),
            ('ar000001/cat.txt', 'seknd'),
        ])

        self.when_iterating_over_tasks()

        self.then_tasks_should_have_names_and_contents(set([
            ('foo/bar.txt', 'content of bar'),
            ('b/ar000001.zip/ar000001/bee.txt', 'forst'),
            ('b/ar000001.zip/ar000001/cat.txt', 'seknd'),
        ]))
        self.then_file_should_be_done('foo/bar.txt')
        self.then_file_should_be_done('b/ar000001.zip')

    def test_pushes_file_back_to_todo_if_task_pushed_back(self):
        self.given_a_file('todo/foo/bar.txt', 'content of bar')
        self.given_a_file('todo/foo/baz.txt', 'content of baz')

        self.when_iterating_over_tasks_pushing_them_back()

        self.then_tasks_should_have_names_and_contents(set([
            ('foo/bar.txt', 'content of bar'),
        ]))
        self.then_file_should_be_todo('foo/bar.txt')
        self.then_file_should_be_todo('foo/baz.txt')

    def test_pushes_file_back_to_todo_if_task_pushed_back_zip(self):
        self.given_a_zip_archive('todo/ar0000/ar000001.zip', [
            ('ar000001/bee.txt', 'forst'),
            ('ar000001/cat.txt', 'seknd'),
        ])

        self.when_iterating_over_tasks_pushing_them_back()

        self.then_tasks_should_have_names_and_contents(set([
            ('ar0000/ar000001.zip/ar000001/bee.txt', 'forst'),
        ]))
        self.then_file_should_be_todo('ar0000/ar000001.zip')

    # Helpers

    def create_a_file(self, relative_path, content=''):
        subdir_path = os.path.join(self.dir_path, os.path.dirname(relative_path))
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
        with open(os.path.join(self.dir_path, relative_path), 'wb') as strm:
            strm.write(content)
    given_a_file = create_a_file

    def given_a_zip_archive(self, relative_path, file_name_contents):
        os.makedirs(os.path.join(self.dir_path, os.path.dirname(relative_path)))
        with open(os.path.join(self.dir_path, relative_path), 'wb') as strm:
            archive = zipfile.ZipFile(strm, 'w', zipfile.ZIP_DEFLATED)
            for file_name, contents in file_name_contents:
                archive.writestr(file_name, contents.encode('UTF-8'))
            archive.close()

    def when_claiming_file(self):
        self.file_path = self.dozup_queue.claim_file()

    def when_claiming_file_but_a_concurrent_thread_snatches_the_first_away(self):
        # The idea in the following is that another concurrent process claims
        # the file between the call to find_file and os.rename.
        real_rename = os.rename
        spoo = {'first': True}

        def snatched_away(src_path, dst_path):
            if spoo['first']:
                # Pretend the following happend on another thread:
                real_rename(src_path, dst_path)
                self.create_a_file('todo/lemonsundae/sock.txt')
                spoo['first'] = False
            real_rename(src_path, dst_path)

        with patch.object(os, 'rename') as mock_rename:
            mock_rename.side_effect = snatched_away
            self.file_path = self.dozup_queue.claim_file()

    def when_iterating_over_tasks(self):
        self.tasks = set()
        for task in self.dozup_queue.iter_tasks():
            self.tasks.add((task, task.input.read()))

    def when_iterating_over_tasks_pushing_them_back(self):
        self.tasks = set()
        for task in self.dozup_queue.iter_tasks():
            self.tasks.add((task, task.input.read()))
            task.push_back()

    def then_file_should_be_claimed(self, file_path):
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, "todo", file_path)))
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, "doing", file_path)))

    def then_file_should_be_done(self, file_path):
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, "doing", file_path)))
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, "done", file_path)))

    def then_file_should_be_todo(self, file_path):
        self.assertFalse(os.path.exists(os.path.join(self.dir_path, "doing", file_path)))
        self.assertTrue(os.path.exists(os.path.join(self.dir_path, "todo", file_path)))

    def then_tasks_should_have_names_and_contents(self, expected_filename_contents):
        actual_filename_contents = set((task.name, content) for task, content in self.tasks)
        self.assertEqual(expected_filename_contents, actual_filename_contents)
