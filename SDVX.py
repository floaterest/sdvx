from html.parser import HTMLParser
from urllib import request
import html

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
        self.hiraganas = ['a', 'k', 's', 't', 'n', 'h', 'm', 'y', 'r', 'w']

    def toc_to_ids(self, sort: str) -> list:
        """
        Parse song ids from sort.htm
        :param sort: hiragana ('a', 'k', 's', 't', 'h', etc)
        :return: list of found ids
        """
        toc = ToCParser()
        content = requests.get(self.url + f'/sort/sort_{sort}.htm') \
            .content.decode('utf8')
        toc.feed(content)
        return toc.songs

    def download_js(self, song_id: str, path=None):
        """
        Download the sort.js file for the song
        """
        path = path or song_id
        path = path if path.endswith('.js') else path + '.js'
        request.urlretrieve(f'{self.url}/{song_id[:2]}/js/{song_id}sort.js', path)


class Song:
    def __init__(self, js: str):
        lines = [html.unescape(l).strip() for l in js]
        self.song = lines[0][3:8]
        self.id3 = {
            'title': lines[0][9:],
            'bpm': self.get_bpm(lines[3]),
        }

        self.id3['composer'], self.id3['artist'] = self.get_artists(lines[2])
        # may be empty string
        self.yt = self.get_yt(lines[14:])

    @staticmethod
    def get_artists(line: str) -> (str, str):
        """
        Parse composer and artist
        :param line: line of code in javascript
        :return: composer, feat(can be None)
        """
        # composer
        line = line[34:-8]
        try:
            i = line.index('feat.')
            # -1 because space
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
        # if the next char is not a digit, bpm DNE
        return line[begin + 1:end] if line[begin + 2].isdigit() else 'n/a'

    @staticmethod
    def get_yt(lines: list):
        """
        Get YouTube ID, won't raise error if it's empty
        :param lines:
        :return:
        """
        for l in lines:
            # the line position of yt url varies
            if l.startswith('var SD'):
                return l[79:90]
        # raise error when html tag not found (can't find the right line in js)
        raise Exception("can't find youtube url")

    def download_mp3(self, filename: str):
        if self.yt:
            opt = {
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': filename.replace('.mp3', '')
            }
            with youtube_dl.YoutubeDL(opt) as ydl:
                ydl.download([f'https://youtu.be/{self.yt}'])

        else:
            raise Exception('This song is not available on YouTube')

    # def download_cover(self):
    #     request.urlretrieve(
    #         self.url + f'/{self.song_id[:2]}/jacket/{self.song_id}n.png',
    #         self.song_id + '.png')

    def add_tags(self, file):
        # put id3 tags
        file = EasyID3(file)
        for tag, value in self.id3.items():
            if value:
                file[tag] = value
        file.save()
