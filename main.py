"""
toc
    id
        javascript
            title
            yt url
            author
            illustrator
        cover
"""

import requests
from html.parser import HTMLParser


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


url = 'https://sdvx.in'
hiraganas = ['a', 'k', 's', 't', 'h', 'n', 'h', 'm', 'y', 'r', 'w']
toc = ToCParser()

for hiragana in hiraganas:
    content = requests.get(url + f'/sort/sort_{hiragana}.htm').content.decode('utf8')
    toc.feed(content)
    print(toc.songs)
