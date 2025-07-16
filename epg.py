import requests
from datetime import datetime

channels = [
    "湖南卫视",
    "东方卫视",
    "CCTV1",
    "CCTV5"
]

base_url = "https://epg.199301.dpdns.org"
today = datetime.utcnow().strftime("%Y-%m-%d")
date_tag = datetime.utcnow().strftime("%Y%m%d")

epg = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']

for ch_name in channels:
    epg.append(f'<channel id="{ch_name}"><display-name>{ch_name}</display-name></channel>')

    url = f"{base_url}/?ch={ch_name}&date={today}"
    print(f"Fetching {ch_name} ...")

    try:
        res = requests.get(url)
        data = res.json()

        for item in data.get("epg_data", []):
            start = f"{date_tag}{item['start'].replace(':', '')} +0000"
            end = f"{date_tag}{item['end'].replace(':', '')} +0000"
            title = item['title'].replace("&", "&amp;").strip()
            desc = item.get('desc', '').replace("&", "&amp;").strip()

            epg.append(f'''
<programme start="{start}" stop="{end}" channel="{ch_name}">
  <title>{title}</title>
  <desc>{desc}</desc>
</programme>''')

    except Exception as e:
        print(f"Failed for {ch_name}: {e}")

epg.append('</tv>')

with open("epg.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(epg))

print("EPG XML generated as epg.xml")
