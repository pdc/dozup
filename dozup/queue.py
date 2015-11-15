# -*- coding: UTF-8 -*-


"""Test for the dozup package.

Run with something like the following:

    python -m unittest tests.test_dozup
"""


import errno
import os


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
            strm = open(os.path.join(self.doing_dir, file_path), 'rb')
            yield file_path, strm
            strm.close()
