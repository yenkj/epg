import requests
import xml.etree.ElementTree as ET
from datetime import datetime

URL = "https://tvking.funorange.com.tw/channel/108"  # 把这里改成你的数据接口地址

def fetch_schedule():
    resp = requests.get(URL)
    resp.raise_for_status()
    data = resp.json()
    return data

def build_xml(data):
    tv = ET.Element("tv")

    # 加频道信息
    channel = data.get("channel", {})
    chan_el = ET.SubElement(tv, "channel", id=str(channel.get("id", "unknown")))
    ET.SubElement(chan_el, "display-name").text = channel.get("name", "Unknown Channel")

    # 加节目表
    for day in data.get("scheduleList", []):
        date_str = day.get("date", "")
        for prog in day.get("programList", []):
            if prog.get("program") == "ads":  # 跳过广告
                continue

            prog_el = ET.SubElement(tv, "programme")
            prog_el.set("start", f"{date_str.replace('-', '')}{prog.get('timeS', '').replace(':', '')}00 +0800")
            prog_el.set("stop",  f"{date_str.replace('-', '')}{prog.get('timeE', '').replace(':', '')}00 +0800")
            prog_el.set("channel", str(channel.get("id", "unknown")))

            title_el = ET.SubElement(prog_el, "title")
            title_el.text = prog.get("program", "Unknown Program")

    return ET.ElementTree(tv)

def main():
    data = fetch_schedule()
    tree = build_xml(data)
    tree.write("schedule.xml", encoding="utf-8", xml_declaration=True)
    print("节目单生成完毕: schedule.xml")

if __name__ == "__main__":
    main()
