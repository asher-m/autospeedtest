#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import matplotlib.pyplot as plt
import os


NAMES = ['boston', 'portland']
# divide be 1e5 to get mbps
BANDWIDTH_SCALE = 1e5
HOUR_DELTA = datetime.timedelta(hours=1)
TZ_OFFSET = datetime.timedelta(hours=4)


def main(overlayed=False, pname='speedtest_auto_tests.png', truncrange=False):
    fig = plt.figure(figsize=(12, 8))

    starttime = None
    stoptime = None

    cutidx = -1 * 24 * 3 * 3  # back 3 days

    for n in NAMES:
        time = []
        dl = []
        ul = []

        if not (starttime or stoptime):
            tstrt = datetime.datetime.strptime(sorted(glob.glob(f'speedtest_auto_tests/{n}*'))[cutidx:][0],  # so no problems if not exist
                                               os.path.join('speedtest_auto_tests', f'{n}_%Y-%m-%dT%H%M.json')) - HOUR_DELTA
            tstop = datetime.datetime.strptime(sorted(glob.glob(f'speedtest_auto_tests/{n}*'))[-1],
                                               os.path.join('speedtest_auto_tests', f'{n}_%Y-%m-%dT%H%M.json')) + HOUR_DELTA

            if (not starttime) or (tstrt < starttime):
                starttime = tstrt
                startday = tstrt.replace(
                    hour=0, minute=0, second=0, microsecond=0)
            if (not stoptime) or (tstop > tstop):
                stoptime = tstop

        # grab files and append
        for f in sorted(glob.glob(f'speedtest_auto_tests/{n}*')):
            with open(f, 'r') as fp:
                d = json.load(fp)

            # check because can fail
            if 'download' in d.keys() and 'upload' in d.keys() and 'bandwidth' in d['download'].keys() and 'bandwidth' in d['upload'].keys():
                if overlayed is False:
                    t = datetime.datetime.strptime(
                        d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') - TZ_OFFSET
                else:
                    t = ((datetime.datetime.strptime(
                        d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') - startday - TZ_OFFSET).total_seconds() % (60 * 60 * 24)) / (60 * 60)
                time.append(t)
                dl.append(d['download']['bandwidth'] / BANDWIDTH_SCALE)
                ul.append(d['upload']['bandwidth'] / BANDWIDTH_SCALE)

        # plot stuff
        if truncrange is False:
            plt.scatter(time, dl, label=f'{n} dl')
            plt.scatter(time, ul, label=f'{n} ul')
        else:
            plt.scatter(time[cutidx:], dl[cutidx:], label=f'{n} dl')
            plt.scatter(time[cutidx:], ul[cutidx:], label=f'{n} ul')

    plt.legend()
    if overlayed is False:
        plt.xlabel('Time (MM-DD HH)')
        plt.xlim(starttime, stoptime)
    else:
        plt.xlabel('Time of Day (Hour)')
        plt.xlim(0, 24)
        plt.gca().set_xticks(range(25))
    plt.ylabel('Throughput (mbps)')
    plt.gca().set_ylim(bottom=0)

    plt.grid()

    plt.tight_layout()
    plt.savefig(pname)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--overlayed', action='store_true',
                        help='overlay selected data into 24 hour period',
                        dest='overlayed')
    parser.add_argument('-t', '--truncate', action='store_true',
                        help='truncate visible data to most recent 72 hours',
                        dest='truncrange')
    parser.add_argument('pname', action='store', nargs='?',
                        default='speedtest_auto_tests.png',
                        help='filename to save speedtest plot')
    args = parser.parse_args()
    main(**vars(args))
