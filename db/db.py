import jaydebeapi
import logging
import random
import hashlib
import os

from db.db_track import DbTrackIterator
from db.db_artist import DbArtistIterator
from db.db_tag import DbTagIterator


def _escape_text(text: str):
    if text is not None:
        return text.replace("'", "''")
    return str


class Database:
    def __init__(self, driver_name: str, url: str, driver_lib_path: str):
        full_path = f'{os.path.dirname(os.path.realpath(__file__))}/../{driver_lib_path}'
        self.connect = jaydebeapi.connect(driver_name, url, None, full_path)

    def update_database(self):
        self._create_column_playcount()
        self._create_column_random()
        self._create_table_tag()
        self._create_table_artist_tag()

    def add_or_get_tag(self, name: str, super_tag: str) -> int:
        table_name = "TAG"
        sql = f"""SELECT ID FROM {table_name} WHERE UPPER(NAME) = UPPER('{_escape_text(name)}')"""
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        data = cursor.fetchone()
        if data is not None:
            id_ = data[0]
            if id_ is not None:
                return id_
        id_ = self._get_min_table_id(table_name) - 1
        sql = f"""INSERT INTO {table_name} (ID, NAME, SUPER_TAG) VALUES ({id_}, 
            UPPER('{_escape_text(name)}'), UPPER('{_escape_text(super_tag)}'))"""
        self._execute_sql(sql)
        return id_

    def add_tag_to_artist(self, artist_id: int, tag_id: int, weight: int):
        table_name = "TAG_ARTIST"
        id_ = self._get_min_table_id(table_name) - 1
        sql = f"""INSERT INTO {table_name} ( ID, ARTIST_ID, TAG_ID, WEIGHT)
                    VALUES ({id_}, {artist_id}, {tag_id}, {weight})"""
        self._execute_sql(sql)

    def get_tags(self) -> DbTagIterator:
        sql = f"SELECT * FROM TAG"
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbTagIterator(cursor)

    def remove_tags_from_artist(self, artist_id):
        sql = f"""DELETE FROM TAG_ARTIST WHERE ARTIST_ID = {artist_id}"""
        self._execute_sql(sql)

    def update_track(self, id_: int, last_fm_playcount: int, artist_name: str):
        rnd = round(random.random() * 100000)
        sql = F"""UPDATE MEDIA_FILE SET LASTFM_PLAY_COUNT = {last_fm_playcount}, RANDOM = {rnd} """
        if artist_name is not None:
            sql += f", ARTIST = '{artist_name}'"
        sql += f" WHERE ID = {id_}"
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

    def get_tag_tracks(self, super_tag: str, limit: int, weight: int) -> DbTrackIterator:
        sql = f"""SELECT  M.ID, PATH, FOLDER, TYPE, FORMAT, M.TITLE, ALBUM, M.ARTIST, DISC_NUMBER, 
        TRACK_NUMBER, YEAR, GENRE, BIT_RATE, DURATION_SECONDS, FILE_SIZE, PLAY_COUNT, LASTFM_PLAY_COUNT 
        FROM MEDIA_FILE M
        JOIN ( SELECT DISTINCT (SELECT ID FROM MEDIA_FILE M2 WHERE M2.TITLE = M1.TITLE 
            AND M2.ARTIST = M1.ARTIST ORDER BY RANDOM LIMIT 1) AS ID, TITLE,  ARTIST
            FROM MEDIA_FILE M1
            WHERE UPPER(M1.ARTIST) in (SELECT UPPER(A.NAME) FROM ARTIST A JOIN TAG_ARTIST TA 
            ON TA.ARTIST_ID = A.ID JOIN TAG T ON TA.TAG_ID = T.ID WHERE T.SUPER_TAG = '{_escape_text(super_tag)}' 
            AND WEIGHT >= {weight})
            AND M1.LASTFM_PLAY_COUNT IS NOT NULL AND TYPE = 'MUSIC' ) M2 ON M.ID = M2.ID
                ORDER BY ((M.LASTFM_PLAY_COUNT + (M.PLAY_COUNT * (SELECT AVG(LASTFM_PLAY_COUNT) 
                FROM MEDIA_FILE)))  / M.RANDOM) DESC  LIMIT  {limit} """

        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbTrackIterator(cursor)

    def get_artists(self) -> DbArtistIterator:
        sql = f"""SELECT * FROM ARTIST ORDER BY NAME"""
        cursor = self.connect.cursor()
        self._execute_sql_for_fetch(sql, cursor)
        return DbArtistIterator(cursor)

    def update_artist(self, id_: int, name: str):
        sql = f"""UPDATE ARTIST SET NAME = '{name}' WHERE ID = {id_}"""
        self._execute_sql(sql)

    def add_playlist(self, user_name: str, is_public: bool, name: str, comment) -> int:
        id_ = self.generate_table_id(name)
        sql = f"""INSERT INTO PLAYLIST (ID, USERNAME, IS_PUBLIC, NAME, COMMENT,  CREATED, CHANGED)
        VALUES 
        ({id_}, '{_escape_text(user_name)}', '{is_public}', '{_escape_text(name)}',
        '{_escape_text(comment)}', CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""
        self._execute_sql(sql)
        return id_

    def update_playlist(self, id_: int, file_count: int, duration_seconds: int):
        sql = f"""UPDATE PLAYLIST SET FILE_COUNT = {file_count}, DURATION_SECONDS = {duration_seconds}
                WHERE ID = {id_}"""
        self._execute_sql(sql)

    def clear_all_my_playlists(self):
        sql = f"DELETE FROM PLAYLIST WHERE ID < 0"
        self._execute_sql(sql)
        sql = f"DELETE FROM PLAYLIST_FILE WHERE ID < 0"
        self._execute_sql(sql)

    def delete_playlist(self, string: str):
        id_ = self.generate_table_id(string)
        logging.info(f'delete id {id_}')
        sql = f"DELETE FROM PLAYLIST WHERE ID = {id_}"
        self._execute_sql(sql)
        sql = f"DELETE FROM PLAYLIST_FILE WHERE PLAYLIST_ID = {id_}"
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

    def generate_table_id(self, string: str) -> int:
        hash_ = int(hashlib.md5(string.encode('utf-8')).hexdigest()[:7], 16)
        if hash_ > 0:
            hash_ = hash_ * -1
        return hash_

    def _create_column_playcount(self):
        try:
            sql = "ALTER TABLE MEDIA_FILE ADD COLUMN LASTFM_PLAY_COUNT INTEGER"
            self._execute_sql(sql)
        except Exception as e:
            logging.error(e)

    def _create_column_random(self):
        try:
            # Разные БД преставляют различный синтаксис для рандомной выборки
            # чтобы не затачиваться на них, сделаем свой механизм рандома
            sql = "ALTER TABLE MEDIA_FILE ADD COLUMN RANDOM INTEGER"
            self._execute_sql(sql)
        except Exception as e:
            logging.error(e)

    def _create_table_tag(self):
        try:
            sql = """ CREATE TABLE TAG ( ID INTEGER, NAME VARCHAR(128), SUPER_TAG VARCHAR(128),
            PRIMARY KEY (ID) ) """
            self._execute_sql(sql)
        except Exception as e:
            logging.error(e)

    def _create_table_artist_tag(self):
        try:
            sql = """CREATE TABLE TAG_ARTIST (ID INTEGER, ARTIST_ID INTEGER, TAG_ID INTEGER,
              WEIGHT INTEGER,  PRIMARY KEY (ID) ) """
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
