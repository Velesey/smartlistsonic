import json
import os

FILE_PATH = f'{os.path.dirname(os.path.realpath(__file__))}/config/genres.json'


class _SuperGenre:
    def __init__(self, name: str, genres: []):
        self.name = name
        self.genres = genres

    # return from 0 to 1
    def get_affilation_value(self, name: str) -> float:
        name = name.upper()
        name = name.replace("'", '')
        name = name.replace('"', '')
        name = name.replace("-", ' ')
        name = name.replace("/", ' ')
        name = name.replace("\\", ' ')

        if name in self.genres:
            return 1

        # max - 0.9
        names = name.split(" ")
        names_cnt = len(names)
        result = 0
        for n in names:
            if n in self.genres:
                result += (0.9 / names_cnt)
        if result > 0:
            return result

        # max - 0.5
        for n in names:
            if any(n in g for g in self.genres):
                result += (0.5 / names_cnt)
        return result


class GenresHelper:
    def __init__(self):
        with open(FILE_PATH) as fid:
            data = json.load(fid)

            all_genres = []
            self.super_genres = []

            for k in data.keys():
                obj = _SuperGenre(k, [])

                for d in data[k]:
                    if d in all_genres:
                        raise Exception(f"Genre '{d}' is not unique!")
                    all_genres.append(d)
                    obj.genres.append(d)

                self.super_genres.append(obj)

    def get_super_genre_name(self, genre_name: str) -> str:
        affiliation = 0
        super_genre_name = ""
        for s in self.super_genres:
            aff = s.get_affilation_value(genre_name)
            if aff > affiliation:
                affiliation = aff
                super_genre_name = s.name
        return super_genre_name


s = GenresHelper()

print(s.get_super_genre_name("SUPER ROCK"))
