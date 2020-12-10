#!/usr/bin/env python3

import datetime
import glob
import json

import speedtest_auto


def main():
    for f in glob.glob('speedtest_auto_tests/*.json'):
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
    main()
