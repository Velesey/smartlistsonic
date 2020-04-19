import jaydebeapi


class _DbIterator:
    def __init__(self, cursor: jaydebeapi.Cursor):
        self._cursor = cursor
        self.prev = None
        self.cur = None

    def __next__(self):
        self.prev = self.cur
        self.cur = self._fetch()
        if self.cur is None:
            raise StopIteration()
        return self.cur

    def __iter__(self):
        return self

    def _fetch(self):
        return self._cursor.fetchone()

    def close(self):
        self._cursor.close()

