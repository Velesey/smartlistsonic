import json
import os

FILE_PATH = f'{os.path.dirname(os.path.realpath(__file__))}/config/genres.json'

class SuperGenre:
    def __init__(self, name: str, genres: []):
        self.name = name
        self.genres = genres

    def get_affilation_value(self, genre_name : str) -> float:
        genre_name = genre_name.replace("'", '')
        genre_name = genre_name.replace('"', '')
        genre_name = genre_name.replace("-", ' ')
        genre_name = genre_name.replace("/", ' ')
        genre_name = genre_name.replace("\\", ' ')

        # и тут дальше волшебным образом вычисляем циферку


with open(FILE_PATH) as fid:
    data = json.load(fid)

    all_genres = []
    super_genres = []


    for k in data.keys():
        obj = SuperGenre(k, [])

        for d in data[k]:
            if d in all_genres:
                raise Exception(f"Genre '{d}' is not unique!")
            all_genres.append(d)
            obj.genres.append(d)

        super_genres.append(obj)

