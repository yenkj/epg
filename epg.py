import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bs4 import BeautifulSoup

# === 频道配置 ===
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels_api = [
    "凤凰中文",
    "凤凰资讯",
    "凤凰香港"
]

channels_ltv = {
    "ott-animation": "龍華卡通台",
    "ott-motion": "龍華日韓台"
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

now = datetime.utcnow() + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
date_str_html = now.strftime('%Y-%m-%d')


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
        start_str, end_str = [t.strip() for t in time_range_str.split('-')]
        date_prefix = date_str_slash.replace('/', '-')
        start_dt = datetime.strptime(f"{date_prefix} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_prefix} {end_str}", "%Y-%m-%d %H:%M")
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        start_epg = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        end_epg = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        return start_epg, end_epg
    except Exception:
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
            continue
        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            time_tag = item.select_one(".timetable-time")
            desc_tag = item.select_one(".timetable-desc")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            if not title_tag or not time_tag or not popup_href:
                continue
            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True) if desc_tag else ""
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
                all_programmes[cid].append((start_epg, end_epg, title, desc))

    # ✅ 按 start_epg 时间排序
    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x[0])

    return all_programmes


def fetch_json_schedule():
    programmes = []
    for ch_id, info in channels_json.items():
        try:
            data = requests.get(info['url'], timeout=10).json()
            for day in data['list']:
                programme_list = day['values']
                if programme_list and programme_list[0]['time'] != "00:00":
                    programme_list.insert(0, {
                        "name": "無節目資料",
                        "date": day['key'],
                        "time": "00:00"
                    })
                for i, p in enumerate(programme_list):
                    start = datetime.strptime(f"{p['date']} {p['time']}", "%Y-%m-%d %H:%M")
                    if i + 1 < len(programme_list):
                        next_p = programme_list[i+1]
                        end = datetime.strptime(f"{next_p['date']} {next_p['time']}", "%Y-%m-%d %H:%M")
                    else:
                        end = start + timedelta(hours=2)
                    if end <= start:
                        end += timedelta(days=1)
                    programmes.append({
                        "channel": ch_id,
                        "title": p['name'],
                        "start": start,
                        "end": end,
                        "desc": ""
                    })
        except Exception as e:
            print(f"[錯誤] 無法抓取 {ch_id}：{e}")
    return programmes


def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S") + " +0800"


def indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i


def write_xml(element, file_path):
    indent(element)
    tree = ElementTree(element)
    with open(file_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True, short_empty_elements=False)


def main():
    epg_programmes = []
    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if not real_id:
            continue
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
            epg_programmes.extend(today_programmes)
        except Exception as e:
            print(f"[錯誤] {name} 失敗：{e}")

    ltv_programmes = fetch_ltv_programmes()
    json_programmes = fetch_json_schedule()

    # === epg.xml ===
    tv_epg = Element("tv")
    for ch in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and ch in names) or (isinstance(names, str) and ch == names)), None)
        if real_id:
            ch_el = SubElement(tv_epg, "channel", id=real_id)
            SubElement(ch_el, "display-name").text = ch

    for start, stop, title, desc in epg_programmes:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and title in names) or (isinstance(names, str) and title == names)), None)
        if not real_id:
            real_id = "unknown"
        p = SubElement(tv_epg, "programme", start=start, stop=stop, channel=real_id)
        SubElement(p, "title").text = title
        SubElement(p, "desc").text = desc

    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_epg, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        if cid in ltv_programmes:
            for start, stop, title, desc in ltv_programmes[cid]:
                p = SubElement(tv_epg, "programme", start=start, stop=stop, channel=cid)
                SubElement(p, "title").text = title
                SubElement(p, "desc").text = desc

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_epg, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
    for prog in json_programmes:
        p = SubElement(tv_epg, "programme",
                       start=fmt(prog['start']),
                       stop=fmt(prog['end']),
                       channel=prog['channel'])
        SubElement(p, "title").text = prog['title']
        SubElement(p, "desc").text = prog['desc']

    write_xml(tv_epg, "epg.xml")

    # === boss.xml（无描述，仅LTV+JSON） ===
    tv_boss = Element("tv")
    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_boss, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        if cid in ltv_programmes:
            for start, stop, title, _ in ltv_programmes[cid]:
                p = SubElement(tv_boss, "programme", start=start, stop=stop, channel=cid)
                SubElement(p, "title").text = title
                SubElement(p, "desc").text = ""

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_boss, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
    for prog in json_programmes:
        p = SubElement(tv_boss, "programme",
                       start=fmt(prog['start']),
                       stop=fmt(prog['end']),
                       channel=prog['channel'])
        SubElement(p, "title").text = prog['title']
        SubElement(p, "desc").text = ""

    write_xml(tv_boss, "boss.xml")


if __name__ == "__main__":
    main()
