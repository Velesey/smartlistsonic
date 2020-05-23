from db.db_iterator import _DbIterator


class DbTag:
    def __init__(self, id_: int, name: str, super_tag: str):
        self.id_ = id_
        self.name = name
        self.super_tag = super_tag


class DbTagIterator(_DbIterator):
    prev: DbTag
    cur: DbTag

    def _fetch(self):
        data = super()._fetch()
        if data is not None:
            obj = DbTag(data[0], data[1], data[2])
            return obj
        return None
