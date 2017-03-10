from contextlib import contextmanager
import os
import zipfile


@contextmanager
def archive(filename):
    try:
        arx = Zip(filename)
        yield arx
    except:
        if os.path.isfile(filename):
            os.remove(filename)
        raise
    finally:
        arx.close()


class Zip:
    def __init__(self, filename, compression=zipfile.ZIP_DEFLATED):
        self.archive = zipfile.ZipFile(filename, mode='w',
                                       compression=compression)

    def write(self, filename, membername=None):
        self.archive.write(filename, membername)

    def close(self):
        self.archive.close()
