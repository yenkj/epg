import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --------- 配置 ---------
output_path_epg = "epg.xml"
output_path_boss = "boss.xml"
timezone = "+0800"

# JSON 频道列表
channels_json = {
    "meya-movie-hd": {
        "name": "美亞電影HD",
        "url": "https://xn--i0yt6h0rn.tw/channel/美亞電影HD/index.json"
    },
    "elta-sport2": {
        "name": "愛爾達體育2台",
        "url": "https://節目表.tw/channel/愛爾達體育2台/index.json"
    }
}

# LTV 和 epg.pw 的频道示例（请用实际URL替换）
channels_ltv = {
    "longhua": {
        "name": "龍華戲劇台",
        "url": "http://ltv.example.com/epg.xml"
    }
}

channels_epgpw = {
    "cctv1": {
        "name": "CCTV1",
        "url": "http://epgpw.example.com/cctv1.xml"
    }
}

# --------- 时间辅助 ---------
def dt(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S") + f" {timezone}"

# --------- JSON 频道抓取 ---------
def fetch_json_schedule():
    programmes = []
    for ch_id, info in channels_json.items():
        try:
            data = requests.get(info['url'], timeout=10).json()
            for day in data['list']:
                day_str = day['key']
                programme_list = day['values']

                # 0点补齐无节目
                if programme_list and programme_list[0]['time'] != "00:00":
                    filler = {
                        "name": "無節目資料",
                        "date": day_str,
                        "time": "00:00"
                    }
                    programme_list.insert(0, filler)

                for i, p in enumerate(programme_list):
                    start = dt(f"{p['date']} {p['time']}")
                    if i + 1 < len(programme_list):
                        next_p = programme_list[i+1]
                        end = dt(f"{next_p['date']} {next_p['time']}")
                    else:
                        end = start + timedelta(hours=2)  # 默认2小时

                    if end <= start:
                        end += timedelta(days=1)

                    programmes.append({
                        "channel": ch_id,
                        "title": p['name'],
                        "start": start,
                        "end": end,
                        "desc": ""
                    })
        except Exception as e:
            print(f"Failed to fetch {ch_id}: {e}")

    return programmes

# --------- LTV 频道抓取 (示例，请用实际解析代码替换) ---------
def fetch_ltv_schedule():
    programmes = []
    # 这里示范，实际根据 LTV 数据格式解析填充 programmes
    # 示例返回空
    return programmes

# --------- epg.pw 频道抓取 (示例，请用实际解析代码替换) ---------
def fetch_epgpw_schedule():
    programmes = []
    # 这里示范，实际根据 epg.pw 格式解析填充 programmes
    # 示例返回空
    return programmes

# --------- 写入 XML ---------
def write_epg(all_programmes, filename, included_channels=None):
    tv = ET.Element("tv")
    channels_written = set()

    for prog in all_programmes:
        ch_id = prog['channel']
        if included_channels and ch_id not in included_channels:
            continue

        if ch_id not in channels_written:
            ch_el = ET.SubElement(tv, "channel", id=ch_id)
            # 名称优先取 JSON 频道名，其它渠道需手动补充
            name = channels_json.get(ch_id, {}).get('name') or \
                   channels_ltv.get(ch_id, {}).get('name') or \
                   channels_epgpw.get(ch_id, {}).get('name') or ch_id
            ET.SubElement(ch_el, "display-name").text = name
            channels_written.add(ch_id)

        p_el = ET.SubElement(tv, "programme", {
            "start": fmt(prog['start']),
            "stop": fmt(prog['end']),
            "channel": ch_id
        })
        ET.SubElement(p_el, "title").text = prog['title']
        ET.SubElement(p_el, "desc").text = prog['desc']

    tree = ET.ElementTree(tv)
    tree.write(filename, encoding="utf-8", xml_declaration=True)

# --------- 主程序 ---------
def main():
    json_programmes = fetch_json_schedule()
    ltv_programmes = fetch_ltv_schedule()
    epgpw_programmes = fetch_epgpw_schedule()

    all_programmes = json_programmes + ltv_programmes + epgpw_programmes

    # 写 epg.xml 全部频道
    write_epg(all_programmes, output_path_epg)

    # boss.xml 只含 JSON + 龙华频道
    boss_channels = list(channels_json.keys()) + list(channels_ltv.keys())
    write_epg(json_programmes + ltv_programmes, output_path_boss, included_channels=boss_channels)

if __name__ == "__main__":
    main()
