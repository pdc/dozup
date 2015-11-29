# -*- coding: UTF-8 -*-


"""Test for the dozup package.

Run with something like the following:

    python -m unittest tests.test_dozup
"""


import errno
import os
import zipfile


class Task(object):
    """One file to post to the server."""
    is_pushed_back = False

    def __init__(self, name, input_stream):
        self.name = name
        self.input = input_stream

    def push_back(self):
        self.is_pushed_back = True


class DozupQueue(object):
    """A queue backed by a directory structure.

    The contents of todo are:
    - files representing tasks
    - zip archives containing task files
    - subdirectories containing task files or zip archives.

    A task file or zip archive is ‘claimed’ by moving it to
    the `doing` directory. Once processed, it goes to the
    `done` directory, preserving subdirectory structure.

    """
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.todo_dir = os.path.join(dir_path, 'todo')
        self.doing_dir = os.path.join(dir_path, 'doing')
        self.done_dir = os.path.join(dir_path, 'done')

    def find_file(self):
        """Return a file from the TODO directory.

        This will not necessarily correspond to a single task.
        """
        for dir_path, subdirs, files in os.walk(self.todo_dir):
            if files:
                file_path = os.path.join(dir_path, files[0])
                return os.path.relpath(file_path, self.todo_dir)

    def claim_file(self):
        """Transfer a file from `todo` to `doing`.

        The idea is to claim the file for processing by this process, in a way
        that is safe from concurrent scripts operating on the same dir.

        Returns --
            file path relative to the `doing` directory.
        """
        while True:
            file_path = self.find_file()
            if not file_path:
                break
            os.makedirs(os.path.join(self.doing_dir, os.path.dirname(file_path)))
            try:
                # The following is an atomic operation.
                os.rename(os.path.join(self.todo_dir, file_path), os.path.join(self.doing_dir, file_path))
                return file_path
            except OSError as err:
                if err.errno in (errno.ENOENT, ):
                    # Another process has snatched this file away from us.
                    pass
                else:
                    raise

    def iter_tasks(self):
        while True:
            file_path = self.claim_file()
            if not file_path:
                break
            is_pushed_back = False
            if file_path.endswith('.zip'):
                archive = zipfile.ZipFile(os.path.join(self.doing_dir, file_path), 'r')
                for info in archive.infolist():
                    task = Task(file_path + '/' + info.filename, archive.open(info))
                    yield task
                    if task.is_pushed_back:
                        is_pushed_back = True
                        break
                archive.close()
            else:
                strm = open(os.path.join(self.doing_dir, file_path), 'rb')
                task = Task(file_path, strm)
                yield task
                strm.close()
                if task.is_pushed_back:
                    is_pushed_back = True
            if is_pushed_back:
                os.rename(os.path.join(self.doing_dir, file_path), os.path.join(self.todo_dir, file_path))
                break
            else:
                os.makedirs(os.path.join(self.done_dir, os.path.dirname(file_path)))
                os.rename(os.path.join(self.doing_dir, file_path), os.path.join(self.done_dir, file_path))
