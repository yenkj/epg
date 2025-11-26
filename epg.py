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
            # 获取三天的节目数据
            xml_today = fetch_epg(real_id, date_str_api)
            xml_yesterday = fetch_epg(real_id, yesterday_str_api)
            xml_tomorrow = fetch_epg(real_id, tomorrow_str_api)

            today_programmes = parse_epg(xml_today, date_str_api, mode='today', channel_id=real_id)
            carryover_programmes = parse_epg(xml_yesterday, date_str_api, mode='carry', channel_id=real_id)
            tomorrow_programmes = parse_epg(xml_tomorrow, tomorrow_str_api, mode='carry', channel_id=real_id)

            # 处理前后节目的补充
            if today_programmes:
                first_start = today_programmes[0][0]
                if not first_start.strftime('%H%M') == '0000':
                    if carryover_programmes:
                        last_prog = carryover_programmes[-1]
                        carry_start = datetime.combine(first_start.date(), datetime.min.time()).replace(tzinfo=timezone(timedelta(hours=8)))
                        carry_end = first_start
                        title, desc = last_prog[2], last_prog[3]
                        today_programmes.insert(0, (carry_start, carry_end, title, desc))

            # 合并今天和未来的节目信息
            for start_dt, stop_dt, title, desc in today_programmes + tomorrow_programmes:
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
    url = "https://www.ltv.com.tw/ott%e7%af%80%e7%9b%ae%e8%a1%a8/"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    all_programmes = {}
    for cid in channels_ottltv:
        all_programmes[cid] = []
        div = soup.find("div", id=cid)
        if not div:
            continue
        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            time_tag = item.select_one(".timetable-time")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            if not title_tag or not time_tag or not popup_href:
                continue
            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
            popup_id = popup_href.lstrip("#")
            popup = soup.find("div", id=popup_id)
            if not popup:
                continue
            time_info_tag = popup.select_one(".timetable-time")
            if not time_info_tag:
                continue
            date_part = time_info_tag.get_text(strip=True).split()[0].strip()
            start_epg, end_epg = parse_time_range(date_part, time_range)
            if start_epg and end_epg:
                all_programmes[cid].append({
                    "channel": cid,
                    "start": start_epg,
                    "end": end_epg,
                    "title": title,
                    "desc": ""  # 精简内容明确 with_desc=False，这里留空
                })
    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x["start"])
    return all_programmes

def fetch_modltv_programmes():
    url = "https://www.ltv.com.tw/mod%e7%af%80%e7%9b%ae%e8%a1%a8/"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    all_programmes = {}
    for cid in channels_modltv:
        all_programmes[cid] = []
        div = soup.find("div", id=cid)
        if not div:
            continue
        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            time_tag = item.select_one(".timetable-time")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            if not title_tag or not time_tag or not popup_href:
                continue
            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
            popup_id = popup_href.lstrip("#")
            popup = soup.find("div", id=popup_id)
            if not popup:
                continue
            time_info_tag = popup.select_one(".timetable-time")
            if not time_info_tag:
                continue
            date_part = time_info_tag.get_text(strip=True).split()[0].strip()
            start_epg, end_epg = parse_time_range(date_part, time_range)
            if start_epg and end_epg:
                all_programmes[cid].append({
                    "channel": cid,
                    "start": start_epg,
                    "end": end_epg,
                    "title": title,
                    "desc": ""  # 精简内容明确 with_desc=False，这里留空
                })
    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x["start"])
    return all_programmes

def write_xml(tv_element, file_name):
    tree = ElementTree(tv_element)
    with open(file_name, 'wb') as f:
        tree.write(f)

def main():
    # 获取节目的数据
    epg_programmes = fetch_api_programmes(channels_api, channel_map, date_str_api, yesterday_str_api, tomorrow_str_api)
    tv_epg = Element("tv")
    tv_boss = Element("tv")

    # 处理并写入XML文件
    for prog in epg_programmes:
        prog_element = Element("programme")
        prog_element.set("channel", prog["channel"])
        prog_element.set("start", prog["start"].strftime("%Y%m%d%H%M%S"))
        prog_element.set("stop", prog["end"].strftime("%Y%m%d%H%M%S"))
        
        title_element = SubElement(prog_element, "title")
        title_element.text = prog["title"]
        
        desc_element = SubElement(prog_element, "desc")
        desc_element.text = prog["desc"]

        tv_epg.append(prog_element)

    write_xml(tv_epg, "epg.xml")
    write_xml(tv_boss, "boss.xml")

if __name__ == "__main__":
    main()
