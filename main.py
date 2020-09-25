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
        content = requests.get(self.url + f'/sort/sort_{sort}.htm').content.decode('utf8')
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

