import pylast
import traceback
import sys

from db.db import *
from config import Config
from db.db_artist import DbArtist

logging.basicConfig(level=logging.DEBUG)

config = Config()

network = pylast.LastFMNetwork(api_key=config.lastfm.api_key, api_secret=config.lastfm.api_secret,
                               username=config.lastfm.username,
                               password_hash=pylast.md5(config.lastfm.password))


def get_and_update_tags_from_lastfm(db: Database, artist: pylast.Artist, db_artist: DbArtist):
    try:
        tags = artist.get_top_tags()
        db.remove_tags_from_artist(db_artist.id_)
        for tag in tags:
            tag_id = db.add_or_get_tag(tag.item.name)
            db.add_tag_to_artist(db_artist.id_, tag_id, tag.weight)

    except Exception as e:
        logging.error("get_and_update_tags_from_lastfm:")
        logging.error(e)


def generate_playlists_by_tags(db: Database):
    iter_tag = db.get_tags()
    for t in iter_tag:
        db_tag = iter_tag.cur
        playlist_name = db_tag.name
        db.delete_playlist(playlist_name)

        iter_top = db.get_tag_tracks(db_tag.id_, config.top_tag_playlist.playlist_max_length,
                                     config.top_tag_playlist.min_tag_weight)

        top = []
        duration = 0
        for t in iter_top:
            top.append(iter_top.cur)
            if iter_top.cur.duration_seconds is not None:
                duration += iter_top.cur.duration_seconds

        if len(top) > 0:
            playlist_id = db.add_playlist('admin', False, playlist_name, 'autogenerated')
            db.fill_playlist(playlist_id, top)
            db.update_playlist(playlist_id, len(top), duration)

        iter_top.close()

    iter_tag.close()


def get_and_update_playcount_from_lastfm(db: Database, db_artist: DbArtist, artist_name: str):
    iter_tracks = db.get_tracks(db_artist.name)
    for t in iter_tracks:
        db_track = iter_tracks.cur
        try:
            track = network.get_track(db_track.artist, db_track.title)
            play_cnt = track.get_playcount()
            logging.debug(F"From Last.Fm: Track {track}, play count {play_cnt}")
            db.update_track(db_track.id_, play_cnt, artist_name)

        except Exception as e:
            logging.error("get_and_update_playcount_from_lastfm:")
            logging.error(e)

    iter_tracks.close()


def generate_playlists_by_artists(artist_name, db):
    playlist_name = f'{artist_name} - the best'
    db.delete_playlist(playlist_name)
    iter_top = db.get_artist_top_tracks(artist_name,
                                        config.top_artist_songs_playlist.playlist_max_length)
    top = []
    duration = 0
    for t in iter_top:
        top.append(iter_top.cur)
        if iter_top.cur.duration_seconds is not None:
            duration += iter_top.cur.duration_seconds
    if len(top) > 0:
        playlist_id = db.add_playlist('admin', False, playlist_name, 'autogenerated')
        db.fill_playlist(playlist_id, top)
        db.update_playlist(playlist_id, len(top), duration)


def main():
    db = Database(config.db.driver_name, config.db.url, config.db.driver_lib_path)
    db.update_database()
    iter_artists = db.get_artists()

    for a in iter_artists:
        db_artist = iter_artists.cur
        artist_name = db_artist.name

        logging.info(f"Artist '{artist_name}'")
        artist = network.get_artist(db_artist.name)

        if config.enable_tags_playlists:
            get_and_update_tags_from_lastfm(db, artist, db_artist)

        if config.enable_top_artist_songs_playlists:
            get_and_update_playcount_from_lastfm(db, db_artist, artist_name)

        if config.enable_top_artist_songs_playlists:
            generate_playlists_by_artists(artist_name, db)

    iter_artists.close()

    if config.enable_tags_playlists:
        generate_playlists_by_tags(db)


if __name__ == '__main__':
    main()
