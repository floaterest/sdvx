import json
import os
from urllib import request
from datetime import datetime
from codecs import open
from time import time

from SDVX import SDVX, Song


def write(i, date, yt, sucess):
    with open('!.txt', 'a+') as f:
        f.write(f'{i} {date} '
                f'{yt if yt else "___________"} '
                f'{"true" if sucess else "false"}\n')


exists = {f[:5]: f for f in os.listdir() if f.endswith('.mp3')}
sdvx = SDVX()


def get_all_ids(output):
    # write all sdvx song ids in a file
    with open(output, 'w+', 'utf8sig') as f:
        for sort in sdvx.hiraganas:
            print('searching', sort)
            for song in sdvx.toc_to_ids(sort):
                f.write(song)
                f.write('\n')


def download_all_js(id_file):
    with open(id_file, 'r') as f:
        while line := f.readline():
            line = line[:-1]
            print(line)
            request.urlretrieve(f'https://sdvx.in/{line[:2]}/js/{line}sort.js', f'js\\{line}.js')


def update_all(folder):
    data = {}
    for js in os.listdir(folder):
        if js.startswith('05'):
            continue
        with open(os.path.join(folder, js), 'r', 'utf-8-sig', errors='ignore') as f:
            s = Song(f.readlines())
            sucess = bool(s.yt)
            # if don't exist
            if s.song not in exists:
                if s.yt:
                    sucess = s.download_mp3(filename := f'{s.song}@{s.yt}.mp3')
            else:
                print(s.song, 'exists')
                filename = exists[s.song]

            if sucess and int(s.song) > 1129:
                s.add_tags(filename)

            s.id3.update({
                'youtube': s.yt,
                'sucess': sucess,
                'date': int(datetime.now().strftime('%Y%m%d')),
            })
            data[s.song] = s.id3

        with open('sucess.json', 'w+', 'utf8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))


t = time()
update_all('js')
print(time() - t)
