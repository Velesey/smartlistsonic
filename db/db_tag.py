from db.db_iterator import _DbIterator


class DbTag:
    def __init__(self, id_: int, name: str):
        self.id_ = id_
        self.name = name


class DbTagIterator(_DbIterator):
    prev: DbTag
    cur: DbTag

    def _fetch(self):
        data = super()._fetch()
        if data is not None:
            obj = DbTag(data[0], data[1])
            return obj
        return None
