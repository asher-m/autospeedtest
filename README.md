# Autospeedtest
A small software suite to periodically test and plot your internet speed (to make sure your ISP is honest).

You'll need [Ookla's Speedtest CLI](https://www.speedtest.net/apps/cli) to use this software.


## Usage
Most simply, the user can open a `screen` and launch the script with args to automatically test every 20 minutes and plot, like:
```
$ screen
$ python autospeedtest.py
```
The script can be stopped at any time by touching `halt` in the script directory, (or the directory from which the script was called.  Touching `halt` will not interrupt a test if it is currently ongoing but it will interrupt any future test until `WAIT_TO_REMOVE` time has passed).


### Script options
The script contains a number of options to allow the user to customize the frequency and site of test.

The `PERIOD` variable controls the approximate period between tests.  Specifically, the script tries to run a test (or tests) in every `PERIOD`-minute interval throughout the day.  Then, to avoid potential conflict with other scheduled network activities (even others outside the local network), the script adds \[0,`PERIOD`) time before starting the test in each time interval.

The `WAIT_TO_REMOVE` variable specifies how long the script should wait before automatically removing the `halt` file.  This functionality is included in case the user forgets to resume the test.

The `SITES` variable is a dictionary containing the Ookla server IDs and a description of each testing location.  Users can add or remove entries to this dictionary to change the servers with which they test.  For plots, if a server is found in the results database that cannot be found in the `SITES` dictionary, its server ID will be used in its place.


### Commandline options
Beyond in-script options, commandline args allow the user to run one-off tests and plots.

For testing:
```
$ python autospeedtest.py -t
```
For plotting:
```
$ python autospeedtest.py -p
```
The user can use these options to set up cron jobs for testing and plotting if leaving open a `screen` is undesireable.

## Other scripts
This tool also includes two other scripts: `autospeedtest_ingestjson.py` and `autospeedtest_createdb.py`.

The `autospeedtest_createdb.py` script is used to create a database for results.  It is called automatically if a database cannot be found, or if explicitly called it will backup any existing databases before creating a new one.

The `autospeedtest_ingestjson.py` is a tool used to migrate old results in json format to the new database format.


## Result Format
There are 3 switches that allow the user to create plots to show internet experience.


### Result type: `bandwidth` or `latency`

These plots show funamentally different statistics about the user's internet experience.  The bandwidth plots show raw serial throughput on the connection (like what one might see if downloading a file or watching online video) while the latency plot shows ping and packetloss statistics.

Here is a time-of-day `bandwidth` plot, appearing as `bandwidth` in the filename:

![tod-bandwidth](https://github.com/asher-m/autospeedtest/raw/master/samples/tod-bandwidth.png)

Notice that download speeds are signficantly impacted by time of day.

Here is a time-of-day `latency` plot, appearing as `latency` in the filename:

![tod-latency](https://github.com/asher-m/autospeedtest/raw/master/samples/tod-latency.png)

Notice that latency and packetloss are also impacted by time of day (but perhaps to a lesser extent).  *A note on packetloss*: Ookla's packetloss statistics do not seem reliable in comparison to other tests avaiable, (see [packetlosstest.com](packetlosstest.com)).  The author's experience is that Ookla's measures significantly *under* estimate realworld packetloss.  This could be because of a number of reasons (Ookla's Speedtest uses TCP, among other reasons), but the result is nonetheless that this should not be taken to be a reliable measure.


### Result temporality: `all` vs `recent`

This option allows the user to choose between plotting all data or just the most recent 3 days.

The `all` option is shown below.  `all` is considered the default option so nothing is prepended or appended to the filename.

![tod-bandwidth](https://github.com/asher-m/autospeedtest/raw/master/samples/tod-bandwidth.png)

Notice that this is the same plot from the discussion above of the `bandwidth` vs `latency` options.  This doesn't mean anything, just that I thought it showed the differences well.

The `recent` option is shown below.  `recent` is considered the adjusting option, so it is appended as `-recent` to the end of the filename.

![tod-bandwidth-recent](https://github.com/asher-m/autospeedtest/raw/master/samples/tod-bandwidth-recent.png)

Notice that this plot has significantly fewer datapoints than the plot immediately above it.  This is because we're only using the most recent 3 days of data.


### Plot temporal axis: `tod` vs `epoch`

This option allows the user to plot data when it was recorded or overlayed onto time-of-day.

The `epoch` option is shown below.  `epoch` is considered the default option so nothing is prepended or appended to the filename.

![latency](https://github.com/asher-m/autospeedtest/raw/master/samples/latency.png)

This is the first time you're seeing the `epoch` option in any of the plots in this readme!  This is simply because I think it's less representative of overall behavior and therefore less interesting than the `tod` adjusted plots.  The gap in the middle is when I stopped tests for a day and a half for a really large download (a few hundred gigabytes).

The `tod` option is shown below.  `tod` is considering the adjusting option, so it is appended as `tod-` to the beginning of the filename.

![tod-latency](https://github.com/asher-m/autospeedtest/raw/master/samples/tod-latency.png)

Notice again that this was the second plot shown under the `bandwidth` vs `latency` option.  It's just nice to see again.

## That's all!
Happy testing, may your ISP's whims be ever in your favor. :wink:
