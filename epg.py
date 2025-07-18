import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bs4 import BeautifulSoup

# === 频道配置 ===
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels_fh = ["凤凰中文",
               "凤凰资讯",
               "凤凰香港"
]

channels_ltv = {
    "ott-animation": "龍華卡通台",
    "ott-motion": "龍華日韓台"
}

# === 时间设置 ===
now = datetime.utcnow() + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')       # 凤凰台接口日期格式
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')

# === 函数定义 ===
def fetch_epg(channel_id, date_str):
    url = f"https://epg.pw/api/epg.xml?lang=zh-hans&timezone=QXNpYS9TaGFuZ2hhaQ==&date={date_str}&channel_id={channel_id}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

def parse_epg(xml, date_prefix, mode='today'):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(xml)
    programmes = []
    for prog in root.findall('programme'):
        start = prog.attrib.get('start', '')
        stop = prog.attrib.get('stop', '')
        if mode == 'today' and not start.startswith(date_prefix):
            continue
        if mode == 'carry' and not stop.startswith(date_prefix):
            continue
        title = prog.findtext('title') or ''
        desc = prog.findtext('desc') or ''
        programmes.append((start, stop, title, desc))
    return programmes

def parse_time_range(date_str_slash, time_range_str):
    try:
        date_prefix = date_str_slash.replace('/', '-')
        start_str, end_str = [t.strip() for t in time_range_str.split('-')]
        start_dt = datetime.strptime(f"{date_prefix} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_prefix} {end_str}", "%Y-%m-%d %H:%M")
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        start_epg = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        end_epg = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        return start_epg, end_epg
    except Exception as e:
        print(f"[錯誤] 時間解析失敗: {time_range_str}")
        return None, None

def fetch_ltv_programmes():
    url = "https://www.ltv.com.tw/ott%e7%af%80%e7%9b%ae%e8%a1%a8/"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    all_programmes = {}
    for cid in channels_ltv:
        all_programmes[cid] = []
        div = soup.find("div", id=cid)
        if not div:
            print(f"[警告] 找不到频道 {cid} 的节目区块")
            continue

        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            popup_id = popup_href.lstrip("#") if popup_href else None
            popup = soup.find("div", id=popup_id) if popup_id else None

            if not title_tag or not popup:
                continue

            # 获取日期和时间范围
            time_info_tag = popup.select_one(".timetable-time")
            if not time_info_tag:
                continue

            time_info = time_info_tag.get_text(strip=True)
            try:
                date_part = time_info.split()[0]  # 2025/07/17
                time_range = time_info.split()[-1]  # 23:30 - 00:00
            except Exception as e:
                print(f"[錯誤] 時間格式錯誤: {time_info}")
                continue

            title = title_tag.get_text(strip=True)
            desc_tag = popup.select_one(".timetable-desc")
            desc = desc_tag.get_text(strip=True).replace("\xa0", " ") if desc_tag else ""

            start_epg, end_epg = parse_time_range(date_part, time_range)
            if start_epg and end_epg:
                all_programmes[cid].append((start_epg, end_epg, title, desc))

    return all_programmes

# === 创建 epg.xml ===
tv_epg = Element('tv')

# 凤凰台写入
for name in channels_fh:
    real_id = None
    for cid, names in channel_map.items():
        if name in names:
            real_id = cid
            break
    if not real_id:
        continue

    channel_el = SubElement(tv_epg, 'channel', id=real_id)
    display_name = SubElement(channel_el, 'display-name')
    display_name.text = name

    try:
        xml_today = fetch_epg(real_id, date_str_api)
        xml_yesterday = fetch_epg(real_id, yesterday_str_api)
        today_programmes = parse_epg(xml_today, date_str_api, mode='today')
        carryover_programmes = parse_epg(xml_yesterday, date_str_api, mode='carry')

        if today_programmes:
            first_start = today_programmes[0][0]
            if not first_start.endswith("0000"):
                if carryover_programmes:
                    last_prog = carryover_programmes[-1]
                    carry_start = date_str_api + "000000"
                    carry_end = first_start
                    title, desc = last_prog[2], last_prog[3]
                    today_programmes.insert(0, (carry_start, carry_end, title, desc))

        for start, stop, title, desc in today_programmes:
            programme = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=real_id)
            SubElement(programme, 'title').text = title
            if desc:
                SubElement(programme, 'desc').text = desc
    except Exception as e:
        print(f"[错误] 获取频道 {name} 失败：{e}")

# LTV节目信息
ltv_data = fetch_ltv_programmes()

# LTV写入 epg.xml
for cid, cname in channels_ltv.items():
    channel_el = SubElement(tv_epg, 'channel', id=cid)
    SubElement(channel_el, 'display-name').text = cname

    for start, stop, title, desc in ltv_data.get(cid, []):
        programme = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=cid)
        SubElement(programme, 'title').text = title
        if desc:
            SubElement(programme, 'desc').text = desc

# 写入 epg.xml 文件
ElementTree(tv_epg).write('epg.xml', encoding='utf-8', xml_declaration=True)
print("✅ epg.xml 生成成功！")

# === 创建 boss.xml（仅 LTV）===
tv_boss = Element('tv')
for cid, cname in channels_ltv.items():
    channel_el = SubElement(tv_boss, 'channel', id=cid)
    SubElement(channel_el, 'display-name').text = cname

    for start, stop, title, desc in ltv_data.get(cid, []):
        programme = SubElement(tv_boss, 'programme', start=start, stop=stop, channel=cid)
        SubElement(programme, 'title').text = title
        if desc:
            SubElement(programme, 'desc').text = desc

ElementTree(tv_boss).write('boss.xml', encoding='utf-8', xml_declaration=True)
print("✅ boss.xml (LTV專用) 生成成功！")
