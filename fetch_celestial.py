import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from html import escape
import re

def fetch_channel(channel_id, channel_name, url):
    print(f"Fetching: {url} → {channel_id}")
    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # 找到包含 scheduleList 的 <script>
        script_tag = soup.find("script", string=re.compile("scheduleList"))
        if not script_tag:
            for script in soup.find_all("script"):
                if "scheduleList" in script.get_text():
                    script_tag = script
                    break
        if not script_tag:
            print(f"❌ Failed to find script for {channel_id}")
            return None

        script_text = script_tag.get_text()
        match = re.search(r"scheduleList\s*=\s*(\[\{.*?\}\]);", script_text, re.S)
        if not match:
            print(f"❌ Failed to extract JSON for {channel_id}")
            return None

        raw_list = eval(match.group(1))  # 假设为安全结构，可用 ast.literal_eval 更安全
        programmes = []

        # 转换节目列表为 XMLTV 结构
        for idx, item in enumerate(raw_list):
            title = item.get("program", "無標題")
            date = item.get("date")
            start = item.get("timeS")
            end = item.get("timeE")
            desc = item.get("description", "")

            start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end}", "%Y-%m-%d %H:%M")
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            programmes.append({
                "start": start_dt,
                "end": end_dt,
                "title": title.strip(),
                "desc": desc.strip() if desc else "",
            })

        # 插入 00:00 的“無節目資料”节目前缀（如果首节目不是 00:00）
        if programmes and programmes[0]["start"].time() != datetime.strptime("00:00", "%H:%M").time():
            first_start = programmes[0]["start"]
            dummy = {
                "start": first_start.replace(hour=0, minute=0),
                "end": first_start,
                "title": "無節目資料",
                "desc": "",
            }
            programmes.insert(0, dummy)

        return {
            "id": channel_id,
            "name": channel_name,
            "programmes": programmes
        }

    except Exception as e:
        print(f"Error fetching {channel_id}: {e}")
        return None


def write_xml(channels, output_path):
    xml = ['<?xml version="1.0" encoding="utf-8"?>', '<tv generator-info-name="celestial-fetcher">']
    
    # 频道定义
    for ch in channels:
        xml.append(f'<channel id="{ch["id"]}"><display-name>{escape(ch["name"])}</display-name></channel>')

    # 每个频道单独按时间排序输出 <programme>
    for ch in channels:
        ch_id = ch["id"]
        for prog in sorted(ch["programmes"], key=lambda p: p["start"]):
            start_str = prog["start"].strftime("%Y%m%d%H%M%S +0800")
            end_str = prog["end"].strftime("%Y%m%d%H%M%S +0800")
            title = escape(prog["title"])
            desc = escape(prog["desc"])
            xml.append(f'<programme start="{start_str}" stop="{end_str}" channel="{ch_id}">')
            xml.append(f'<title lang="zh">{title}</title>')
            if desc:
                xml.append(f'<desc lang="zh">{desc}</desc>')
            xml.append('</programme>')

    xml.append("</tv>")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml))


if __name__ == "__main__":
    raw_channels = [
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

    # 过滤掉无数据的频道
    all_channels = [ch for ch in raw_channels if isinstance(ch, dict) and ch.get("programmes")]
    write_xml(all_channels, "celestial.xml")
