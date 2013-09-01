import os
import gzip
import shutil
import logging
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

        def normalize(name):
            return name.partition('.')[0]

        uncompressed_names = {stripgz(k): k for k in names}

        filename = normalize(filename)
        removing_names = [uncompressed_names[k] for k in uncompressed_names
                          if normalize(k) < filename]

        for obj_name in removing_names:
            logging.debug('Removing file %s...', obj_name)
            self.cnt.delete_object(obj_name)
