from db.db_iterator import _DbIterator


class DbArtist:
    def __init__(self, id_: int, name: str, cover_art_path: str, album_count: str):
        self.id_ = id_
        self.name = name
        self.cover_art_path = cover_art_path
        self.album_count = album_count


class DbArtistIterator(_DbIterator):
    prev: DbArtist
    cur: DbArtist

    def _fetch(self):
        data = super()._fetch()
        if data is not None:
            obj = DbArtist(data[0], data[1], data[2], data[3])
            return obj
        return None
