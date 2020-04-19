from db.db_iterator import _DbIterator
from db.db_media_file_type import DbMediaFileType


class DbTrack:
    def __init__(self, id_: int, path: str, folder: str, type_: DbMediaFileType, format_: str,
                 title: str, album: str, artist: str, disc_number: int, track_number: int,
                 year: int, genre: str, bit_rate: int, duration_seconds: int, file_size: int,
                 play_count, lastfm_play_count):
        self.id_ = id_
        self.path = path
        self.folder = folder
        self.type_ = type_
        self.format_ = format_
        self.title = title
        self.album = album
        self.artist = artist
        self.disc_number = disc_number
        self.track_number = track_number
        self.year = year
        self.genre = genre
        self.bit_rate = bit_rate
        self.duration_seconds = duration_seconds
        self.file_size = file_size
        self.play_count = play_count
        self.lastfm_play_count = lastfm_play_count

class DbTrackIterator(_DbIterator):
    prev: DbTrack
    cur: DbTrack

    def _fetch(self):
        data = super()._fetch()
        if data is not None:
            obj = DbTrack(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
                           data[8], data[9], data[10], data[11], data[12], data[13], data[14],
                           data[15], data[16])
            return obj
        return None
