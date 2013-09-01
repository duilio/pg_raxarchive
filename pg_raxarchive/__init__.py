"""Command line tool to handle Postgresql WAL archiving on Rackspace's cloudfiles.

pg_raxarchive
=============

``pg_raxarchive`` is a command line tool to handle Postgresql WAL archiving on
Rackspace's cloudfiles.


Quick help
----------

Install using pip then:

- Create a file ``/etc/pg_raxarchive.ini`` with rackspace credentials (see below).
- Run ``pg_raxarchive upload {path_to_file} {basename}`` to upload archive a file.
- Run ``pg_raxarchive download {basename} {path_to_file}`` to download an archived file.
- Run ``pg_raxarchive cleanup {filename}`` to remove WAL files older than {filename}.

Rackspace credential file follows pyrax format::

    [rackspace_cloud]
    username = YUOR_USERNAME_HERE
    api_key  = YOUR_API_KEY_HERE

You can customize the region and the container name using:

- ``pg_raxarchive --container CONTAINE_RNAME ...``
- ``pg_raxarchive --region REGION_NAME ...``

By default ``pg_raxarchive`` expects to be running inside rackspace network. If this is
not your case or you want to be billed for some other reasons use ``pg_raxarchive --use-public``.


More
----

* Run ``pg_raxarchive --help`` to know more.
* Check the repository at https://github.com/duilio/pg_raxarchive/

"""
__version__ = '1.0'
__author__ = 'Maurizio Sambati'

import sys
import logging
import argparse


def main():
    from archiver import PGRaxArchiver

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='/etc/pg_raxarchive.ini')
    parser.add_argument('--region', default='DFW')
    parser.add_argument('--container', default='pg_archives')
    parser.add_argument('--use-public', default=False, action='store_true')
    parser.add_argument('-d', '--debug', dest='loglevel', default=logging.WARNING,
                        action='store_const', const=logging.DEBUG)

    subparsers = parser.add_subparsers()
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('srcpath', help='Full source path')
    upload_parser.add_argument('filename', help='WAL filename')
    upload_parser.add_argument('--disable-compression', dest='compress',
                               default=True, action='store_false')
    upload_parser.set_defaults(cmd='upload')

    download_parser = subparsers.add_parser('download', help='Download a file')
    download_parser.add_argument('filename', help='WAL filename')
    download_parser.add_argument('destpath', help='Full destination path')
    download_parser.set_defaults(cmd='download')

    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup archives')
    cleanup_parser.add_argument('filename', help='Last file to keep')
    cleanup_parser.set_defaults(cmd='cleanup')

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=args.loglevel)

    archiver = PGRaxArchiver(args.config, args.region, args.container, args.use_public)

    if args.cmd == 'upload':
        return archiver.upload(args.srcpath, args.filename, args.compress)
    elif args.cmd == 'download':
        return archiver.download(args.filename, args.destpath)
    elif args.cmd == 'cleanup':
        return archiver.cleanup(args.filename)
    else:
        raise RuntimeError('Unknown subcommand {}'.format(args.cmd))


if __name__ == '__main__':
    sys.exit(main())
