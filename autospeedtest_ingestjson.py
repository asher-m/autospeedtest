#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import os

import speedtest_auto


def main(searchdir=None):
    globhere = 'speedtest_auto_tests/*.json'
    if searchdir and os.path.isdir(searchdir):
        globhere = os.path.join(searchdir, '*.json')
        print(f'Looking at the following directory for speedtest-cli json files:\n{globhere}')
    for f in glob.glob(globhere):
        with open(f, 'r') as fp:
            line = fp.readline()
            d = json.loads(line)

        if not 'server' in d:
            continue
        else:
            speedtest_auto.dump(
                d['server']['id'],
                line,
                datetime.datetime.strptime(
                    d['timestamp'], "%Y-%m-%dT%H:%M:%SZ"
                ) - datetime.timedelta(hours=5)
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('searchdir', action='store', nargs='?', default=None,
                        help='directory to search for speedtest-cli json files')
    kwargs = vars(parser.parse_args())
    main(**kwargs)
