#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import socket
import time
from urllib import request, error, parse
from config import read_config, save_config, check_config, cfg
from get_ip import get_ip


def header():
    h = {
        'User-Agent': 'Client/0.0.1 ({})'.format(cfg['email'])
    }
    return h


def get_record_ids():
    sub_domains = cfg['sub_domain'].split(",")
    url = 'https://dnsapi.cn/Record.List'
    params = parse.urlencode({
        'login_token': cfg['login_token'],
        'format': 'json',
        'domain': cfg['domain']
    })
    req = request.Request(
        url=url, data=params.encode('utf-8'), method='POST', headers=header())
    try:
        resp = request.urlopen(req).read().decode()
    except (error.HTTPError, error.URLError, socket.timeout):
        return None
    records = json.loads(resp).get('records', {})
    for item in records:
        sd_name = item.get('name')
        if sd_name in sub_domains:
            cfg[sd_name] = item.get('id')
            logging.info(
                "get record_id: %s for sub_domain %s" % (
                    item.get('id'), sd_name))
    return None


def update_records():
    for sd_name in cfg['sub_domain'].split(","):
        url = 'https://dnsapi.cn/Record.Ddns'
        params = parse.urlencode({
            'login_token': cfg['login_token'],
            'format': 'json',
            'domain': cfg['domain'],
            'sub_domain': sd_name,
            'record_id': cfg[sd_name],
            'record_line': '默认'
        })
        print(params)
        req = request.Request(
            url=url, data=params.encode('utf-8'),
            method='POST', headers=header())
        resp = request.urlopen(req).read().decode()
        records = json.loads(resp)
        cfg['last_update_time'] = str(time.gmtime())
        logging.info("record updated: %s" % records)


# async def main():
def main():
    interval = 5
    ip_count = 1
    ip_pool = []
    try:
        interval = int(cfg['interval'])
        ip_count = int(cfg['ip_count'])
        ip_pool = cfg['ip_pool'].split(',')[:ip_count]
    except ValueError:
        pass
    while 1:
        current_ip = get_ip()
        if current_ip:
            # 对于拥有多个出口 IP 负载均衡的服务器，上面的 get_ip() 函数会在几个 ip 之间不停切换
            # 然后频繁进入这个判断，进行 update_record()，然后很快就会触发 API Limited 了
            # 于是建立一个IP池记载这个服务器的几个出口IP，以免频繁切换
            if current_ip not in ip_pool:
                # new ip found
                logging.info("new ip found: %s", current_ip)
                cfg['current_ip'] = current_ip
                ip_pool.insert(0, current_ip)
                cfg['ip_pool'] = ','.join([str(x) for x in ip_pool[:ip_count]])
                update_records()
                save_config()
        else:
            logging.error('get current ip FAILED.')
        # await asyncio.sleep(interval)
        time.sleep(interval)

def ask_exit(_sig_name):
        logging.warning('got signal {}: exit'.format(_sig_name))
        loop.stop()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s : %(message)s')
    logging.info('start...')
    read_config()
    check_config()
    cfg['record_id'] = get_record_ids()
    logging.info("watching ip for ddns: %s.%s" % (cfg['sub_domain'], cfg['domain']))
    main()
