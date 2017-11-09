import logging
import os, sys

logger = logging.getLogger("singleton")

# code adapted from https://github.com/pycontribs/tendo/blob/master/tendo/singleton.py
class InstanceFileLock:
    def __init__(self, lockpath):
        self._lock = lockpath

    def __enter__(self):
        if sys.platform == 'win32':
            try:
                if os.path.exists(self._lock):
                    os.unlink(self._lock)
                self.fd = os.open(self._lock, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError:
                logger.warning("Another instance is running.")
                sys.exit(-1)
        else:
            import fcntl
            self.fp = open(self._lock, 'w')
            try:
                fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                logger.warning("Another instance is running.")
                sys.exit(-1)

    def __exit__(self, type, value, traceback):
        try:
            if sys.platform == 'win32':
                os.close(self.fd)
            else:
                import fcntl
                fcntl.lockf(self.fp, fcntl.LOCK_UN)
                self.fp.close()
            os.unlink(self._lock)
        except Exception as e:
            logger.error(e)
