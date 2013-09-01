Postgresql archiving tool for Rackspace
=======================================

`pg_raxarchive` it's an utility tool to manage Postgresql's WAL file archiving using
Rackspace cloudfiles.

Requirements
------------

- Python 2.7
- `pyrax` module installed
- A rackspace account :-)


Installation and Setup
----------------------

Install using pip and git:

    pip install git+https://github.com/duilio/pg_raxarchive#egg=pg_raxarchive

(pypi package in progress)


By default, `pg_raxarchive` reads Rackspace credentials from the `/etc/pg_raxarchive.ini`
file. The configuration is the same as `pyrax` ini file:

    [rackspace_cloud]
    username = YOUR_USERNAME_HERE
    api_key = YOUR_API_HERE


Getting Started
---------------

On your master `postgresql.conf` set the archive command to:

    archive_mode = on
    archive_command = 'pg_raxarchive upload %p %f'

On your slave `recovery.conf` set the restore command to:

    restore_command = 'pg_raxarchive download %f %p'
    archive_cleanup_command = 'pg_raxarchive cleanup %r'

And you are done.


Global options
--------------

* `--help` show the help screen
* `--config` sets Rackspace credential file, defaults to `/etc/pg_raxarchive.ini`.
* `--region` sets Rackspace region to use, defaults to `DFW`.
* `--container` sets the container name, defaults to `pg_archives`.
* `--use-public` use non internal connection for cloudfiles (i.e. when running from a non-Rackspace host).
* `--debug` enable some debugging info.


Command options
---------------

Currently only `upload` subcommand has an option.

* `--disable-compression` do not use gzip to compress the WAL


Contributes
-----------

This software is distributed with a BSD license. If you want to contribute to it, please feel
free to submit a pull request. The official git repository is on github:

https://github.com/duilio/pg_raxarchive

Some future development might be:

- Usage of environment variables for Rackspace authentication.
- Usage of command line options for Rackspace authentication.
- Better handling of large files during download.
