Alpine System Info Log
======================

Alpine System Info logger with email functionality and log Viewer.

This repository contains two tools:

* Alpine System Info logger (to create log files)
* Alpine System Info log Viewer (to view and compare log files)

The Alpine System Info log Viewer reads all log-files from a folder (sorted by timestamp).
It parses the log files and shows the information per module in a table.
Any changes in the log file (compared with the previous log file) are marked red.
This allows to find changes to the system fast!

![CSV Compare screenshot](https://raw.githubusercontent.com/hanckmann/alplogs/master/assets/screenshot1.png)

The code is super easy to extend with other modules (both the logger and the viewer).

The ZFS version is targetted at local installations on ZFS. It also includes Smart Monitoring via smartmontools.
The "other" version is targetted at Virtual Machine installations using non-ZFS filesystems (ext2/3/4, xfs, etc).

This is work in progress...


Requirements
------------

The Alpine System Info logger is _only_ tested on [Alpine Linux](https://www.alpinelinux.org/).
Other POSIX Compliant operating systems might work as well.

For the Alpine System Info logger:

* a POSIX compatible shell
* the following applications should be available (installed):
  - ssmtp
  - mailx
  - wget
  - util-linux
  - procps
* for the ZFS script the following applications should also be available (installed):
  - zfs
  - smartmontools

For the Alpine System Info log Viewer:

* Python 3.5+
* PyQt5 (Python3 bindings for Qt5)


Running
-------


### Alpine System Info logger

It is recommended to run the Alpine System Info logger via a cronjob.
It can be started via:

```
$ cd <script folder>
$ ./system-status
```

To send the log via email:

```
$ cd <script folder>
$ ./system-status mail
```

*Note:* that sending an email requires a working ssmtp setup!


### Alpine System Info log Viewer

First create and start a [python 3 virtual environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments):

```
$ python -m venv venv
$ source venv/bin/activate
```

The last line might be different depending on the shell/prompt environment.

Then install the dependencies:

```
$ pip install -r requirements.txt
```

Finally the application can be started via:

```
$ cd <viewer folder>
$ ./alplogviewer.py
```


License
-------

The license is Apache License Version 2.0.

Also see: LICENSE.txt


Contributing
------------

Alpine System Info Log uses Github to track bugs, user questions, and development.

Repository: https://github.com/hanckmann/alplogs
