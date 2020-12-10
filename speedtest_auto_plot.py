#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import matplotlib.pyplot as plt
import os
import time

from speedtest_auto import SITES

# divide be 1e5 to get mbps
BANDWIDTH_SCALE = 1e5
HOUR_DELTA = datetime.timedelta(hours=1)
# Not awesome, but we need UTC offset:
TZ_OFFSET = datetime.datetime.fromtimestamp(time.mktime(
    time.localtime())) - datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))


def main(overlayed=False, pname='speedtest_auto_tests.png', truncrange=False):
    plt.figure(figsize=(12, 8))

    starttime = None
    stoptime = None

    cutidx = -1 * 24 * 3 * 3  # back 3 days

    for s in SITES:
        time = []
        dl = []
        ul = []

        if not (starttime or stoptime):
            if truncrange is False:
                fname_strt = sorted(glob.glob(f'speedtest_auto_tests/{s}*'))[0]
            else:
                fname_strt = sorted(
                    glob.glob(f'speedtest_auto_tests/{s}*'))[cutidx:][0]
            with open(fname_strt, 'r') as fp:
                d = json.load(fp)
            tstrt = datetime.datetime.strptime(
                d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') - HOUR_DELTA + TZ_OFFSET

            fname_tstop = sorted(glob.glob(f'speedtest_auto_tests/{s}*'))[-1]
            with open(fname_tstop, 'r') as fp:
                d = json.load(fp)
            tstop = datetime.datetime.strptime(
                d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') + HOUR_DELTA + TZ_OFFSET

            if (not starttime) or (tstrt < starttime):
                starttime = tstrt
                startday = tstrt.replace(
                    hour=0, minute=0, second=0, microsecond=0)
            if (not stoptime) or (tstop > stoptime):
                stoptime = tstop

        # grab files and append
        for f in sorted(glob.glob(f'speedtest_auto_tests/{s}*')):
            with open(f, 'r') as fp:
                d = json.load(fp)

            # check because can fail
            if 'download' in d.keys() and 'upload' in d.keys() and 'bandwidth' in d['download'].keys() and 'bandwidth' in d['upload'].keys():
                if overlayed is False:
                    t = datetime.datetime.strptime(
                        d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') + TZ_OFFSET
                else:
                    t = ((datetime.datetime.strptime(
                        d['timestamp'], f'%Y-%m-%dT%H:%M:%SZ') - startday + TZ_OFFSET).total_seconds() % (60 * 60 * 24)) / (60 * 60)
                time.append(t)
                dl.append(d['download']['bandwidth'] / BANDWIDTH_SCALE)
                ul.append(d['upload']['bandwidth'] / BANDWIDTH_SCALE)

        # plot stuff
        if truncrange is False:
            plt.scatter(time, dl, label=f'{SITES[s]} dl')
            plt.scatter(time, ul, label=f'{SITES[s]} ul')
        else:
            plt.scatter(time[cutidx:], dl[cutidx:], label=f'{SITES[s]} dl')
            plt.scatter(time[cutidx:], ul[cutidx:], label=f'{SITES[s]} ul')

    plt.legend()
    if overlayed is False:
        plt.xlabel('UTC Time (MM-DD HH)')
        plt.xlim(starttime, stoptime)
    else:
        plt.xlabel('UTC Time of Day (Hour)')
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
