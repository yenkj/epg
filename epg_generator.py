# epg_generator.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

def parse_tvking_programmes(channel_id="108"):
    url = f"https://tvking.funorange.com.tw/channel/{channel_id}"
    res = requests.get(url)
    res.raise_for_status()

    # ⬇️ 加上这段来保存网页内容到 debug.html
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(res.text)

    soup = BeautifulSoup(res.text, "html.parser")

    programmes = {}
    date_tabs = soup.select("a[data-slick-index]")
    date_map = {}
    for tab in date_tabs:
        index = tab.get("data-slick-index")
        date_text = tab.get_text(separator=" ").strip().split()[-1]  # e.g. 07.18
        try:
            date_obj = datetime.strptime(f"2025.{date_text}", "%Y.%m.%d")
        except ValueError:
            continue
        date_map[index] = date_obj.strftime("%Y-%m-%d")

    slides = soup.select(".slick-slide")
    for slide in slides:
        index = slide.get("data-slick-index")
        if index not in date_map:
            continue
        date_str = date_map[index]
        programme_list = []
        rows = slide.select("div.mt-2")
        for i, row in enumerate(rows):
            time_tag = row.select_one('.col-3 span')
            title_tag = row.select_one('.card-body')
            if not time_tag or not title_tag:
                continue
            start_str = f"{date_str} {time_tag.text.strip()}"
            start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            programme_list.append((start_dt, title_tag.text.strip()))
        programmes[date_str] = programme_list

    return programmes

def generate_epg_xml(programmes, channel_id="tvking.108", channel_name="TVKing 108", tz="+0800"):
    tv = ET.Element("tv")
    channel = ET.SubElement(tv, "channel", id=channel_id)
    ET.SubElement(channel, "display-name").text = channel_name

    for date_str, items in programmes.items():
        for i, (start_dt, title) in enumerate(items):
            end_dt = items[i + 1][0] if i + 1 < len(items) else start_dt + timedelta(hours=2)
            prog_elem = ET.SubElement(tv, "programme", {
                "start": start_dt.strftime("%Y%m%d%H%M%S") + f" {tz}",
                "stop": end_dt.strftime("%Y%m%d%H%M%S") + f" {tz}",
                "channel": channel_id
            })
            ET.SubElement(prog_elem, "title", lang="zh").text = title

    tree = ET.ElementTree(tv)
    tree.write("epg_tvking_108.xml", encoding="utf-8", xml_declaration=True)
    print("✅ EPG saved to epg_tvking_108.xml")

if __name__ == "__main__":
    programmes = parse_tvking_programmes("108")
    generate_epg_xml(programmes)
