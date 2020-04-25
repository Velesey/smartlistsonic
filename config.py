import configparser
import os

TOP_ARTIST_SONGS_PLAYLIST = "top_artist_songs_playlist"
TOP_TAG_PLAYLIST = "top_tag_playlist"
COMMON = "common"
DB = "db"
LASTFM = "last.fm"

CONFIG_PATH = f'{os.path.dirname(os.path.realpath(__file__))}/config/config.ini'
CONFIG_PATH_EXAMPLE = CONFIG_PATH + '.example'


def _str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class TopArtistSongsPlaylist:
    def __init__(self):
        self.playlist_max_length: int = None


class TopTagPlaylist:
    def __init__(self):
        self.top_tags_count: int = None
        self.min_tag_weight: int = None
        self.playlist_max_length: int = None


class Db:
    def __init__(self):
        self.driver_name: str = None
        self.url: str = None
        self.driver_lib_path: str = None


class LastFm:
    def __init__(self):
        self.api_key: str = None
        self.api_secret: str = None
        self.username: str = None
        self.password: str = None


class Config:
    def __init__(self):
        self.create_config_file()
        self._config = configparser.ConfigParser()
        self._config.read(CONFIG_PATH)

        self.enable_top_artist_songs_playlists: bool = _str2bool(self._config[COMMON][
                                                                     'enable_top_artist_songs_playlists'])
        self.enable_tags_playlists: bool = _str2bool(self._config[COMMON][
                                                             'enable_tags_playlists'])

        self.db: Db = Db()
        self.db.driver_name = self._config[DB]["driver_name"]
        self.db.url = self._config[DB]["url"]
        self.db.driver_lib_path = self._config[DB]["driver_lib_path"]

        self.lastfm = LastFm()
        self.lastfm.api_key = self._config[LASTFM]["api_key"]
        self.lastfm.api_secret = self._config[LASTFM]["api_secret"]
        self.lastfm.username = self._config[LASTFM]["username"]
        self.lastfm.password = self._config[LASTFM]["password"]

        self.top_artist_songs_playlist: TopArtistSongsPlaylist = TopArtistSongsPlaylist()
        self.top_artist_songs_playlist.playlist_max_length = \
            int(self._config[TOP_ARTIST_SONGS_PLAYLIST]["playlist_max_length"])

        self.top_tag_playlist: TopTagPlaylist = TopTagPlaylist()
        self.top_tag_playlist.min_tag_weight = int(self._config[TOP_TAG_PLAYLIST]["min_tag_weight"])
        self.top_tag_playlist.playlist_max_length = int(
            self._config[TOP_TAG_PLAYLIST]["playlist_max_length"])

    def create_config_file(self):
        if not os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH_EXAMPLE, 'r') as src, open(CONFIG_PATH, 'w') as dst:
                dst.write(src.read())
