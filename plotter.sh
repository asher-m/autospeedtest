#!/bin/bash
python speedtest_auto_plot.py -o speedtest_auto_tests-overlayed.png
python speedtest_auto_plot.py -ot speedtest_auto_tests-overlayed-trunced.png
python speedtest_auto_plot.py -t speedtest_auto_tests-trunced.png
python speedtest_auto_plot.py speedtest_auto_tests.png
