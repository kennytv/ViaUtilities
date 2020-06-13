from __future__ import print_function, absolute_import, division, unicode_literals

_package_data = dict(
    full_package_name='ruamel.std.zipfile',
    version_info=(0, 1, 1),
    __version__='0.1.1',
    author='Anthon van der Neut',
    author_email='a.van.der.neut@ruamel.eu',
    description='improvements over the standard zipfile package',
    # keywords="",
    entry_points=None,
    license='MIT License',
    since=2017,
    universal=True,
    install_requires=[],
    tox=dict(env='23'),
    print_allowed=True,
)


version_info = _package_data['version_info']
__version__ = _package_data['__version__']

###########

import os              # NOQA
import sys             # NOQA
import zipfile         # NOQA
from zipfile import *  # NOQA

class InMemoryZipFile(object):
    # original idea from http://stackoverflow.com/a/19722365/1307905
    def __init__(self, file_name=None, compression=None, debug=0):
        if compression is None:
            compression = zipfile.ZIP_DEFLATED
        try:
            from cStringIO import StringIO
        except ImportError:
            from io import BytesIO as StringIO
        # Create the in-memory file-like object
        if hasattr(file_name, '_from_parts'):
            self._file_name = str(file_name)
        else:
            self._file_name = file_name
        self.in_memory_data = StringIO()
        # Create the in-memory zipfile
        self.in_memory_zip = zipfile.ZipFile(
            self.in_memory_data, "w", compression, False)
        self.in_memory_zip.debug = debug

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        self.in_memory_zip.writestr(filename_in_zip, file_contents)
        return self   # so you can daisy-chain

    def write_to_file(self, filename):
        '''Writes the in-memory zip to a file.'''
        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in self.in_memory_zip.filelist:
            zfile.create_system = 0
        self.in_memory_zip.close()
        with open(filename, 'wb') as f:
            f.write(self.data)

    @property
    def data(self):
        return self.in_memory_data.getvalue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._file_name is None:
            return
        self.write_to_file(self._file_name)

    def delete_from_zip_file(self, pattern=None, file_names=None):
        """
        zip_file can be a string or a zipfile.ZipFile object, the latter will be closed
        any name in file_names is deleted, all file_names provided have to be in the ZIP
        archive or else an IOError is raised
        """
        if pattern and isinstance(pattern, str):
            import re
            pattern = re.compile(pattern)
        if file_names:
            if not isinstance(file_names, list):
                file_names = [str(file_names)]
            else:
                file_names = [str(f) for f in file_names]
        else:
            file_names = []
        with zipfile.ZipFile(self._file_name) as zf:
            for l in zf.infolist():
                if l.filename in file_names:
                    file_names.remove(l.filename)
                    continue
                if pattern and pattern.match(l.filename):
                    continue
                self.append(l.filename, zf.read(l))
            if file_names:
                raise IOError('[Errno 2] No such file{}: {}'.format(
                    '' if len(file_names) == 1 else 's',
                    ', '.join([repr(f) for f in file_names])))


def delete_from_zip_file(file_name, pattern=None, file_names=None,
                         compression=None):
    with InMemoryZipFile(file_name, compression=compression) as imz:
        imz.delete_from_zip_file(pattern, file_names)
