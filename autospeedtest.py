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


# "user-editable" script parameters
PERIOD = 20  # periodicity of tests in minutes
WAIT_TO_REMOVE = 180  # time to wait to remove halt file in minutes
SITES = {  # sites to test
    # 1037: 'Portland Otelco',
    1774: 'Boston Comcast',
    17193: 'Burlington Telecom'
}


# database connection
if not os.path.exists('speedtests.db'):
    import autospeedtest_createdb
    autospeedtest_createdb.main()
CONN = sqlite3.connect('speedtests.db')
# test params
COMMAND_PROTO = r"speedtest -f json -s {}"  # test command prototype
# plot params
BANDWIDTH_SCALE = 1e5  # divide be 1e5 to get mbps
HOUR_DELTA = datetime.timedelta(hours=1)
# date format
DATEFORMAT = "%Y-%m-%dT%H-%M-%S"


def get_site_name(s):
    return SITES[s] if s in SITES else f'serverid {s}'


def test():
    for s in SITES:
        print(f'Testing {get_site_name(s)}...')
        try:
            out, _ = subprocess.Popen(
                COMMAND_PROTO.format(s).split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate(
                timeout=60  # timeout after 60 seconds
            )
            dump(s, out)
        except Exception as e:
            print(f'There was a problem when testing {SITES[s]} at'
                  f' {datetime.datetime.now().strftime(DATEFORMAT)}:'
                  f'\n\t{type(e).__module__}.{type(e).__name__}: {str(e)}')


def dump(site, result_as_str, timestamp=None):
    # get timestamp
    if timestamp:
        assert isinstance(timestamp, datetime.datetime)
    else:
        timestamp = datetime.datetime.now()
    # get result
    result = json.loads(result_as_str)
    # assemble data
    data = (
        timestamp.strftime(DATEFORMAT),
        site,
        result_as_str,
        result['ping']['latency'] if 'ping' in result and 'latency' in result['ping'] else None,
        result['ping']['jitter'] if 'ping' in result and 'jitter' in result['ping'] else None,
        result['download']['bandwidth'] if 'download' in result and 'bandwidth' in result['download'] else None,
        result['upload']['bandwidth'] if 'upload' in result and 'bandwidth' in result['download'] else None,
        result['packetLoss'] if 'packetLoss' in result else None
    )

    cur = CONN.cursor()
    cur.execute('INSERT INTO tests VALUES (?,?,?,?,?,?,?,?)', data)
    CONN.commit()


def plot_bandwidth(pname, overlayed=False, trunced=False):
    # make figure
    _, axes = plt.subplots(2, 1, figsize=(12, 8),
                           sharex=True, sharey=True, dpi=300)
    ax1, ax2 = axes
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

    for s in np.unique(tests['site']):
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

        # plot download
        if not np.all(np.isnan(tests_site['dl'][cutidx:])):
            ax1.scatter(
                tests_site['date'][cutidx:],
                tests_site['dl'][cutidx:] / BANDWIDTH_SCALE,
                label=f'{get_site_name(s)}'
            )

        # plot upload
        if not np.all(np.isnan(tests_site['ul'][cutidx:])):
            ax2.scatter(
                tests_site['date'][cutidx:],
                tests_site['ul'][cutidx:] / BANDWIDTH_SCALE,
                label=f'{get_site_name(s)}'
            )

    # plot start/stop time
    if trunced:
        strtidx = np.searchsorted(
            tests['date'], tests['date'][-1] - datetime.timedelta(days=3))
    else:
        strtidx = 0
    strttime = tests['date'][strtidx] - HOUR_DELTA
    stoptime = tests['date'][-1] + HOUR_DELTA

    # finish plot
    ax1.legend(loc=2)
    ax1.set_ylabel('Download Throughput (mbps)')
    ax1.set_ylim(bottom=0)
    ax1.grid(True)
    ax2.legend(loc=2)
    ax2.set_ylabel('Upload Throughput (mbps)')
    ax2.set_ylim(bottom=0)
    ax2.grid(True)

    if overlayed is False:
        ax2.set_xlabel('Date')
        ax2.set_xlim(strttime, stoptime)
    else:
        ax2.set_xlabel('Time of Day (Hour)')
        ax2.set_xlim(0, 24)
        ax2.set_xticks(range(25))

    plt.tight_layout()
    plt.savefig(pname)
    plt.close()


def plot_ping(pname, overlayed=False, trunced=False):
    # make figure
    _, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, dpi=300)
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

    for s in np.unique(tests['site']):
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
        if not np.all(np.isnan(tests_site['latency'][cutidx:])):
            ax1.scatter(
                tests_site['date'][cutidx:],
                tests_site['latency'][cutidx:],
                label=f'{get_site_name(s)} latency'
            )

        # plot packetloss
        if not np.all(np.isnan(tests_site['packetloss'][cutidx:])):
            ax2.scatter(
                tests_site['date'][cutidx:],
                tests_site['packetloss'][cutidx:],
                label=f'{get_site_name(s)} packetloss'
            )

    # plot start/stop time
    if trunced:
        strtidx = np.searchsorted(
            tests['date'], tests['date'][-1] - datetime.timedelta(days=3))
    else:
        strtidx = 0
    strttime = tests['date'][strtidx] - HOUR_DELTA
    stoptime = tests['date'][-1] + HOUR_DELTA

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
        ax2.set_xlabel('Date')
        ax2.set_xlim(strttime, stoptime)
    else:
        ax2.set_xlabel('Time of Day (Hour)')
        ax2.set_xlim(0, 24)
        ax2.set_xticks(range(25))

    plt.tight_layout()
    plt.savefig(pname)
    plt.close()


def do_plots():
    # plot
    print('Plotting...')

    # regular plots
    plot_bandwidth('bandwidth.png')
    plot_bandwidth('bandwidth-recent.png', trunced=True)
    plot_bandwidth('tod-bandwidth.png', overlayed=True)
    plot_bandwidth('tod-bandwidth-recent.png', overlayed=True, trunced=True)  # nopep8

    # latency plots
    plot_ping('latency.png')
    plot_ping('latency-recent.png', trunced=True)
    plot_ping('tod-latency.png', overlayed=True)
    plot_ping('tod-latency-recent.png', overlayed=True, trunced=True)  # nopep8


def main():
    halted = None
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    wait_delta = datetime.timedelta(minutes=PERIOD)
    wait_to_remove_delta = datetime.timedelta(minutes=WAIT_TO_REMOVE)

    # sanity checks
    # must test more than once per day (timedelta.seconds breaks if not)
    assert(wait_delta < datetime.timedelta(days=1))
    # must not try ot remove halt file more than testing
    assert(wait_delta < wait_to_remove_delta)

    # start with a test
    test()
    do_plots()

    # then start testing repeatedly
    while True:
        now = datetime.datetime.now()
        # calculate how much time to wait until next interval
        wait = wait_delta - ((now - today) % wait_delta)
        # calculate random waiting time
        wait_more = datetime.timedelta(
            seconds=random.randint(0, wait_delta.seconds))
        print(f'Waiting until {now + wait + wait_more} for next test...')
        time.sleep(wait.seconds + wait_more.seconds)

        # if we shouldn't pause
        if not os.path.exists('./halt'):
            # do the tests again
            test()
            do_plots()
            pass
        else:
            print('Halt file exists.  Not running test...')
            if not halted:
                halted = datetime.datetime.now()  # so we know when to delete the halt file

            if datetime.datetime.now() - halted > datetime.timedelta(minutes=WAIT_TO_REMOVE):
                halted = None
                os.remove('./halt')
            else:
                w = wait_to_remove_delta - (datetime.datetime.now() - halted)
                print(f'Waiting for another {w.seconds} seconds '
                      'until removing halt file...')

        # wait in all cases for good measure (usually problems if not)
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
