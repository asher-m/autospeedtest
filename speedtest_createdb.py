#!/usr/bin/env python3

import datetime
import os
import shutil
import sqlite3


def main():
    maketable = """CREATE TABLE tests (
            date TEXT NOT NULL,
            site INTEGER,
            raw TEXT,
            latency REAL,
            jitter REAL,
            dl_bandwidth INTEGER,
            ul_bandwidth INTEGER,
            packetloss REAL
        )"""

    # Back up old db:
    if os.path.exists('speedtests.db'):
        shutil.move(
            'speedtests.db',
            f'speedtests.db.{datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")}.back'
        )

    d = sqlite3.connect('speedtests.db')
    c = d.cursor()

    c.execute(maketable)

    d.commit()
    d.close()


if __name__ == '__main__':
    main()
