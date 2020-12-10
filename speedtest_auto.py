#!/usr/bin/env python3

import argparse
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import random
import sqlite3
import subprocess
import time


if not os.path.exists('speedtests.db'):
    import speedtest_createdb
    speedtest_createdb.main()
# database connection
CONN = sqlite3.connect('speedtests.db')

# test params
PERIOD = 20  # periodicity of tests in minutes
COMMAND_PROTO = r"speedtest -f json -s {}"  # test command prototype
SITES = {  # sites to test
    1774: 'Boston Comcast',
    17193: 'Burlington Telecom'
}

# plot params
BANDWIDTH_SCALE = 1e5  # divide be 1e5 to get mbps
HOUR_DELTA = datetime.timedelta(hours=1)

# date format
DATEFORMAT = "%Y-%m-%dT%H-%M-%S"


def test():
    for s in SITES:
        print(f'Testing {SITES[s]}...')
        out, _ = subprocess.Popen(COMMAND_PROTO.format(s).split(),
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE).communicate()
        dump(s, out)


def dump(site, rawout, timestamp=None):
    if timestamp:
        assert isinstance(timestamp, datetime.datetime)
    else:
        timestamp = datetime.datetime.now()
    result = json.loads(rawout)
    data = (
        timestamp.strftime(DATEFORMAT),
        site,
        rawout,
        result['ping']['latency'] if 'ping' in result and 'latency' in result['ping'] else None,
        result['ping']['jitter'] if 'ping' in result and 'jitter' in result['ping'] else None,
        result['download']['bandwidth'] if 'download' in result and 'bandwidth' in result['download'] else None,
        result['upload']['bandwidth'] if 'upload' in result and 'bandwidth' in result['download'] else None,
        result['packetLoss'] if 'packetLoss' in result else None
    )

    cur = CONN.cursor()
    cur.execute('INSERT INTO tests VALUES (?,?,?,?,?,?,?,?)', data)
    CONN.commit()


def plot_bandwidth(overlayed=False, trunced=False, pname='speedtest_auto_bandwidth_tests.png'):
    # make figure
    plt.figure(figsize=(12, 8))
    # open db and read
    cur = CONN.cursor()
    cur.execute('SELECT date, site, dl_bandwidth, ul_bandwidth FROM tests')
    tests_strdate = np.array(
        cur.fetchall(),
        dtype=[('date', 'U64'), ('site', int), ('dl', float), ('ul', float)]
    )

    # convert to dated
    data = [(datetime.datetime.strptime(t, DATEFORMAT), s, dl, ul)
            for t, s, dl, ul in tests_strdate]
    dtype = [('date', datetime.datetime),
             ('site', int), ('dl', float), ('ul', float)]
    # make array
    tests = np.sort(np.array(data, dtype=dtype), order='date')

    for s in SITES:
        # get site data
        tests_site = tests[tests['site'] == s]
        # skip if no data for site
        if len(tests_site) < 1:
            continue

        # if trunced
        if trunced is True:
            # get plot index
            cutidx = np.searchsorted(
                tests_site['date'],
                tests_site['date'][-1] - datetime.timedelta(days=3)
            )
        else:
            cutidx = 0

        # get startday for overlayed datetime modulus
        if overlayed is True:
            startday = datetime.datetime.combine(
                tests_site['date'][cutidx].date(),
                datetime.time()
            )
            tests_site['date'] = [((t - startday).total_seconds() % (60 * 60 * 24))
                                  / (60 * 60) for t in tests_site['date']]  # not great with typing, but works

        # plot
        plt.scatter(
            tests_site['date'][cutidx:],
            tests_site['dl'][cutidx:] / BANDWIDTH_SCALE,
            label=f'{SITES[s]} dl'
        )
        plt.scatter(
            tests_site['date'][cutidx:],
            tests_site['ul'][cutidx:] / BANDWIDTH_SCALE,
            label=f'{SITES[s]} ul'
        )

    # plot start/stop time
    strttime = np.min(tests['date']) - HOUR_DELTA
    stoptime = np.max(tests['date']) + HOUR_DELTA

    # finish plot
    plt.legend(loc=2)
    if overlayed is False:
        plt.xlabel('UTC Time (MM-DD HH)')
        plt.xlim(strttime, stoptime)
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


def plot_ping(overlayed=False, trunced=False, pname='speedtest_auto_latency_tests.png'):
    colors_latency = ['blue', 'green']
    colors_packetloss = ['red', 'orange']
    # make figure
    _, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    ax1, ax2 = axes
    # open db and read
    cur = CONN.cursor()
    cur.execute('SELECT date, site, packetloss, latency, jitter FROM tests')
    tests_strdate = np.array(
        cur.fetchall(),
        dtype=[('date', 'U64'), ('site', int), ('packetloss', float),
               ('latency', float), ('jitter', float)]
    )

    # convert to dated
    data = [(datetime.datetime.strptime(t, DATEFORMAT), s, p, l, j)
            for t, s, p, l, j in tests_strdate]
    dtype = [('date', datetime.datetime), ('site', int), ('packetloss', float),
             ('latency', float), ('jitter', float)]
    # make array
    tests = np.sort(np.array(data, dtype=dtype), order='date')

    for j, s in enumerate(SITES):
        # get site data
        tests_site = tests[tests['site'] == s]
        # skip if no data for site
        if len(tests_site) < 1:
            continue

        # if trunced
        if trunced is True:
            # get plot index
            cutidx = np.searchsorted(
                tests_site['date'],
                tests_site['date'][-1] - datetime.timedelta(days=3)
            )
        else:
            cutidx = 0

        # get startday for overlayed datetime modulus
        if overlayed is True:
            startday = datetime.datetime.combine(
                tests_site['date'][cutidx].date(),
                datetime.time()
            )
            tests_site['date'] = [((t - startday).total_seconds() % (60 * 60 * 24))
                                  / (60 * 60) for t in tests_site['date']]  # not great with typing, but works

        # plot latency
        ax1.scatter(
            tests_site['date'],
            tests_site['latency'],
            color=colors_latency[j],
            label=f'{SITES[s]} latency'
        )

        # plot packetloss
        if not np.all(np.isnan(tests_site['packetloss'])):
            ax2.scatter(
                tests_site['date'],
                tests_site['packetloss'],
                color=colors_packetloss[j],
                label=f'{SITES[s]} packetloss'
            )

    # plot start/stop time
    strttime = np.min(tests['date']) - HOUR_DELTA
    stoptime = np.max(tests['date']) + HOUR_DELTA

    # finish plot
    ax1.legend(loc=2)
    ax1.set_ylabel('Ping (ms)')
    ax1.set_ylim(bottom=0)
    ax1.grid(True)
    ax2.legend(loc=2)
    ax2.set_ylabel('Packetloss (percentage)')
    ax2.set_ylim(bottom=0)
    ax2.grid(True)

    if overlayed is False:
        ax2.set_xlabel('UTC Time (MM-DD HH)')
        ax2.set_xlim(strttime, stoptime)
    else:
        ax2.set_xlabel('UTC Time of Day (Hour)')
        ax2.set_xlim(0, 24)
        ax2.set_xticks(range(25))

    plt.tight_layout()
    plt.savefig(pname)
    plt.close()


def do_plots():
    # plot
    print('Plotting...')

    # regular plots
    plot_bandwidth()
    plot_bandwidth(overlayed=True,
         pname='speedtest_auto_bandwidth_tests-overlayed.png')
    plot_bandwidth(trunced=True,
         pname='speedtest_auto_bandwidth_tests-trunced.png')
    plot_bandwidth(overlayed=True, trunced=True,
         pname='speedtest_auto_bandwidth_tests-overlayed-trunced.png')

    # latency plots
    plot_ping()
    plot_ping(overlayed=True,
        pname='speedtest_auto_latency_tests-overlayed.png')
    plot_ping(trunced=True,
        pname='speedtest_auto_latency_tests-trunced.png')
    plot_ping(overlayed=True, trunced=True,
        pname='speedtest_auto_latency_tests-overlayed-trunced.png')

def main():
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    wait_delta = datetime.timedelta(minutes=PERIOD)

    # start with a test
    test()
    do_plots()

    # then start testing repeatedly
    while True:
        # get now again
        now = datetime.datetime.now()

        # calculate how long to wait for until next 20 minute interval and wait
        wait = wait_delta - ((now - today) % wait_delta)
        print(f'Waiting until {now + wait} for next test...')
        time.sleep(wait.seconds)

        # random waiting time
        wait_more = random.randint(0, 20 * 60)
        wait_more_td = datetime.timedelta(seconds=wait_more)
        print(f'Waiting an additional {wait_more} seconds '
              f'for random test population (until {now + wait + wait_more_td})...')
        time.sleep(wait_more)

        # if we shouldn't pause
        if not os.path.exists('speedtest_auto_tests/halt'):
            # do the tests again
            test()

            # do plots
            do_plots()

        else:
            print('Halt file exists.  Not running test...')
            time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run automated speedtests on your internet.\n\nDefault (no options)'
        ' is to run immediately then again at random times in every 20 minute interval.'
        '  Plots are also made after every test in the default mode.\n\nOptions can be'
        ' used to run one-off tests or plot.\n\nAny arguments are ignored if neither'
        'a one-off test or plot are indicated.'
    )
    parser.add_argument('-t', '--test', action='store_true',
                        help='run a one-off test', dest='test')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='make plots then close', dest='plot')
    kwargs = vars(parser.parse_args())
    if kwargs['plot'] is True:
        do_plots()
    elif kwargs['test'] is True:
        test()
    else:
        main()
