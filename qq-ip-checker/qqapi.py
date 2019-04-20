import requests
import time

HEADERS = {
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,ja;q=0.6,zh-TW;q=0.5',
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'accept': '*/*',
}


def qqkey(guid, song_mid):
    url = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg'
    params = {
        'cid': '205361747',
        'guid': guid,
        'songmid': song_mid,
        'filename': '0.m4a',
        'format': 'json',
        '_': int(time.time() * 1000),
    }

    resp = requests.get(url, params=params, headers=HEADERS)
    js = resp.json()
    return js['data']['items'][0]['vkey']
