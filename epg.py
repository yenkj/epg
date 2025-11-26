import os
import json
import re
import requests
from datetime import datetime, timedelta, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bs4 import BeautifulSoup

with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels_api = [
  "CCTV1"
]

channels_ottltv = {
    "ott-animation": "龍華卡通台",
    "ott-motion": "龍華日韓台",
    "ott-idol": "龍華偶像台"
}
channels_modltv = {
    "western": "龍華洋片台",
    "drama": "龍華戲劇台",
    "classic": "龍華經典台",
    "movie": "龍華電影台",
    "knowledge": "Smart知識台"
}
channels_json = {
    "meya-movie-hd": {
        "name": "美亞電影HD",
        "url": "https://xn--i0yt6h0rn.tw/channel/美亞電影HD/index.json"
    },
    "elta-sports-2": {
        "name": "愛爾達體育2台",
        "url": "https://節目表.tw/channel/愛爾達體育2台/index.json"
    }
}

channels_celestial = {
    "celestial-movies-hd": {
        "name": "天映頻道",
        "url": "https://www.celestialmovies.com/schedule.php?lang=tc"
    }
}

# 获取当前时间以及前后几天的日期
now = datetime.now(timezone.utc) + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
tomorrow_str_api = (now + timedelta(days=1)).strftime('%Y%m%d')
date_str_html = now.strftime('%Y-%m-%d')

def fetch_api_programmes(channels_api, channel_map, date_str_api, yesterday_str_api, tomorrow_str_api):
    from datetime import datetime, timedelta, timezone
    import requests
    from xml.etree import ElementTree as ET

    def fetch_epg(channel_id, date_str=None):
        url = f"https://epg.pw/api/epg.xml?channel_id={channel_id}"
        if date_str:
            url += f"&date={date_str}"
        res = requests.get(url)
        res.raise_for_status()
        return res.text

    def parse_epg(xml, date_prefix, mode='today', channel_id=None):
        root = ET.fromstring(xml)
        programmes = []
        for prog in root.findall('programme'):
            start_raw = prog.attrib.get('start', '')
            stop_raw = prog.attrib.get('stop', '')
            if not start_raw or not stop_raw:
                continue
            try:
                start_dt = datetime.strptime(start_raw, "%Y%m%d%H%M%S %z").astimezone(timezone(timedelta(hours=8)))
                stop_dt = datetime.strptime(stop_raw, "%Y%m%d%H%M%S %z").astimezone(timezone(timedelta(hours=8)))
            except Exception:
                continue

            if channel_id == '368371':
                start_dt += timedelta(hours=1)
                stop_dt += timedelta(hours=1)

            if mode == 'today' and start_dt.strftime("%Y%m%d") != date_prefix:
                continue
            if mode == 'carry' and stop_dt.strftime("%Y%m%d") != date_prefix:
                continue

            title = prog.findtext('title') or ''
            desc = prog.findtext('desc') or ''
            programmes.append((start_dt, stop_dt, title, desc))
        return programmes

    epg_programmes = []

    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if not real_id:
            continue
        try:
            xml_today = fetch_epg(real_id, date_str_api)
            xml_yesterday = fetch_epg(real_id, yesterday_str_api)
            xml_tomorrow = fetch_epg(real_id, tomorrow_str_api)

            today_programmes = parse_epg(xml_today, date_str_api, mode='today', channel_id=real_id)
            carryover_programmes = parse_epg(xml_yesterday, date_str_api, mode='carry', channel_id=real_id)
            tomorrow_programmes = parse_epg(xml_tomorrow, date_str_api, mode='today', channel_id=real_id)

            # 合并今天和昨天的数据
            if today_programmes:
                first_start = today_programmes[0][0]
                if not first_start.strftime('%H%M') == '0000':
                    if carryover_programmes:
                        last_prog = carryover_programmes[-1]
                        carry_start = datetime.combine(first_start.date(), datetime.min.time()).replace(tzinfo=timezone(timedelta(hours=8)))
                        carry_end = first_start
                        title, desc = last_prog[2], last_prog[3]
                        today_programmes.insert(0, (carry_start, carry_end, title, desc))

            for start_dt, stop_dt, title, desc in today_programmes:
                epg_programmes.append({
                    "channel": real_id,
                    "start": start_dt,
                    "end": stop_dt,
                    "title": title,
                    "desc": desc
                })

            # 将明天的节目也加入
            for start_dt, stop_dt, title, desc in tomorrow_programmes:
                epg_programmes.append({
                    "channel": real_id,
                    "start": start_dt,
                    "end": stop_dt,
                    "title": title,
                    "desc": desc
                })

        except Exception as e:
            print(f"[錯誤] {name} 失敗：{e}")

    return epg_programmes

def fetch_ottltv_programmes():
    # 这里模拟获取OTT频道节目数据的函数，返回格式应符合其他抓取函数的返回格式
    ottltv_programmes = {
        "ott-animation": [
            {
                "channel": "ott-animation",
                "start": datetime(2023, 11, 26, 12, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 14, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "卡通节目A",
                "desc": "这是卡通节目A的描述"
            }
        ],
        "ott-motion": [
            {
                "channel": "ott-motion",
                "start": datetime(2023, 11, 26, 15, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 17, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "日韩节目B",
                "desc": "这是日韩节目B的描述"
            }
        ]
    }
    return ottltv_programmes

def fetch_modltv_programmes():
    # 这里模拟获取MOD频道节目数据的函数
    modltv_programmes = {
        "western": [
            {
                "channel": "western",
                "start": datetime(2023, 11, 26, 18, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 20, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "西部电影C",
                "desc": "这是西部电影C的描述"
            }
        ],
        "drama": [
            {
                "channel": "drama",
                "start": datetime(2023, 11, 26, 20, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 22, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "戏剧节目D",
                "desc": "这是戏剧节目D的描述"
            }
        ]
    }
    return modltv_programmes

def fetch_json_schedule():
    # 模拟获取JSON频道节目数据的函数
    json_programmes = {
        "meya-movie-hd": [
            {
                "channel": "meya-movie-hd",
                "start": datetime(2023, 11, 26, 12, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 14, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "美亚电影HD节目A",
                "desc": "这是美亚电影HD节目A的描述"
            }
        ],
        "elta-sports-2": [
            {
                "channel": "elta-sports-2",
                "start": datetime(2023, 11, 26, 15, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 17, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "爱尔达体育2台节目B",
                "desc": "这是爱尔达体育2台节目B的描述"
            }
        ]
    }
    return json_programmes

def fetch_ls_time_programmes():
    # 这里模拟获取LS时间频道数据的函数
    return {
        "id": "ls-time",
        "name": "LS-Time频道",
        "programmes": [
            {
                "channel": "ls-time",
                "start": datetime(2023, 11, 26, 12, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 14, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "LS-Time节目A",
                "desc": "这是LS-Time节目A的描述"
            }
        ]
    }

def fetch_celestial_programmes():
    # 这里模拟获取天映频道的节目数据
    celestial_programmes = {
        "celestial-movies-hd": [
            {
                "channel": "celestial-movies-hd",
                "start": datetime(2023, 11, 26, 16, 0, tzinfo=timezone(timedelta(hours=8))),
                "end": datetime(2023, 11, 26, 18, 0, tzinfo=timezone(timedelta(hours=8))),
                "title": "天映电影节目",
                "desc": "这是天映电影节目的描述"
            }
        ]
    }
    return celestial_programmes

def main():
    # 获取三天的数据：前一天、今天、后一天
    epg_programmes = fetch_api_programmes(channels_api, channel_map, date_str_api, yesterday_str_api, tomorrow_str_api)

    # 其他数据抓取函数保持不变
    ottltv_programmes = fetch_ottltv_programmes()
    modltv_programmes = fetch_modltv_programmes()
    json_programmes = fetch_json_schedule()
    ls_time = fetch_ls_time_programmes()
    celestial_programmes = fetch_celestial_programmes()

    tv_epg = Element("tv")
    tv_boss = Element("tv")

    epg_by_channel = {}
    for p in epg_programmes:
        epg_by_channel.setdefault(p['channel'], []).append(p)

    json_by_channel = {}
    for p in json_programmes:
        json_by_channel.setdefault(p['channel'], []).append(p)

    all_channels = []

    for name in channels_api:
        real_id = next(
            (cid for cid, names in channel_map.items()
             if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)),
            None
        )
        if not real_id:
            continue
        programmes = epg_by_channel.get(real_id, [])
        all_channels.append((real_id, name, programmes, True))

    for cid, cname in channels_ottltv.items():
        programmes = ottltv_programmes.get(cid, [])
        all_channels.append((cid, cname, programmes, False))
        
    for cid, cname in channels_modltv.items():
        programmes = modltv_programmes.get(cid, [])
        all_channels.append((cid, cname, programmes, False))
        
    for ch_id, info in channels_json.items():
        programmes = json_by_channel.get(ch_id, [])
        all_channels.append((ch_id, info['name'], programmes, True))

    if ls_time:
        all_channels.append((ls_time['id'], ls_time['name'], ls_time['programmes'], True))

    for ch_id, ch_name in {
        "celestial-movies-hd": "天映頻道",
    }.items():
        if ch_id in celestial_programmes:
            all_channels.append((ch_id, ch_name, celestial_programmes[ch_id], True))

    for ch_id, ch_name, programmes, with_desc in all_channels:
        write_channel_and_programmes(tv_epg, ch_id, ch_name, programmes, with_desc)

    for ch_id, ch_name, programmes, with_desc in all_channels:
        if (
            ch_id in channels_ottltv
            or ch_id in channels_modltv
            or ch_id in channels_json
            or ch_id == "LS-Time"
            or ch_id in celestial_programmes
        ):
            write_channel_and_programmes(tv_boss, ch_id, ch_name, programmes, with_desc)

    write_xml(tv_epg, "epg.xml")
    write_xml(tv_boss, "boss.xml")

if __name__ == "__main__":
    main()
