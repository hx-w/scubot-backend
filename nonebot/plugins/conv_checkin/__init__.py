import nonebot
import json
import redis
import datetime
import time
import requests

redis_inst: redis.Redis = redis.Redis(
    host='scubot-redis', port=6379, decode_responses=True, password="811021")

# serverless_url = 'https://service-0wsl5m13-1256946954.cd.apigw.tencentcs.com/release/'
serverless_url = 'http://scubot-scripts:7777'

bot: nonebot.NoneBot = nonebot.get_bot()


@nonebot.on_request('friend')
async def _(session: nonebot.RequestSession):
    if '7355608' in session.event.comment:
        await session.approve()
        return
    await session.reject('请填写正确的邀请码')

@nonebot.scheduler.scheduled_job('cron', minute="*")
async def handler_timer():
    keylist = redis_inst.keys("scubot-*")
    nowtime = datetime.datetime.now().strftime("%H:%M")
    if keylist == None or len(keylist) == 0:
        return
    packlist = redis_inst.mget(keylist)
    validlist = []
    for pack in packlist:
        pack_dict = json.loads(pack)
        if pack_dict['triggerTime'] == nowtime:
            validlist.append(pack_dict)

    qq_list = list(map(lambda x: x["user_id"], await bot.get_friend_list()))
    for pack_dict in validlist:
        print('命中', pack_dict['qqid'])
        valid_qq = False
        qqid = pack_dict["qqid"].strip()
        if len(qqid) > 0 and int(qqid) in qq_list:
            valid_qq = True
        try:
            postdata = {
                'content': pack_dict,
                'token': '811021'
            }
            resp = requests.post(f'{serverless_url}/checkin', data=json.dumps(
                postdata))
            assert resp.status_code == 200, resp.status_code
            res = json.loads(resp.content.decode('utf-8'))
            print(res["message"], res["detail_json"]["area"])

            if int(res['status']) != 0:
                print('serverless success, but failed from wfw')
                if valid_qq:
                    await bot.send_private_msg(user_id=int(qqid), message=f'SCU健康每日报打卡脚本错误\n{res["message"]}')
                else:
                    await bot.send_private_msg(user_id=765892480, message=f'出现错误: {res["message"]}')
                redis_inst.set(f'checkinLog-{pack_dict["uid"]}-{int(time.time())}', json.dumps({
                    'uid': pack_dict["uid"],
                    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    'time': datetime.datetime.now().strftime("%H:%M:%S"),
                    'status': 2,
                    'result': res['message'],
                    'area': res['detail_json']['area'],
                    'notified': valid_qq,
                    'ip': res['ip']
                }), ex=72*60*60)
                continue

            redis_inst.set(f'checkinLog-{pack_dict["uid"]}-{int(time.time())}', json.dumps({
                'uid': pack_dict["uid"],
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                'time': datetime.datetime.now().strftime("%H:%M:%S"),
                'status': 0 if '操作成功' in res['message'] else 1,
                'result': res['message'],
                'area': res['detail_json']['area'],
                'notified': valid_qq,
                'ip': res['ip']
            }), ex=72*60*60)
            if valid_qq:
                # sfzx = '是' if res['detail_json']['sfzx'] else '否'
                await bot.send_private_msg(user_id=int(qqid), message=f'SCU健康每日报打卡结束\n[状态] {res["message"]}\n[地点] {res["detail_json"]["area"]}\n[IP] {res["ip"]}')
        except Exception as ept:
            print(f'failed {ept}')
            if valid_qq:
                await bot.send_private_msg(user_id=int(qqid), message=f'SCU健康每日报打卡脚本错误\n{ept}')
            else:
                await bot.send_private_msg(user_id=765892480, message=f'出现错误: {ept}')
            redis_inst.set(f'checkinLog-{pack_dict["uid"]}-{int(time.time())}', json.dumps({
                'uid': pack_dict["uid"],
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                'time': datetime.datetime.now().strftime("%H:%M:%S"),
                'status': 2,
                'result': f'{ept}',
                'area': 'Unknown',
                'notified': valid_qq,
            }), ex=72*60*60)
