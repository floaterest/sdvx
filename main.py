"""
toc
    id
        javascript
            title
            feat
            bpm
            yt url
            composer
            illustrator
        cover
"""
import os
import requests
from html.parser import HTMLParser
from urllib import request


class JSParser:
    @staticmethod
    def get_title(line: str):
        return line[10:]

    @staticmethod
    def get_artist(line: str):
        return line[34:-8]

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

    @staticmethod
    def get_yt(line: str):
        return line[79:90]


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

    def parse_javascript(self, song_id: str):
        """

        :param song_id: id of the song, e.g. '04265'
        :return:
        """
        lines = requests.get(self.url + f'/{song_id[:2]}/js/{song_id}sort.js') \
            .content.decode('utf8') \
            .split('\n')
        # line position is fixed (thank you dev)
        commands = [
            [0, JSParser.get_title],
            [2, JSParser.get_artist],
            [3, JSParser.get_bpm],
            [18, JSParser.get_yt]
        ]
        for i, cmd in commands:
            print(cmd(lines[i]))


s = SDVX()
s.parse_javascript('05153')
