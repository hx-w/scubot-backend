import json
import re
import datetime
import time
import requests
import socket
import random


def disturb_location(lat: float, lng: float, T: float=0.00045) -> tuple:
    _raw = (random.random() % (2 * T)) - T
    if abs(_raw) < (T / 2): _raw = 0.
    print('raw:', _raw)
    return (lat + _raw, lng + _raw)

def get_host_ip():
    return '43.136.171.6'
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(('8.8.8.8',80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_area(lat: float, lng: float):
    resp = requests.get(f'https://api.map.baidu.com/reverse_geocoding/v3/?output=json&coordtype=wgs84ll&ak=0hYGiH3Ob5ZhV0eWzrGVXCD3bEdBCi6L&location={lat},{lng}')
    addr = json.loads(resp.content.decode('utf-8'))['result']['addressComponent']
    return addr


def generate_template(pack: dict) -> tuple:
    cookies_dict = pack['cookies']
    session = requests.session()
    cookiesJar = requests.utils.cookiejar_from_dict(
        cookies_dict, cookiejar=None, overwrite=True)
    session.cookies = cookiesJar
    url = 'https://wfw.scu.edu.cn/ncov/wap/default/index'

    resp = session.get(url=url, headers={
        'User-Agent': pack['userAgent']
    })

    if resp.status_code != 200:
        print('[ERROR]', resp.status_code)
        return False, f'模拟登录失败: {resp.status_code}'

    html = resp.content.decode('utf-8')

    pattern = re.compile('var def =(.*);!?')

    res = re.findall(pattern, html)
    if len(res) == 0:
        return False, f'模拟登录失败：无法获取个人信息模板'
    res_json = json.loads(res[0])
    if type(res_json['geo_api_info']) == str:
        try:
            res_json['geo_api_info'] = json.loads(res_json['geo_api_info'])
        except: res_json['geo_api_info'] = {
            "type": "complete",
    "position": {
        "Q": 30.630839301216,
        "R": 104.079966362848,
        "lng": 104.07997,
        "lat": 30.630839
    },
    "location_type": "ip",
    "message": "Get ipLocation success.Get address success.",
    "isConverted": True,
    "status": 1,
    "formattedAddress": "四川省成都市武侯区望江路街道四川大学四川大学望江校区研究生院",
    "roads": [],
    "crosses": [],
    "pois": [],
    "info": "SUCCESS"
        }
    return True, (res_json, session)


def modify_json(res_json: dict, pack: dict) -> dict:
    # load default geo_api_info
    res_json['geo_api_info']['position'] = {
            "Q": float(pack['location']['lat']),
            "R": float(pack['location']['lng']),
            "lng": float(pack['location']['lat']),
            "lat": float(pack['location']['lng'])
        }
    res_json['geo_api_info']['addressComponent'] =  get_area(float(pack['location']['lat']), float(pack['location']['lng']))

    res_json['province'] = res_json['geo_api_info']['addressComponent']['province']
    res_json['city'] = res_json['geo_api_info']['addressComponent']['city']
    res_json['address'] = res_json['geo_api_info']['formattedAddress']
    res_json['area'] = ' '.join([
        res_json['province'],
        res_json['city'],
        res_json['geo_api_info']['addressComponent']['district']
    ])
    res_json['date'] = datetime.datetime.now().strftime("%Y%m%d")
    res_json['created'] = int(time.time())
    res_json['ismoved'] = 0
    return res_json


def checkin(pack: dict) -> dict:
    message = ''
    success, ret =  generate_template(pack)
    # disturb lat & lng with T=0.00045
    print('origin:', pack['location'])
    pack['location']['lat'], pack['location']['lng'] = disturb_location(float(pack['location']['lat']), float(pack['location']['lng']))
    print('disturbed:', pack['location']) 
    if not success:
        message += f'[打卡失败] {ret}'
        return {'status': '1', 'message': message}
    

    res_json, session = ret
    res_json =  modify_json(res_json, pack)
    # post checkin data
    url = 'https://wfw.scu.edu.cn/ncov/wap/default/save'
    resp = session.post(url=url, data=res_json, headers={'User-Agent': pack['userAgent']})
    ip = get_host_ip()
    if resp.status_code == 200:
        resp_json = json.loads(resp.content.decode('utf-8'))
        return {
            "status": "0",
            "message": f'{resp_json["m"]}',
            "detail_json": res_json,
            "ip": ip
        }
    else:
        return {
            "status": "1",
            "message": f'{resp.status_code} {resp.content.decode("utf-8")}',
            "detail_json": res_json,
            "ip": ip
        }
