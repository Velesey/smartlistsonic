import jaydebeapi
import logging
import random

from db.db_track import DbTrackIterator
from db.db_artist import DbArtistIterator


def _escape_text(text: str):
    return text.replace("'", "''")


class Database:
    def __init__(self, driver_name: str, url: str, driver_lib_path: str):
        self.connect = jaydebeapi.connect(driver_name, url, None, driver_lib_path)

    def update_database(self):
        self._create_play_count_column()
        self._create_random_column()

    def update_track(self, id_: int, count: int):
        rnd = round(random.random() * 10000)
        sql = F"UPDATE MEDIA_FILE SET LASTFM_PLAY_COUNT = {count}, RANDOM = {rnd} WHERE ID = {id_}"
        self._execute_sql(sql)

    def get_tracks(self, artist: str) -> DbTrackIterator:
        sql = """SELECT ID, PATH, FOLDER, TYPE, FORMAT, TITLE, ALBUM, ARTIST, DISC_NUMBER, 
        TRACK_NUMBER, YEAR, GENRE, BIT_RATE, DURATION_SECONDS, FILE_SIZE, PLAY_COUNT, LASTFM_PLAY_COUNT 
        FROM MEDIA_FILE"""
        sql += " WHERE TYPE = 'MUSIC'"
        if artist is not None:
            sql += f" AND UPPER(ARTIST) = UPPER('{_escape_text(artist)}')"
        sql += " ORDER BY ID"
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbTrackIterator(cursor)

    def get_artist_top_tracks(self, artist: str, limit: int) -> DbTrackIterator:
        sql = f"""SELECT  M.ID, PATH, FOLDER, TYPE, FORMAT, M.TITLE, ALBUM, M.ARTIST, DISC_NUMBER, 
        TRACK_NUMBER, YEAR, GENRE, BIT_RATE, DURATION_SECONDS, FILE_SIZE, PLAY_COUNT, LASTFM_PLAY_COUNT 
        FROM MEDIA_FILE M
        JOIN ( SELECT DISTINCT (SELECT ID FROM MEDIA_FILE M2 WHERE M2.TITLE = M1.TITLE 
            AND M2.ARTIST = M1.ARTIST ORDER BY RANDOM LIMIT 1) AS ID,  TITLE,  ARTIST
            FROM MEDIA_FILE M1
            WHERE UPPER(M1.ARTIST) = UPPER('{_escape_text(artist)}') AND M1.LASTFM_PLAY_COUNT IS NOT NULL 
            AND TYPE = 'MUSIC' ) M2
        ON M.ID = M2.ID
        ORDER BY M.LASTFM_PLAY_COUNT DESC LIMIT  {limit} """
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbTrackIterator(cursor)

    def get_artists(self) -> DbArtistIterator:
        sql = f"""SELECT * FROM ARTIST ORDER BY NAME"""
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbArtistIterator(cursor)

    def add_playlist(self, user_name: str, is_public: bool, name: str, comment) -> int:
        table_name = "PLAYLIST"
        id_ = self._get_min_table_id(table_name) - 1
        sql = f"""INSERT INTO {table_name} (ID, USERNAME, IS_PUBLIC, NAME, COMMENT,  CREATED, CHANGED)
        VALUES 
        ({id_}, '{_escape_text(user_name)}', '{is_public}', '{_escape_text(name)}',
        '{_escape_text(comment)}', CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""
        self._execute_sql(sql)
        return id_

    def update_playlist(self, id_: int, file_count: int, duration_seconds: int):
        sql = f"""UPDATE PLAYLIST SET FILE_COUNT = {file_count}, DURATION_SECONDS = {duration_seconds}
                WHERE ID = {id_}"""
        self._execute_sql(sql)

    def clear_playlist(self):
        sql = f"DELETE FROM PLAYLIST WHERE ID < 0"
        self._execute_sql(sql)
        sql = f"DELETE FROM PLAYLIST_FILE WHERE ID < 0"
        self._execute_sql(sql)

    def fill_playlist(self, playlist_id: int, tracks: list):
        tracks.reverse()
        table_name = "PLAYLIST_FILE"
        id_ = self._get_min_table_id(table_name) - 1
        for track in tracks:
            sql = f"""INSERT INTO {table_name} (ID, PLAYLIST_ID, MEDIA_FILE_ID) 
            VALUES ({id_}, {playlist_id},
            (SELECT ID FROM MEDIA_FILE WHERE upper(TITLE) = upper('{_escape_text(track.title)}') 
            AND upper(ARTIST) = upper('{_escape_text(track.artist)}') LIMIT 1))"""

            self._execute_sql(sql)
            id_ = id_ - 1

    def _get_min_table_id(self, table_name: str) -> int:
        sql = f"SELECT MIN(ID) FROM {table_name}"
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        id_ = cursor.fetchone()[0]
        return id_ if id_ is not None else 0

    def _create_play_count_column(self):
        try:
            sql = "ALTER TABLE MEDIA_FILE ADD COLUMN LASTFM_PLAY_COUNT INTEGER"
            self._execute_sql(sql)
        except Exception as e:
            logging.error(e)

    def _create_random_column(self):
        try:
            # Разные БД преставляют различный синтаксис для рандомной выборки
            # чтобы не затачиваться на них, сделаем свой механизм рандома
            sql = "ALTER TABLE MEDIA_FILE ADD COLUMN RANDOM INTEGER"
            self._execute_sql(sql)
        except Exception as e:
            logging.error(e)

    def _execute_sql(self, sql: str):
        cursor = self.connect.cursor()
        try:
            logging.debug(f"EXECUTING '{sql}'")
            cursor.execute(sql)
            logging.debug(f"EXECUTED SQL")
        except Exception as e:
            logging.error(e)
        finally:
            cursor.close()

    def _execute_sql_for_fetch(self, sql: str, cursor: jaydebeapi.Cursor):
        try:
            logging.debug(f"EXECUTING '{sql}'")
            cursor.execute(sql)
            logging.debug(f"SQL EXECUTED'")
        except Exception as e:
            logging.error(e)
