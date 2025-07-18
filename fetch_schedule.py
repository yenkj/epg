import requests
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

URL = "https://tvking.funorange.com.tw/channel/108"
CHANNEL_ID = "tvking.108"
CHANNEL_NAME = "TVKing 108"
OUTPUT = "schedule.xml"

def fetch_vue_data():
    res = requests.get(URL)
    res.raise_for_status()
    html = res.text

    # 精确提取 scheduleList
    match = re.search(r"scheduleList:\s*(\[\{.*?\}\])\s*[,}]", html, re.DOTALL)
    if not match:
        raise ValueError("未找到 scheduleList")

    schedule_list_raw = match.group(1)
    # 替换 JS 中的属性名，确保 JSON 能解析
    schedule_list_json = re.sub(r'(\w+):', r'"\1":', schedule_list_raw)
    schedule_list_json = schedule_list_json.replace("undefined", "null")

    schedule_list = json.loads(schedule_list_json)

    return {
        "channel": {
            "id": 108,
            "name": "TVKing 108"
        },
        "scheduleList": schedule_list
    }


def generate_xmltv(data):
    root = ET.Element("tv")
    channel = ET.SubElement(root, "channel", id=CHANNEL_ID)
    ET.SubElement(channel, "display-name").text = CHANNEL_NAME

    for day in data["scheduleList"]:
        date = day["date"]
        for prog in day["programList"]:
            title = prog["program"]
            if title.lower() == "ads":
                continue

            try:
                start = datetime.strptime(f"{date} {prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(f"{date} {prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                if end <= start:
                    end += timedelta(days=1)
            except KeyError:
                continue  # 无时间的广告等跳过

            start_str = start.strftime("%Y%m%d%H%M%S +0800")
            end_str = end.strftime("%Y%m%d%H%M%S +0800")

            p = ET.SubElement(root, "programme", start=start_str, stop=end_str, channel=CHANNEL_ID)
            ET.SubElement(p, "title", lang="zh").text = title

    tree = ET.ElementTree(root)
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    vue_data = fetch_vue_data()
    generate_xmltv(vue_data)
    print(f"✅ XMLTV 已生成：{OUTPUT}")
