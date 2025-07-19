import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def fetch_channel(channel_id: str, channel_name: str, url: str):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    script = soup.find("script", string=re.compile("scheduleList"))
    if not script:
        return []

    data = re.search(r"scheduleList\s*=\s*(\[\{.*?\}\]);", script.string, re.S)
    if not data:
        return []

    import json
    schedule = json.loads(data.group(1))

    programmes = []
    for idx, item in enumerate(schedule):
        title = item.get("program", "無節目資料").strip()
        desc = item.get("description", "").strip()
        start_dt = datetime.strptime(f"{item['date']} {item['timeS']}", "%Y-%m-%d %H:%M")
        end_str = item.get("timeE")
        if end_str:
            end_dt = datetime.strptime(f"{item['date']} {end_str}", "%Y-%m-%d %H:%M")
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(hours=2)
        programmes.append((start_dt, end_dt, title, desc))

    # 插入 00:00 無節目資料
    if programmes and programmes[0][0].time() != datetime.strptime("00:00", "%H:%M").time():
        day_start = programmes[0][0].replace(hour=0, minute=0)
        programmes.insert(0, (day_start, programmes[0][0], "無節目資料", ""))

    # 拆分跨天节目
    fixed = []
    for s, e, t, d in programmes:
        if e.date() != s.date():
            midnight = s.replace(hour=0, minute=0) + timedelta(days=1)
            fixed.append((s, midnight, t, d))
            fixed.append((midnight, e, t, d))
        else:
            fixed.append((s, e, t, d))

    return {
        "id": channel_id,
        "name": channel_name,
        "programmes": sorted(fixed, key=lambda x: x[0])
    }

def write_xml(channels: list, filename="celestial.xml"):
    from xml.sax.saxutils import escape

    xml = ['<?xml version="1.0" encoding="utf-8"?>', '<tv generator-info-name="celestial-fetcher">']

    # 输出所有频道信息
    for ch in channels:
        xml.append(f'<channel id="{ch["id"]}"><display-name>{escape(ch["name"])}</display-name></channel>')

    # 输出每个频道的节目
    for ch in channels:
        for s, e, t, d in ch["programmes"]:
            start = s.strftime("%Y%m%d%H%M%S") + " +0800"
            end = e.strftime("%Y%m%d%H%M%S") + " +0800"
            xml.append(f'<programme start="{start}" stop="{end}" channel="{ch["id"]}">')
            xml.append(f'  <title lang="zh">{escape(t)}</title>')
            if d:
                xml.append(f'  <desc lang="zh">{escape(d)}</desc>')
            xml.append(f'</programme>')

    xml.append("</tv>")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

if __name__ == "__main__":
    all_channels = [
        fetch_channel(
            "celestial-movies-hd",
            "天映頻道",
            "https://www.celestialmovies.com/schedule.php?lang=tc"
        ),
        fetch_channel(
            "celestial-classic-hd",
            "天映經典台",
            "https://www.cmclassic.tv/schedule.php?lang=tc"
        )
    ]

    write_xml(all_channels, "celestial.xml")
