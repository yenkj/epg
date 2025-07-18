import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree

# 1. 载入epg.pw频道映射
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

# 2. 凤凰频道列表（中文名）
channels = [
    "凤凰中文",
    "凤凰资讯",
    "凤凰香港"
]

# 3. 额外频道（channel_id => name）
boss_channels = {
    "187": "博斯運動一台",
    "198": "愛爾達體育2台",
    "259": "愛爾達影劇台"
}

# 4. 当前北京时间
today = datetime.utcnow() + timedelta(hours=8)
date_str = today.strftime('%Y%m%d')
yesterday_str = (today - timedelta(days=1)).strftime('%Y%m%d')

# 5. 创建两个根节点
tv_all = Element('tv')     # epg.xml
tv_boss = Element('tv')    # boss.xml

# ========== epg.pw频道 ==========
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

for name in channels:
    real_id = next((cid for cid, names in channel_map.items() if name in names), None)
    if not real_id:
        continue

    # 添加频道到 tv_all
    ch = SubElement(tv_all, 'channel', id=real_id)
    SubElement(ch, 'display-name').text = name

    try:
        xml_today = fetch_epg(real_id, date_str)
        xml_yesterday = fetch_epg(real_id, yesterday_str)

        today_programmes = parse_epg(xml_today, date_str, mode='today')
        carryover_programmes = parse_epg(xml_yesterday, date_str, mode='carry')

        # 若非00:00开始补前一个节目
        if today_programmes:
            first_start = today_programmes[0][0]
            if not first_start.endswith("0000") and carryover_programmes:
                last_prog = carryover_programmes[-1]
                carry_start = date_str + "000000"
                carry_end = first_start
                title, desc = last_prog[2], last_prog[3]
                today_programmes.insert(0, (carry_start, carry_end, title, desc))

        for start, stop, title, desc in today_programmes:
            p = SubElement(tv_all, 'programme', start=start, stop=stop, channel=real_id)
            SubElement(p, 'title').text = title
            if desc:
                SubElement(p, 'desc').text = desc

    except Exception as e:
        print(f"[错误] 获取频道 {name} 失败：{e}")

# ========== 额外频道（同时写入 tv_all 和 tv_boss） ==========
import re

def fetch_boss_schedule(channel_id):
    url = f"https://tvking.funorange.com.tw/channel/{channel_id}"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    html = res.text
    match = re.search(r'scheduleList:\s*(\[\{.*?\}\]),\s*\n', html, re.DOTALL)
    if not match:
        return []
    return json.loads(match.group(1))

for cid, name in boss_channels.items():
    # 添加频道节点到两个 XML
    ch_all = SubElement(tv_all, 'channel', id=cid)
    SubElement(ch_all, 'display-name').text = name

    ch_boss = SubElement(tv_boss, 'channel', id=cid)
    SubElement(ch_boss, 'display-name').text = name

    try:
        schedule = fetch_boss_schedule(cid)
        for day in schedule:
            date = day["date"]
            for prog in day["programList"]:
                if "timeS" not in prog or "timeE" not in prog:
                    continue
                time_start = datetime.strptime(f"{date} {prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                time_end = datetime.strptime(f"{date} {prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                if time_end <= time_start:
                    time_end += timedelta(days=1)
                start_str = time_start.strftime("%Y%m%d%H%M%S") + " +0800"
                stop_str = time_end.strftime("%Y%m%d%H%M%S") + " +0800"

                for root in [tv_all, tv_boss]:
                    p = SubElement(root, 'programme', start=start_str, stop=stop_str, channel=cid)
                    SubElement(p, 'title').text = prog["program"]

    except Exception as e:
        print(f"[错误] 抓取额外频道 {name} 失败：{e}")

# ========== 写入 epg.xml 和 boss.xml ==========
ElementTree(tv_all).write('epg.xml', encoding='utf-8', xml_declaration=True)
ElementTree(tv_boss).write('boss.xml', encoding='utf-8', xml_declaration=True)

print("✅ epg.xml 和 boss.xml 已生成成功")
