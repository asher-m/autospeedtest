#!/usr/bin/env python3

import datetime
import json
import os
import random
import subprocess
import time

import speedtest_auto_plot as plot


# time to wait in minutes
WAIT = 20

# command to execute
COMMAND_BOS = """speedtest -f json -s 1774"""  # 1774 is Boston Comcast
# COMMAND_POR = """speedtest -f json -s 1037"""  # 1037 is Portland Otelco; no longer online
COMMAND_BUR = """speedtest -f json -s 17193"""  # 17193 is Burlington Telecom


def test(when):
    print('Testing Boston Comcast...')
    out, err = subprocess.Popen(COMMAND_BOS.split(),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE).communicate()
    dump(when, out, 'boston')

    print('Testing Burlington Telecom...')
    out, err = subprocess.Popen(COMMAND_BUR.split(),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE).communicate()
    dump(when, out, 'burlington')


def dump(when, out, pref):
    try:
        d = json.loads(out)
        with open(f'speedtest_auto_tests/{pref}_{when.strftime("%FT%H%M")}.json', 'w') as fp:
            json.dump(d, fp)
    except:
        pass


def main():
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    wait_delta = datetime.timedelta(minutes=WAIT)

    # start with a test
    test(now)

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
            test(now + wait + wait_more_td)

            # plot
            print('Plotting...')
            plot.main()
            plot.main(overlayed=True, pname='speedtest_auto_tests-overlayed.png')
            plot.main(truncrange=True, pname='speedtest_auto_tests-trunced.png')
            plot.main(overlayed=True, truncrange=True,
                      pname='speedtest_auto_tests-overlayed-trunced.png')

        else:
            print('Halt file exists.  Not running test...')
            time.sleep(3)


if __name__ == '__main__':
    main()
