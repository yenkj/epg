import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

def fetch_celestial_generic(name, url, ch_id):
    programmes = []
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        items = soup.select("div.schedule-item")
        now_date = datetime.now() + timedelta(hours=8)
        today_str = now_date.strftime("%Y-%m-%d")

        for i, item in enumerate(items):
            time_str = item.select_one(".schedule-time").get_text(strip=True)
            title_tag = item.select_one(".programme-title")
            desc_tag = item.select_one(".schedule-description")

            title = title_tag.get_text(strip=True) if title_tag else "無標題"
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            try:
                start = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %I:%M%p")
            except:
                continue

            if i + 1 < len(items):
                next_time_str = items[i + 1].select_one(".schedule-time").get_text(strip=True)
                try:
                    end = datetime.strptime(f"{today_str} {next_time_str}", "%Y-%m-%d %I:%M%p")
                    if end <= start:
                        end += timedelta(days=1)
                except:
                    end = start + timedelta(hours=2)
            else:
                end = start + timedelta(hours=2)

            # 跨天拆分
            if end.date() > start.date():
                midnight = datetime.combine(end.date(), datetime.min.time())
                programmes.append({
                    "channel": ch_id,
                    "start": start,
                    "end": midnight,
                    "title": title,
                    "desc": desc,
                    "name": name
                })
                programmes.append({
                    "channel": ch_id,
                    "start": midnight,
                    "end": end,
                    "title": title,
                    "desc": desc,
                    "name": name
                })
            else:
                programmes.append({
                    "channel": ch_id,
                    "start": start,
                    "end": end,
                    "title": title,
                    "desc": desc,
                    "name": name
                })

        # 若第一个节目不是00:00补無節目資料
        if programmes:
            programmes.sort(key=lambda x: x["start"])
            first_start = programmes[0]["start"]
            day_start = datetime.combine(first_start.date(), datetime.min.time())
            if first_start > day_start:
                programmes.insert(0, {
                    "channel": ch_id,
                    "start": day_start,
                    "end": first_start,
                    "title": "無節目資料",
                    "desc": "",
                    "name": name
                })

        return programmes

    except Exception as e:
        print(f"[錯誤] 抓取 {name} 失敗：{e}")
        return []

def write_xmltv(programmes, channels, output_path):
    tv = ET.Element("tv", attrib={"generator-info-name": "celestial-fetcher"})

    for ch in channels:
        ch_elem = ET.SubElement(tv, "channel", id=ch["id"])
        name_elem = ET.SubElement(ch_elem, "display-name")
        name_elem.text = ch["name"]

    for prog in sorted(programmes, key=lambda x: x["start"]):
        p_elem = ET.SubElement(tv, "programme", attrib={
            "start": prog["start"].strftime("%Y%m%d%H%M%S +0800"),
            "stop": prog["end"].strftime("%Y%m%d%H%M%S +0800"),
            "channel": prog["channel"]
        })
        title_elem = ET.SubElement(p_elem, "title", lang="zh")
        title_elem.text = prog["title"]
        if prog["desc"]:
            desc_elem = ET.SubElement(p_elem, "desc", lang="zh")
            desc_elem.text = prog["desc"]

    tree = ET.ElementTree(tv)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    channels = [
        {
            "name": "天映頻道",
            "url": "https://www.celestialmovies.com/schedule.php?lang=tc",
            "id": "celestial-movies-hd"
        },
        {
            "name": "天映經典台",
            "url": "https://www.cmclassic.tv/schedule.php?lang=tc",
            "id": "celestial-classic-hd"
        }
    ]

    all_programmes = []
    for ch in channels:
        all_programmes.extend(fetch_celestial_generic(ch["name"], ch["url"], ch["id"]))

    write_xmltv(all_programmes, channels, "celestial.xml")
