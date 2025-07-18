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
    resp = requests.get(URL)
    resp.raise_for_status()

    # 匹配 window.createApp({...}) 中的内容
    match = re.search(r"createApp\(\s*{\s*data\(\)\s*{\s*return\s*({.*?})\s*}\s*}\s*\)", resp.text, re.DOTALL)
    if not match:
        raise ValueError("未找到 Vue 数据块")

    js_obj_str = match.group(1)

    # 修复 JSON 格式：将 JavaScript 的单引号、None、True/False 替换为 JSON 格式
    js_obj_str = js_obj_str.replace("undefined", "null")
    js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)  # 对 key 加引号
    js_obj_str = re.sub(r'\'', '"', js_obj_str)

    # 转为 Python 字典
    vue_data = json.loads(js_obj_str)
    return vue_data


def generate_xmltv(data):
    root = ET.Element("tv")

    # 添加频道信息
    channel = ET.SubElement(root, "channel", id=CHANNEL_ID)
    ET.SubElement(channel, "display-name").text = CHANNEL_NAME

    for day in data["scheduleList"]:
        date = day["date"]
        for program in day["programList"]:
            title = program["program"]
            if title.lower() == "ads":
                continue  # 跳过广告

            start_time = f"{date} {program['timeS']}"
            end_time = f"{date} {program['timeE']}"

            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

            # 处理跨天（end < start）
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            start_str = start_dt.strftime("%Y%m%d%H%M%S +0800")
            end_str = end_dt.strftime("%Y%m%d%H%M%S +0800")

            prog = ET.SubElement(root, "programme", start=start_str, stop=end_str, channel=CHANNEL_ID)
            ET.SubElement(prog, "title", lang="zh").text = title

    # 写入文件
    tree = ET.ElementTree(root)
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    data = fetch_vue_data()
    generate_xmltv(data)
    print(f"✅ 已生成：{OUTPUT}")
