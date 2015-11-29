# -*- coding: UTF-8 -*-

import argparse

from dozup import DozupQueue, DozupPoster


def create_parser():
    parser = argparse.ArgumentParser('POST some files to a web service')
    parser.add_argument(
        'data_dir', metavar='PATH', type=str,
        help='root directory containing ‘todo’, ‘doing’ and ‘done’ directories')
    parser.add_argument(
        'url', metavar='URL', type=str,
        help='URL to send POST requests to')
    return parser


def main(argv):
    parser = create_parser()
    options = parser.parse_args(argv)

    queue = DozupQueue(options.data_dir)
    poster = DozupPoster(options.url)

    errors = []
    for task in queue.iter_tasks():
        is_ok = poster.post(task.name, task.input)
        if not is_ok:
            task.push_back()
            errors += poster.errors

    return errors
