import requests
import re
import xml.etree.ElementTree as ET
import demjson3
from datetime import datetime, timedelta

URL = "https://tvking.funorange.com.tw/channel/108"

def fetch_vue_data():
    res = requests.get(URL)
    res.raise_for_status()
    html = res.text

    match = re.search(r'scheduleList\s*:\s*(\[\s*\{.*?\}\s*\])\s*[,\}]', html, re.DOTALL)
    if not match:
        raise ValueError("未找到 scheduleList")

    schedule_list_raw = match.group(1)

    try:
        schedule_list = demjson3.decode(schedule_list_raw)
    except demjson3.JSONDecodeError as e:
        raise ValueError(f"解析 scheduleList 出错: {e}")

    return {
        "channel": {
            "id": 108,
            "name": "TVKing 108"
        },
        "scheduleList": schedule_list
    }

def generate_epg(vue_data, filename="tvking_epg.xml"):
    tv = ET.Element("tv")
    channel_id = f"tvking.{vue_data['channel']['id']}"

    # 添加频道信息
    channel = ET.SubElement(tv, "channel", id=channel_id)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = vue_data["channel"]["name"]

    for day in vue_data["scheduleList"]:
        date = day["date"]
        for prog in day["programList"]:
            if prog.get("program") == "ads":
                continue  # 跳过广告

            time_start = prog.get("timeS")
            time_end = prog.get("timeE")
            if not time_start or not time_end:
                continue

            start_dt = datetime.strptime(f"{date} {time_start}", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{date} {time_end}", "%Y-%m-%d %H:%M:%S")

            # 若结束时间在第二天
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            start_str = start_dt.strftime("%Y%m%d%H%M%S +0000")
            end_str = end_dt.strftime("%Y%m%d%H%M%S +0000")

            programme = ET.SubElement(tv, "programme", start=start_str, stop=end_str, channel=channel_id)
            title = ET.SubElement(programme, "title", lang="zh")
            title.text = prog["program"]

    tree = ET.ElementTree(tv)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"✅ EPG written to: {filename}")

if __name__ == "__main__":
    vue_data = fetch_vue_data()
    generate_epg(vue_data)
