import requests
import re
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

URL = "https://tvking.funorange.com.tw/channel/108"
CHANNEL_ID = "LS-Time"
CHANNEL_NAME = "LS-Time電影台"

def fetch_schedule_list():
    res = requests.get(URL)
    res.raise_for_status()
    html = res.text

    # 提取 scheduleList: [...]
    match = re.search(r"scheduleList\s*:\s*(\[[\s\S]+?\])\s*,\s*\n", html)
    if not match:
        raise ValueError("未找到 scheduleList")

    raw_json = match.group(1)

    # JSON 修复：替换单个 program: "ads" 为字符串（避免结构错乱）
    raw_json = re.sub(r'{\s*"program"\s*:\s*"ads"\s*}', '{"program": "[廣告]"}', raw_json)

    # 解析为 Python 对象
    return json.loads(raw_json)

def generate_epg(schedule_list, channel_id=CHANNEL_ID, channel_name=CHANNEL_NAME):
    tv = ET.Element('tv')
    channel = ET.SubElement(tv, 'channel', id=channel_id)
    ET.SubElement(channel, 'display-name').text = channel_name

    for day in schedule_list:
        date = day["date"]
        for prog in day.get('programList', []):
            if 'timeS' not in prog or 'timeE' not in prog:
                continue

            start_time = f"{date} {prog['timeS']}"
            end_time = f"{date} {prog['timeE']}"

            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            programme = ET.SubElement(tv, 'programme',
                                      start=start_dt.strftime("%Y%m%d%H%M%S") + " +0800",
                                      stop=end_dt.strftime("%Y%m%d%H%M%S") + " +0800",
                                      channel=channel_id)
            ET.SubElement(programme, 'title').text = prog["program"]  # 无 lang 属性
            ET.SubElement(programme, 'desc').text = ""  # 空描述

    tree = ET.ElementTree(tv)
    tree.write("tvking_epg.xml", encoding="utf-8", xml_declaration=True, short_empty_elements=False)

if __name__ == "__main__":
    schedule_list = fetch_schedule_list()
    generate_epg(schedule_list)
    print("✅ EPG 已生成：tvking_epg.xml")
