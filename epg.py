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

# === JSON 新增频道配置 ===
channels_json = {
    "meya-movie-hd": {
        "name": "美亞電影HD",
        "url": "https://xn--i0yt6h0rn.tw/channel/美亞電影HD/index.json"
    },
    # 你可以按需继续添加新的 JSON 源
}

# === 时间设置 ===
now = datetime.utcnow() + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')       # epg.pw的api接口日期格式
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
date_str_html = now.strftime('%Y-%m-%d')     # LTV 页面日期格式

# --- epg.pw API 抓取 ---
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

# --- LTV 网站抓取 ---
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
    except Exception as e:
        print(f"[錯誤] 時間解析失敗: {date_str_slash} {time_range_str}")
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
            time_tag = item.select_one(".timetable-time")
            desc_tag = item.select_one(".timetable-desc")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None

            if not title_tag or not time_tag or not popup_href:
                continue

            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            # 从弹窗中取出真实日期
            popup_id = popup_href.lstrip("#")
            popup = soup.find("div", id=popup_id)
            if not popup:
                print(f"[警告] 找不到 popup：{popup_id}")
                continue
            time_info_tag = popup.select_one(".timetable-time")
            if not time_info_tag:
                print(f"[警告] popup {popup_id} 中找不到時間")
                continue
            time_info = time_info_tag.get_text(strip=True)
            date_part = time_info.split()[0].strip()

            start_epg, end_epg = parse_time_range(date_part, time_range)
            if start_epg and end_epg:
                all_programmes[cid].append((start_epg, end_epg, title, desc))
    return all_programmes

# --- JSON 新源抓取 ---
def fetch_json_schedule():
    programmes = []
    for ch_id, info in channels_json.items():
        try:
            data = requests.get(info['url'], timeout=10).json()
            for day in data['list']:
                day_str = day['key']
                programme_list = day['values']

                # 若第一節目非00:00，自動補"無節目資料"
                if programme_list and programme_list[0]['time'] != "00:00":
                    filler = {
                        "name": "無節目資料",
                        "date": day_str,
                        "time": "00:00"
                    }
                    programme_list.insert(0, filler)

                for i, p in enumerate(programme_list):
                    start = datetime.strptime(f"{p['date']} {p['time']}", "%Y-%m-%d %H:%M")

                    if i + 1 < len(programme_list):
                        end_raw = programme_list[i+1]
                        end = datetime.strptime(f"{end_raw['date']} {end_raw['time']}", "%Y-%m-%d %H:%M")
                    else:
                        end = start + timedelta(hours=2)

                    # 處理跨天節目（end 時間早於 start）
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
            print(f"Failed to fetch JSON source {ch_id}: {e}")

    return programmes

def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S") + " +0800"

# --- 写入 XML ---
def write_epg(all_programmes, filename, included_channels=None):
    tv = Element("tv")
    channels_written = set()

    for prog in all_programmes:
        ch_id = prog['channel'] if isinstance(prog, dict) else prog[3] if len(prog) > 3 else None
        if isinstance(prog, tuple):
            # epg.pw和ltv的节目数据格式为元组 (start, stop, title, desc)
            start, stop, title, desc = prog
            ch_id = None  # 下面再用real id匹配
        else:
            start = fmt(prog['start'])
            stop = fmt(prog['end'])
            title = prog['title']
            desc = prog['desc']

        # 根据来源不同取频道ID
        if ch_id is None:
            # epg.pw数据没带频道id，只能用写死的方式
            # 这里直接跳过，后面写入时分别处理
            continue

        if included_channels and ch_id not in included_channels:
            continue

        if ch_id not in channels_written:
            display_name = ""
            # 优先从 channel_map 找名字
            if ch_id in channel_map:
                display_name = channel_map[ch_id][0] if isinstance(channel_map[ch_id], list) else channel_map[ch_id]
            elif ch_id in channels_ltv:
                display_name = channels_ltv[ch_id]
            elif ch_id in channels_json:
                display_name = channels_json[ch_id]['name']
            else:
                display_name = ch_id
            ch_el = SubElement(tv, "channel", id=ch_id)
            SubElement(ch_el, "display-name").text = display_name
            channels_written.add(ch_id)

        p_el = SubElement(tv, "programme", {
            "start": start,
            "stop": stop,
            "channel": ch_id
        })
        SubElement(p_el, "title").text = title
        SubElement(p_el, "desc").text = desc

    tree = ElementTree(tv)
    tree.write(filename, encoding="utf-8", xml_declaration=True)

# --- 主程序 ---
def main():
    # 1. epg.pw API 数据抓取
    epg_programmes = []
    for name in channels_api:
        real_id = None
        for cid, names in channel_map.items():
            # channel_map里名字是列表或字符串都兼容
            if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names):
                real_id = cid
                break
        if not real_id:
            continue

        try:
            xml_today = fetch_epg(real_id, date_str_api)
            xml_yesterday = fetch_epg(real_id, yesterday_str_api)
            today_programmes = parse_epg(xml_today, date_str_api, mode='today')
            carryover_programmes = parse_epg(xml_yesterday, date_str_api, mode='carry')

            # 跨日补齐逻辑
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
            print(f"[错误] 获取频道 {name} 失败：{e}")

    # 2. LTV 数据抓取
    ltv_programmes = fetch_ltv_programmes()

    # 3. JSON 新源抓取
    json_programmes = fetch_json_schedule()

    # 4. 写入 epg.xml (包含 epg.pw, LTV, JSON)
    tv_epg = Element('tv')

    # 写 epg.pw 的频道和节目
    for name in channels_api:
        real_id = None
        for cid, names in channel_map.items():
            if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names):
                real_id = cid
                break
        if not real_id:
            continue
        channel_el = SubElement(tv_epg, 'channel', id=real_id)
        SubElement(channel_el, 'display-name').text = name

    for start, stop, title, desc in epg_programmes:
        # 频道id信息epg.pw已有，使用上面循环时已添加频道
        real_id = None
        # 先找对应的channel_id
        for cid, names in channel_map.items():
            if (isinstance(names, list) and title in names) or (isinstance(names, str) and title == names):
                real_id = cid
                break
        # 这里用之前找到的频道id
        if real_id is None:
            real_id = channels_api[0] # 默认放第一个频道，避免空值
        p = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=real_id)
        SubElement(p, 'title').text = title
        SubElement(p, 'desc').text = desc

    # 写 LTV 频道和节目
    for cid, cname in channels_ltv.items():
        channel_el = SubElement(tv_epg, 'channel', id=cid)
        SubElement(channel_el, 'display-name').text = cname
        if cid in ltv_programmes:
            for start, stop, title, desc in ltv_programmes[cid]:
                p = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=cid)
                SubElement(p, 'title').text = title
                SubElement(p, 'desc').text = desc

    # 写 JSON 频道和节目
    for ch_id, info in channels_json.items():
        channel_el = SubElement(tv_epg, 'channel', id=ch_id)
        SubElement(channel_el, 'display-name').text = info['name']
    for prog in json_programmes:
        p = SubElement(tv_epg, 'programme',
                      start=fmt(prog['start']),
                      stop=fmt(prog['end']),
                      channel=prog['channel'])
        SubElement(p, 'title').text = prog['title']
        SubElement(p, 'desc').text = prog['desc']

    # 写 epg.xml 文件
    ElementTree(tv_epg).write('epg.xml', encoding='utf-8', xml_declaration=True)

    # 5. 写 boss.xml 只含 LTV 和 JSON 的频道（无描述）
    tv_boss = Element('tv')

    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_boss, 'channel', id=cid)
        SubElement(ch_el, 'display-name').text = cname
        if cid in ltv_programmes:
            for start, stop, title, _ in ltv_programmes[cid]:
                p = SubElement(tv_boss, 'programme', start=start, stop=stop, channel=cid)
                SubElement(p, 'title').text = title
                SubElement(p, 'desc').text = ""

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_boss, 'channel', id=ch_id)
        SubElement(ch_el, 'display-name').text = info['name']

    for prog in json_programmes:
        p = SubElement(tv_boss, 'programme', start=fmt(prog['start']), stop=fmt(prog['end']), channel=prog['channel'])
        SubElement(p, 'title').text = prog['title']
        SubElement(p, 'desc').text = ""

    ElementTree(tv_boss).write('boss.xml', encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    main()
