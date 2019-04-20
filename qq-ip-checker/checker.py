import json
import logging
import traceback
from urllib.parse import unquote_plus

import requests
import asyncio
import aiohttp

import qqapi


FORMAT = '%(asctime)-15s %(levelname)s # %(message)s'

logging.basicConfig(filename='log.log', format=FORMAT, level=logging.INFO)
logger = logging.getLogger('main')

fl = open('qq-ips.txt', 'w')


class Task:

    def __init__(self, target, user, ut, code):
        self.target = target
        self.user = user
        self.ut = ut
        self.code = code

    def __str__(self):
        return '''
        target: {}
        user: {}
        ut: {}
        code: {}
        '''.format(self.target, self.user, self.ut, self.code)


def request_task(target):
    url = 'http://www.17ce.com/site/checkuser'
    headers = {
        'Accept': '*/*',
        'Referer': 'http://www.17ce.com/site',
        'Origin': 'http://www.17ce.com',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'url': target,
        'type': 'http',
        'isp': '0',
    }
    try:
        resp = requests.post(url, headers=headers, data=data)
        js = resp.json()
        if not js.get('rt'):
            raise Exception('Task response fails: {}'.format(js))
    except Exception as err:
        raise Exception('Task request fails: {}'.format(err))

    data = js['data']
    return Task(target, data['user'], data['ut'], data['code'])


def handle_data(data):
    js = json.loads(data)

    if js.get('error') != '':
        raise Exception('17ce error: {}'.format(data))

    if js.get('type') == 'NewData':
        result = js['data']
        if result['HttpCode'] == 200:
            ip = result['SrcIP']
            logger.info('ok-ip: ' + ip)
            fl.write(ip + '\n')


async def receive_result(task):
    url = 'wss://wsapi.17ce.com:8001/socket/?user={}&code={}&ut={}'.format(
        unquote_plus(task.user), task.code, task.ut
    )

    headers = {
        'Origin': 'http://www.17ce.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6,ja;q=0.5',
        'Sec-WebSocket-Key': '5vMf2Sf69YGTIUqinm5Gfw==',
        'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'Upgrade': 'websocket',
        'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
        'Cache-Control': 'no-cache',
        'Connection': 'Upgrade',
        'Sec-WebSocket-Version': '13',
    }

    ws = await aiohttp.ClientSession().ws_connect(url, headers=headers)

    data = {
        "txnid": 1,
        "nodetype": 1,
        "num": 1,
        "Url": task.target,
        "TestType": "HTTP",
        "Host": "",
        "TimeOut": 10,
        "Request": "GET",
        "NoCache": False,
        "Speed": 0,
        "Cookie": "",
        "Trace": False,
        "Referer": "",
        "UserAgent": "",
        "FollowLocation": 3,
        "GetMD5": True,
        "GetResponseHeader": True,
        "MaxDown": 1048576,
        "AutoDecompress": True,
        "type": 1,
        "isps": [0, 1, 2, 6, 7, 8, 17, 18, 19, 3, 4],
        "pro_ids":
            [
                12, 49, 79, 80, 180, 183, 184, 188, 189, 190, 192, 193, 194, 195, 196, 221, 227,
                235, 236, 238, 241, 243, 250, 346, 349, 350, 351, 353, 354, 355, 356, 357, 239,
                352, 3, 5, 8, 18, 27, 42, 43, 46, 47, 51, 56, 85
            ],
        "areas": [0, 1, 2, 3],
        "SnapShot": True,
        "postfield": "",
        "PingCount": 10,
        "PingSize": 32,
        "SrcIP": ""
    }

    msg = await ws.receive()
    handle_data(msg.data.strip())

    await ws.send_str(json.dumps(data))
    while True:
        msg = await ws.receive()
        if msg.type == aiohttp.WSMsgType.TEXT:
            handle_data(msg.data.strip())
        elif msg.type == aiohttp.WSMsgType.PING:
            ws.pong()
        elif msg.type == aiohttp.WSMsgType.PONG:
            pass
        else:
            if msg.type == aiohttp.WSMsgType.CLOSE:
                logger.info('ws close')
                await ws.close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.info('ws error')
                await ws.close()
                raise Exception('Error during ws receive: {}'.format(ws.exception()))
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                logger.info('ws closed')
                await ws.close()
                break


def main():
    logger.info('================= Start =================')

    try:
        guid = 0
        song_mid = '004JaCzc1KhTrU'
        qqkey = qqapi.qqkey(guid, song_mid)

        if not qqkey:
            raise Exception('No qqkey')

        target = 'http://mobileoc.music.tc.qq.com/M800003MsMD70D1xC9.mp3?guid=0&uin=0&fromtag=53&vkey=' + qqkey
        logger.info('target: {}'.format(target))

        task = request_task(target)
        logger.info('task: {}'.format(task))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(receive_result(task))
    except Exception as err:
        logger.error('Error: {}'.format(err))
        logger.error('Traceback: {}'.format(traceback.format_exc()))
    finally:
        fl.close()


if __name__ == '__main__':
    main()
