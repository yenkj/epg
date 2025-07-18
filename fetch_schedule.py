import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

URL = "https://tvking.funorange.com.tw/channel/108"
CHANNEL_ID = "tvking.108"
CHANNEL_NAME = "TVKing 108"

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

def generate_epg(schedule_list):
    tv = ET.Element("tv")
    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    ET.SubElement(channel, "display-name").text = CHANNEL_NAME

    for day in schedule_list:
        date = day["date"]  # e.g. 2025-07-18
        for prog in day["programList"]:
            title = prog.get("program", "").strip()
            if not title:
                continue

            start_time = f"{date} {prog['timeS']}"
            end_time = f"{date} {prog['timeE']}"

            # 解决跨午夜问题
            dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            if dt_end <= dt_start:
                dt_end += timedelta(days=1)

            start_str = dt_start.strftime("%Y%m%d%H%M%S") + " +0800"
            end_str = dt_end.strftime("%Y%m%d%H%M%S") + " +0800"

            programme = ET.SubElement(tv, "programme", start=start_str, stop=end_str, channel=CHANNEL_ID)
            ET.SubElement(programme, "title", lang="zh").text = title

    tree = ET.ElementTree(tv)
    tree.write("tvking_epg.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    schedule_list = fetch_schedule_list()
    generate_epg(schedule_list)
    print("✅ EPG 已生成：tvking_epg.xml")
