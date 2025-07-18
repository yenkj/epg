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
  "凤凰中文",
  "A&E_East",
  "ACC-Network",
  "AMC_East",
  "American-Heroes-Channel"
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

now = datetime.now(timezone.utc) + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
date_str_html = now.strftime('%Y-%m-%d')

def fetch_epg(channel_id, date_str):
    url = f"https://epg.pw/api/epg.xml?channel_id={channel_id}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

def parse_epg(xml, date_prefix, mode='today'):
    from xml.etree import ElementTree as ET
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

        if mode == 'today' and start_dt.strftime("%Y%m%d") != date_prefix:
            continue
        if mode == 'carry' and stop_dt.strftime("%Y%m%d") != date_prefix:
            continue

        title = prog.findtext('title') or ''
        desc = prog.findtext('desc') or ''
        programmes.append((start_dt, stop_dt, title, desc))
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
    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x[0])
    return all_programmes

def fetch_json_schedule():
    programmes = []
    for ch_id, info in channels_json.items():
        try:
            data = requests.get(info['url'], timeout=10).json()
            for i_day, day in enumerate(data['list']):
                programme_list = day['values']

                # 记录第一节目时间（后面再补空）
                real_first_start = None
                if programme_list:
                    real_first_start = datetime.strptime(f"{programme_list[0]['date']} {programme_list[0]['time']}", "%Y-%m-%d %H:%M")

                # 预先计算下一天第一个节目的开始时间
                next_day_start = None
                if i_day + 1 < len(data['list']):
                    next_day = data['list'][i_day + 1]
                    next_prog_list = next_day['values']
                    if next_prog_list:
                        first_prog = next_prog_list[0]
                        next_day_start = datetime.strptime(f"{first_prog['date']} {first_prog['time']}", "%Y-%m-%d %H:%M")

                for i, p in enumerate(programme_list):
                    start = datetime.strptime(f"{p['date']} {p['time']}", "%Y-%m-%d %H:%M")

                    if i + 1 < len(programme_list):
                        next_p = programme_list[i + 1]
                        end = datetime.strptime(f"{next_p['date']} {next_p['time']}", "%Y-%m-%d %H:%M")
                    else:
                        # 最后一个节目，优先用下一天第一个节目开始时间作为结束时间
                        if next_day_start and next_day_start > start:
                            end = next_day_start
                        else:
                            end = start + timedelta(hours=2)

                    if end <= start:
                        end += timedelta(days=1)

                    # 处理跨天拆分
                    if end.date() > start.date():
                        midnight = datetime.combine(end.date(), datetime.min.time())  # 次日 00:00:00
                        # 第一段：当天结束到午夜
                        programmes.append({
                            "channel": ch_id,
                            "title": p['name'],
                            "start": start,
                            "end": midnight,
                            "desc": ""
                        })
                        # 第二段：午夜到结束时间
                        programmes.append({
                            "channel": ch_id,
                            "title": p['name'],
                            "start": midnight,
                            "end": end,
                            "desc": ""
                        })
                    else:
                        programmes.append({
                            "channel": ch_id,
                            "title": p['name'],
                            "start": start,
                            "end": end,
                            "desc": ""
                        })

                # 插入 00:00 的無節目資料（避免與跨天節目重疊）
                if real_first_start:
                    day_start = datetime.combine(real_first_start.date(), datetime.min.time())
                    if real_first_start > day_start:
                        # 检查已有节目是否覆盖这段时间
                        has_overlap = any(
                            prog['channel'] == ch_id and
                            prog['start'] < real_first_start and
                            prog['end'] > day_start
                            for prog in programmes
                        )
                        if not has_overlap:
                            programmes.append({
                                "channel": ch_id,
                                "title": "無節目資料",
                                "start": day_start,
                                "end": real_first_start,
                                "desc": ""
                            })

        except Exception as e:
            print(f"[錯誤] 無法抓取 {ch_id}：{e}")

    programmes.sort(key=lambda x: x['start'])
    return programmes

def fetch_ls_time_programmes():
    url = "https://tvking.funorange.com.tw/channel/108"
    ch_id = "LS-Time"
    ch_name = "LS-Time電影台"
    programmes = []
    try:
        res = requests.get(url)
        res.raise_for_status()
        html = res.text
        match = re.search(r"scheduleList\s*:\s*(\[[\s\S]+?\])\s*,\s*\n", html)
        if not match:
            raise ValueError("未找到 scheduleList")
        raw_json = match.group(1)
        raw_json = re.sub(r'{\s*"program"\s*:\s*"ads"\s*}', '{"program": "[廣告]"}', raw_json)
        schedule_list = json.loads(raw_json)

        for i, day in enumerate(schedule_list):
            date = day["date"]
            prog_list = day.get('programList', [])
            fixed_list = []

            # 檢查是否需要補00:00節目
            if prog_list:
                first_time = prog_list[0].get("timeS", "")
                if first_time != "00:00:00":
                    need_patch = True
                    if i > 0:
                        prev_day = schedule_list[i - 1]
                        prev_list = prev_day.get('programList', [])
                        if prev_list:
                            last_prog = prev_list[-1]
                            try:
                                prev_start = datetime.strptime(f"{prev_day['date']} {last_prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                                prev_end = datetime.strptime(f"{prev_day['date']} {last_prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                                if prev_end <= prev_start:
                                    prev_end += timedelta(days=1)
                                today_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                                if prev_end > today_start:
                                    need_patch = False
                            except:
                                pass
                    if need_patch:
                        fixed_list.append({
                            "program": "無節目資料",
                            "timeS": "00:00:00",
                            "timeE": first_time
                        })

            fixed_list.extend(prog_list)

            for prog in fixed_list:
                if 'timeS' not in prog or 'timeE' not in prog:
                    continue
                try:
                    start_dt = datetime.strptime(f"{date} {prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                    end_dt = datetime.strptime(f"{date} {prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                except Exception as time_err:
                    print(f"[時間錯誤] {prog.get('program')} 日期解析失敗: {time_err}")
                    continue

                # 如果跨天，先生成第一段到 00:00，再補第二天副本
                if end_dt.date() > start_dt.date():
                    midnight = datetime.combine(end_dt.date(), datetime.min.time())  # 次日 00:00:00
                    # 第一天节目（结尾为 00:00:00）
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": start_dt,
                        "end": midnight,
                        "desc": ""
                    })
                    # 第二天补上副本
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": midnight,
                        "end": end_dt,
                        "desc": ""
                    })
                else:
                    # 非跨天，正常添加
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": start_dt,
                        "end": end_dt,
                        "desc": ""
                    })

        # 確保順序正確
        programmes.sort(key=lambda x: x["start"])

        return {
            "id": ch_id,
            "name": ch_name,
            "programmes": programmes
        }

    except Exception as e:
        print(f"[錯誤] 抓取 LS-Time 失敗：{e}")
        return None
def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S") + " +0800"

def write_xml(root_element, filepath):
    tree = ElementTree(root_element)
    with open(filepath, 'wb') as f:
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
                    "start": fmt(start_dt),
                    "stop": fmt(stop_dt),
                    "title": title,
                    "desc": desc
                })
        except Exception as e:
            print(f"[錯誤] {name} 失敗：{e}")

    ltv_programmes = fetch_ltv_programmes()
    json_programmes = fetch_json_schedule()
    ls_time = fetch_ls_time_programmes()

    tv_epg = Element("tv")

    # API频道
    epg_by_channel = {}
    for p in epg_programmes:
        epg_by_channel.setdefault(p['channel'], []).append(p)

    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if real_id:
            ch_el = SubElement(tv_epg, "channel", id=real_id)
            SubElement(ch_el, "display-name").text = name
            for p in epg_by_channel.get(real_id, []):
                prog_el = SubElement(tv_epg, "programme", start=p['start'], stop=p['stop'], channel=p['channel'])
                SubElement(prog_el, "title").text = p['title']
                SubElement(prog_el, "desc").text = p['desc']

    # LTV
    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_epg, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        for start, stop, title, desc in ltv_programmes.get(cid, []):
            p = SubElement(tv_epg, "programme", start=start, stop=stop, channel=cid)
            SubElement(p, "title").text = title
            SubElement(p, "desc").text = desc

    # JSON
    json_by_channel = {}
    for p in json_programmes:
        json_by_channel.setdefault(p['channel'], []).append(p)

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_epg, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
        for p in sorted(json_by_channel.get(ch_id, []), key=lambda x: x['start']):
            prog_el = SubElement(tv_epg, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ch_id)
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = p['desc']

    # LS-Time
    if ls_time:
        ch_el = SubElement(tv_epg, "channel", id=ls_time['id'])
        SubElement(ch_el, "display-name").text = ls_time['name']
        for p in ls_time['programmes']:
            prog_el = SubElement(tv_epg, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ls_time['id'])
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = p['desc']

    write_xml(tv_epg, "epg.xml")

    # boss.xml（只有 LTV、JSON、LS-Time）
    tv_boss = Element("tv")

    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_boss, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        for start, stop, title, _ in ltv_programmes.get(cid, []):
            p = SubElement(tv_boss, "programme", start=start, stop=stop, channel=cid)
            SubElement(p, "title").text = title
            SubElement(p, "desc").text = ""  # 留空

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_boss, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
        for p in sorted(json_by_channel.get(ch_id, []), key=lambda x: x['start']):
            prog_el = SubElement(tv_boss, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ch_id)
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = ""

    if ls_time:
        ch_el = SubElement(tv_boss, "channel", id=ls_time['id'])
        SubElement(ch_el, "display-name").text = ls_time['name']
        for p in ls_time['programmes']:
            prog_el = SubElement(tv_boss, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ls_time['id'])
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = ""

    write_xml(tv_boss, "boss.xml")

if __name__ == "__main__":
    main()
