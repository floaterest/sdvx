import os
from html.parser import HTMLParser
from urllib import request

import requests
import youtube_dl
from mutagen.easyid3 import EasyID3


class ToCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.songs = []

    def error(self, message):
        print('error', message)

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            for attr, value in attrs:
                if attr == 'src' and 'common' not in value:
                    # get all the js path, don't want '/files/common.js'
                    # e.g. '/05/js/05174sort.js' => '05174'
                    self.songs.append(value[7:12])
                    break


class SDVX:
    def __init__(self, url='https://sdvx.in'):
        self.url = url

    def parse_toc(self, sort: str) -> list:
        """
        :param sort: hiragana (a, k, s, t, h, etc)
        :return: list of found ids
        """
        toc = ToCParser()
        content = requests.get(self.url + f'/sort/sort_{sort}.htm') \
            .content.decode('utf8')
        toc.feed(content)
        return toc.songs

    def download_cover(self, song_id: str, path=''):
        """
        Download the cover of the song, filename will be {song_id}.png
        :param song_id: id of the song, e.g. '05238'
        :param path: destination folder
        """
        request.urlretrieve(
            self.url + f'/{song_id[:2]}/jacket/{song_id}n.png',
            os.path.join(path, song_id + '.png'))

    def get_javascript(self, song_id: str) -> list:
        """

        :param song_id: id of the song, e.g. '04265'
        :return:
        """
        return requests.get(self.url + f'/{song_id[:2]}/js/{song_id}sort.js') \
            .content.decode('utf8') \
            .split('\n')


class Song:
    def __init__(self, js: list):
        self.song_id = js[0][4:9]
        self.title = js[0][10:]
        self.composer, self.feat = self.get_artists(js[2])
        self.bpm = self.get_bpm(js[3])
        self.ytid = js[18][79:90]

    @staticmethod
    def get_artists(line: str) -> (str, str):
        line = line[34:-8]
        try:
            i = line.index('feat.')
            # -1 b/c space
            return line[:i - 1], line[i:]
        except ValueError:
            return line, None

    @staticmethod
    def get_bpm(line: str):
        # no regex
        end = len(line) - 1
        while not line[end].isdigit():
            end -= 1
        begin = (end := end + 1) - 2
        while (c := line[begin]).isdigit() or c == '-':
            begin -= 1
        return line[begin + 1:end]

    def download_from_yt(self) -> str:
        if self.ytid:
            opt = {
                'format': 'bestaudio/best',
                'outtmpl': (filename := f'[{self.song_id}][{self.ytid}].mp3')
            }
            with youtube_dl.YoutubeDL(opt) as ydl:
                ydl.download([f'https://youtu.be/{self.ytid}'])

            return filename
        else:
            raise Exception('This song is unavailable on YouTube')

