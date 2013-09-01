"""Command line tool to handle Postgresql WAL archiving on Rackspace's cloudfiles.

Quick help
==========

Install using pip then:
- Create a file ``/etc/pg_raxarchive.ini`` with rackspace credentials (see below).
- Run ``pg_raxarchive upload {path_to_file} {basename}`` to upload archive a file.
- Run ``pg_raxarchive download {basename} {path_to_file}`` to download an archived file.
- Run ``pg_raxarchive cleanup {filename}`` to remove WAL files older than {filename}.

Rackspace credential file follow pyrax format::

    [rackspace_cloud]
    username = YUOR_USERNAME_HERE
    api_key  = YOUR_API_KEY_HERE

You can customize the region and the container name using:
- ``pg_raxarchive --container CONTAINE_RNAME ...``
- ``pg_raxarchive --region REGION_NAME ...``

By default ``pg_raxarchive`` expect to be running inside rackspace network. If this is
not your case or you want to be billed for some other reasons use ``pg_raxarchive --use-public``.


More options
------------

Check ``pg_raxarchive --help`` to know more.

"""
__version__ = '1.0'
__author__ = 'Maurizio Sambati'

import os
import sys
import gzip
import shutil
import logging
import argparse
try:
    from cStringIO import StringIO
    StringIO  # XXX: pyflakes workaround
except ImportError:
    from StringIO import StringIO
from tempfile import NamedTemporaryFile
from contextlib import closing, contextmanager

import pyrax


@contextmanager
def removing_dir(dirname):
    try:
        yield dirname
    finally:
        shutil.rmtree(dirname)


@contextmanager
def atomicfilewriter(filename, mode='wb'):
    try:
        tmpfilename = os.path.join(
            os.path.dirname(filename),
            '.tmp-{}'.format(os.path.basename(filename)))
        fout = open(tmpfilename, mode)
        yield fout
    except:
        fout.close()
        os.unlink(tmpfilename)
    else:
        fout.close()
        os.rename(tmpfilename, filename)


def iterchunks(stream):
    while True:
        data = stream.read(2**20)
        if not data:
            break
        yield data


class FileNotFound(RuntimeError):
    pass


class PGRaxArchiver(object):
    def __init__(self, filename, region, container_name, use_public):
        pyrax.set_setting('identity_type', 'rackspace')
        pyrax.set_credential_file(filename)
        self.cf = pyrax.connect_to_cloudfiles(region=region, public=use_public)
        self.cnt = self.cf.create_container(container_name)

    def upload(self, src_name, dst_name, compress=True):
        if not compress:
            self._upload(src_name, dst_name)

        fout = NamedTemporaryFile(suffix='.gz', mode='wb', delete=False)
        try:
            fout.close()
            logging.debug('Compressing file %s...', src_name)
            with \
                    open(src_name, 'rb') as fin, \
                    closing(gzip.GzipFile(fout.name, mode='wb')) as gzout:
                for chunk in iterchunks(fin):
                    gzout.write(chunk)
            return self._upload(fout.name, dst_name + '.gz')
        finally:
            fout.unlink(fout.name)

    def _upload(self, filename, obj_name):
        logging.debug('Uploading file %s...', obj_name)
        self.cnt.upload_file(filename, obj_name=obj_name, return_none=True)

    def download(self, src_name, dst_name, compress='auto'):
        # XXX: use external memory instead of store everything in RAM
        if compress == 'auto':
            names = self.cnt.get_object_names()
            if src_name + '.gz' in names:
                compress = True
                src_name = src_name + '.gz'
            elif src_name in names:
                compress = False
            else:
                raise FileNotFound(src_name)

        logging.debug('Fetching file %s...', src_name)
        data = self.cnt.fetch_object(src_name)
            
        if compress is True:
            logging.debug('Decompressing...')
            stream = StringIO(data)
            with closing(gzip.GzipFile(fileobj=stream, mode='rb')) as fin:
                data = fin.read()

        logging.debug('Writing file %s...', dst_name)
        with atomicfilewriter(dst_name, 'wb') as fout:
            fout.write(data)

    def cleanup(self, filename):
        names = self.cnt_get_object_names()

        def stripgz(s):
            if s.endswith('.gz'):
                return s[:-3]
            return s

        uncompressed_names = {stripgz(k): k for k in names}
        removing_names = [uncompressed_names[k] for k in uncompressed_names if k < filename]

        for obj_name in removing_names:
            logging.debug('Removing file %s...', obj_name)
            self.cnt.delete_object(obj_name)


def main():
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
