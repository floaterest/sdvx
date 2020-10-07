from html.parser import HTMLParser
from urllib import request
from html import unescape

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


class ID3Parser(HTMLParser):
    def __init__(self, expect_tag: str, expect_classes: list = None, attr: str = None):
        super().__init__()
        self.data = ''
        self.tag = expect_tag
        self.classes = expect_classes or []
        self.parse = False
        self.attr = attr

    def error(self, message):
        print('error', message)

    def handle_starttag(self, tag, attrs):
        # check if it's wanted element
        self.parse = tag == self.tag
        if len(self.classes):
            for attr, value in attrs:
                if attr == 'class':
                    # if wanted class
                    self.parse = self.parse or value in self.classes

        # if want attr but not data
        if self.parse and self.attr:
            for attr, value in attrs:
                if attr == self.attr:
                    self.data = value
                    self.parse = False
                    break

    def handle_data(self, data):
        if self.parse:
            self.data = data


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
    def __init__(self, javascript: list):
        lines = [unescape(l).strip() for l in javascript]
        p = {
            'TI': self.title,
            'AR': self.artists,
            'BP': self.bpm,
            'SD': self.youtube
        }
        self.song = lines[3][7:12]
        self.yt = ''
        self.id3 = {}
        # assign id3
        for l in lines:
            if l.startswith('var'):
                if l[4:6] in p:
                    p[l[4:6]](l[l.index('=') + 2:-2])
            elif l.startswith('function'):
                break

    @staticmethod
    def parse(html: str, tag: str = None, classes: list = None, attr: str = None):
        parser = ID3Parser(tag, classes, attr)
        parser.feed(html)
        return parser.data

    def title(self, html: str):
        start = html.index('>', 1) + 1
        end = html.index('<', start)
        self.id3['title'] = html[start:end]

    def artists(self, html: str) -> (str, str):
        # composer
        composer = self.parse(html, 'div')[3:]
        try:
            i = composer.index('feat.')
            # -1 because space
            self.id3['composer'], self.id3['artist'] = composer[:i - 1], composer[i:]
        except ValueError:
            self.id3['composer'], self.id3['artist'] = composer, None

    def bpm(self, html: str):
        for char in (bpm := self.parse(html, classes=['f1', 'bpm'])):
            if not char.isdigit() and char != '-':
                bpm = None
                break
        self.id3['bpm'] = bpm

    def youtube(self, html: str):
        self.yt = self.parse(html, 'a', attr='href')[32:] or None

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

    def add_tags(self, file):
        # put id3 tags
        file = EasyID3(file)
        for tag, value in self.id3.items():
            if value:
                file[tag] = value
        file.save()
