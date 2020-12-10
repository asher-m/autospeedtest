#!/usr/bin/env python3

import datetime
import json
import os
import random
import subprocess
import time

import speedtest_auto_plot as plot


# periodicity of tests in minutes
PERIOD = 20
COMMAND_PROTO = r"speedtest -f json -s {}"
SITES = {
    1774: 'Boston Comcast',
    17193: 'Burlington Telecom'
}


def test(when):
    for s in SITES:
        out, _ = subprocess.Popen(COMMAND_PROTO.format(s).split(),
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE).communicate()
        dump(when, out, s)


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
    wait_delta = datetime.timedelta(minutes=PERIOD)

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
