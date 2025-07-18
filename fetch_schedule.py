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

    # 匹配 createApp 中的 data()
    match = re.search(r"createApp\(\s*{\s*data\(\)\s*{\s*return\s*({.*?})\s*}\s*}\s*\)", res.text, re.DOTALL)
    if not match:
        raise ValueError("未找到 Vue 数据")

    js_obj = match.group(1)
    js_obj = re.sub(r'(\w+):', r'"\1":', js_obj)  # key 加引号
    js_obj = js_obj.replace("undefined", "null")

    data = json.loads(js_obj)
    return data


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
