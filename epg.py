import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bs4 import BeautifulSoup

# === 频道配置 ===
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels_api = [
  "凤凰中文",
  "凤凰资讯",
  "凤凰香港",
  "北京卫视",
  "湖南卫视",
  "江苏卫视",
  "东方卫视",
  "浙江卫视",
  "湖北卫视",
  "天津卫视",
  "山东卫视",
  "辽宁卫视",
  "安徽卫视",
  "黑龙江卫视",
  "贵州卫视",
  "东南卫视",
  "重庆卫视",
  "江西卫视",
  "广东卫视",
  "河北卫视",
  "深圳卫视",
  "吉林卫视",
  "河南卫视",
  "四川卫视",
  "广西卫视",
  "陕西卫视",
  "山西卫视",
  "内蒙古卫视",
  "青海卫视",
  "海南卫视",
  "宁夏卫视",
  "西藏卫视",
  "新疆卫视",
  "甘肃卫视",
  "云南卫视",
  "海峡卫视",
  "CCTV1",
  "CCTV2",
  "CCTV3",
  "CCTV4",
  "CCTV5",
  "CCTV5+",
  "CCTV6",
  "CCTV7",
  "CCTV8",
  "CCTV9",
  "CCTV10",
  "CCTV11",
  "CCTV12",
  "CCTV13",
  "CCTV14",
  "CCTV15",
  "CCTV16",
  "CCTV17",
  "CGTN",
  "CGTN纪录",
  "民視",
  "民視第一台",
  "民視新聞台",
  "民視台灣台",
  "民視影劇台",
  "民視旅遊台",
  "民視綜藝台",
  "中視",
  "中視新聞台",
  "中視經典台",
  "中視菁采台",
  "中天新聞台",
  "中天娛樂台",
  "中天綜合台",
  "中天亞洲台",
  "華視",
  "華視新聞",
  "靖天綜合台",
  "靖天國際台",
  "靖天戲劇台",
  "靖天日本台",
  "靖天映畫台",
  "靖天卡通台",
  "靖天育樂台",
  "靖天資訊台",
  "靖天電影台",
  "靖天歡樂台",
  "龍華洋片台",
  "龍華偶像台",
  "龍華戲劇台",
  "龍華經典台",
  "龍華電影台",
  "靖洋戲劇台",
  "靖洋卡通Nice-Bingo",
  "寰宇新聞台",
  "寰宇新聞台灣台",
  "寰宇財經台",
  "TVBS",
  "TVBS新聞台",
  "TVBS綜藝台",
  "TVBS歡樂台",
  "TVBS精采台",
  "TVBS台劇台",
  "八大第一台",
  "八大綜合台",
  "八大戲劇台",
  "八大精彩台",
  "八大綜藝台",
  "三立台灣台",
  "三立戲劇台",
  "三立綜合台",
  "三立財經新聞台",
  "台視",
  "台視新聞台",
  "台視綜合台",
  "台視財經台",
  "博斯運動一台",
  "博斯運動二台",
  "博斯無限台",
  "博斯無限二台",
  "博斯網球台",
  "博斯高球台",
  "博斯高球二台",
  "博斯魅力台",
  "愛爾達體育3台",
  "愛爾達體育4台",
  "愛爾達影劇台",
  "愛爾達娛樂台",
  "愛爾達生活旅遊台",
  "東森綜合",
  "東森洋片",
  "東森戲劇",
  "東森幼幼",
  "東森新聞",
  "東森財經新聞",
  "緯來日本台",
  "緯來電影台",
  "緯來體育台",
  "緯來綜合台",
  "智林體育台",
  "TraceSports",
  "CatchPlay電影台",
  "影迷數位電影台",
  "LS-Time電影台",
  "經典電影台",
  "HBO_TW",
  "好萊塢電影台",
  "CINEMAX_TW",
  "AXN_TW",
  "AMC電影台",
  "My-Cinema-Europe-HD我的歐洲電影",
  "CinemaWorld",
  "Rock-Action",
  "Rock-Entertainment",
  "HITS頻道",
  "Lifetime娛樂頻道",
  "MTV-90's",
  "MTV綜合台",
  "MTV-Live-HD音樂頻道",
  "Trace-Urban",
  "Fun探索娛樂台",
  "Mezzo-Live",
  "Classica古典樂",
  "電影原聲台CMusic",
  "豬哥亮歌廳秀",
  "韓國娛樂台",
  "時尚運動X",
  "LUXE-TV",
  "INULTRA_TW",
  "BBC-Lifestyle",
  "TV5MONDE-Style",
  "Pet-Club-TV",
  "幸福空間居家台",
  "車迷TV",
  "DMAX",
  "亞洲旅遊台",
  "TLC旅遊生活頻道",
  "亞洲美食",
  "美食星球",
  "EYE-TV旅遊台",
  "Global-Trekker",
  "動物星球",
  "Discovery_Asia",
  "BBC-Earth",
  "Magellan-TV",
  "影迷數位紀實台",
  "Love-Nature",
  "Smart知識台",
  "History歷史頻道",
  "CI罪案偵查頻道",
  "滾動力Rollor",
  "視納華仁紀實頻道",
  "原住民族電視台",
  "客家電視台",
  "國會頻道1",
  "國會頻道2",
  "華藝中文台",
  "EYE-TV戲劇台",
  "公視戲劇台",
  "采昌影劇台",
  "台灣戲劇台",
  "戲劇免費看1台",
  "GINX-Esports-TV",
  "DreamWorks夢工廠動畫",
  "卡通頻道",
  "尼克兒童頻道",
  "Nick-Jr.兒童頻道",
  "精選動漫台",
  "經典卡通台",
  "達文西頻道",
  "MOMO親子台",
  "LiveABC互動英語台",
  "ELTV生活英語台",
  "金光布袋戲",
  "霹靂布袋戲",
  "非凡新聞台",
  "非凡商業台",
  "年代新聞台",
  "鏡電視新聞台",
  "SBN全球財經台",
  "半島國際新聞台",
  "第1商業台",
  "CNBC-Asia財經台",
  "Bloomberg-TV",
  "France24",
  "VOA美國之音",
  "DW德國之聲",
  "Arirang-TV",
  "東森購物一台",
  "東森購物二台",
  "東森購物三台",
  "東森購物四台",
  "人間衛視",
  "好消息",
  "好消息2台",
  "大愛電視",
  "大愛電視2",
  "翡翠台4K",
  "翡翠台",
  "华丽翡翠台",
  "TVB星河",
  "明珠台",
  "TVB-Plus",
  "無綫新聞台",
  "娛樂新聞台",
  "ViuTV",
  "ViuTVsix",
  "港台电视31",
  "港台电视32",
  "千禧經典台",
  "天映頻道",
  "天映經典頻道",
  "鳳凰衛視中文台",
  "鳳凰衛視資訊台",
  "鳳凰衛視香港台",
  "八度空间",
  "Astro-AOD",
  "Astro-AEC",
  "Astro全佳台",
  "Astro欢喜台",
  "A&E_East",
  "ACC-Network",
  "AMC_East",
  "American-Heroes-Channel",
  "Animal-Planet_East",
  "BBC-America_East",
  "BBC-World-News_North",
  "BET_East",
  "BET-Her",
  "Bloomberg-TV",
  "Boomerang",
  "Bravo_East",
  "Cartoon-Network_East",
  "CBS-Sports-Network",
  "Cinemax_East",
  "CMT_East",
  "CNBC",
  "CNN",
  "Comedy-Central_East",
  "Cooking-Channel",
  "Crime&Investigation",
  "CSPAN",
  "CSPAN-2",
  "Destination-America",
  "Discovery-Channel_East",
  "Discovery-Family-Channel",
  "Discovery-Life",
  "Disney_East",
  "Disney-Junior_East",
  "Disney-XD_East",
  "E!_East",
  "ESPN",
  "ESPN-2",
  "ESPN-News",
  "ESPN-U",
  "Food-Network_East",
  "Fox-Business-Network",
  "Fox-News-Channel",
  "Fox-Sports-1",
  "Fox-Sports-2",
  "Freeform_East",
  "Fuse_East",
  "FX_Networks_East",
  "FX-Movie",
  "FXX_East",
  "FYI_East",
  "Golf-Channel",
  "Hallmark_East",
  "Hallmark-Drama",
  "Hallmark-Mysteries_East",
  "HBO_East",
  "HBO-2_East",
  "HBO-Comedy_East",
  "HBO-Family_East",
  "HBO-Signature_East",
  "HBO-Zone_East",
  "HGTV_East",
  "History_East",
  "HLN",
  "IFC",
  "Investigation-Discovery",
  "ION_East",
  "Lifetime_East",
  "Lifetime-Movies_East",
  "Logo",
  "MLB-Network",
  "MoreMAX_East",
  "Motor-Trend",
  "MovieMAX_East",
  "MSNBC",
  "MTV_East",
  "National-Geographic_East",
  "National-Geographic-Wild",
  "NBA-TV",
  "NFL-Network",
  "NHL-Network",
  "Nick-Jr._East",
  "Nickelodeon_East",
  "Nicktoons_East",
  "Outdoor-Channel",
  "OWN_East",
  "Oxygen_East",
  "PBS-NY",
  "ReelzChannel",
  "Science",
  "Showtime-Extreme_East",
  "Showtime-2_East",
  "STARZ_East",
  "Sundance-TV_East",
  "SYFY_East",
  "TBS_East",
  "TCM",
  "TeenNick_East",
  "Telemundo_East",
  "Tennis-Channel",
  "WPIX-New-York",
  "The-Movie-Channel_East",
  "The-Weather-Channel",
  "TLC_East",
  "TNT_East",
  "Travel-Channel_East",
  "truTV_East",
  "TV-One",
  "Universal-Kids",
  "Univision_East",
  "USA-Network_East",
  "VH1_East",
  "VICE",
  "ABC-NY",
  "CBS-NY",
  "WE-TV_East",
  "NBC-NY",
  "FOX-NY",
  "CCTV4K",
  "CCTV16",
  "北京IPTV-4K",
  "北京纪实科教8K",
  "Love-Nature-4K",
  "Loupe-4K",
  "Fashion-One",
  "咪咕4K-1",
  "咪咕4K-2",
  "EZ-FM",
  "KEXP",
  "NTS-Radio-1",
  "NTS-Radio-2",
  "HIT-FM",
  "摩登音乐台",
  "宁波音乐广播",
  "深圳飞扬971",
  "中廣音樂網",
  "浙江交通之声",
  "BBC-Radio-1",
  "BBC-Radio-1-Dance",
  "BBC-Radio-2",
  "BBC-Radio-3",
  "BBC-Radio-4",
  "BBC-Radio-4-Extra",
  "BBC-Radio-5",
  "BBC-Radio-6",
  "RNE-Radio-3",
  "KISS-FM",
  "法国国际广播电台",
  "美国之音",
  "自由亚洲电台",
  "BBC-World-Service",
  "npr|News&Culture"
]

channels_ltv = {
    "ott-animation": "龍華卡通台",
    "ott-motion": "龍華日韓台"
}

channels_json = {
    "meya-movie-hd": {
        "name": "美亞電影HD",
        "url": "https://xn--i0yt6h0rn.tw/channel/美亞電影HD/index.json"
    },
    "elta-sports-2": {
        "name": "愛爾達體育2台",
        "url": "https://節目表.tw/channel/愛爾達體育2台/index.json"
    }
}

now = datetime.utcnow() + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
date_str_html = now.strftime('%Y-%m-%d')


def fetch_epg(channel_id, date_str):
    url = f"https://epg.pw/api/epg.xml?lang=zh-hans&timezone=QXNpYS9TaGFuZ2hhaQ==&date={date_str}&channel_id={channel_id}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text


def parse_epg(xml, date_prefix, mode='today'):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(xml)
    programmes = []
    for prog in root.findall('programme'):
        start = prog.attrib.get('start', '')
        stop = prog.attrib.get('stop', '')
        if mode == 'today' and not start.startswith(date_prefix):
            continue
        if mode == 'carry' and not stop.startswith(date_prefix):
            continue
        title = prog.findtext('title') or ''
        desc = prog.findtext('desc') or ''
        programmes.append((start, stop, title, desc))
    return programmes


def parse_time_range(date_str_slash, time_range_str):
    try:
        start_str, end_str = [t.strip() for t in time_range_str.split('-')]
        date_prefix = date_str_slash.replace('/', '-')
        start_dt = datetime.strptime(f"{date_prefix} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_prefix} {end_str}", "%Y-%m-%d %H:%M")
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        start_epg = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        end_epg = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"
        return start_epg, end_epg
    except Exception:
        return None, None


def fetch_ltv_programmes():
    url = "https://www.ltv.com.tw/ott%e7%af%80%e7%9b%ae%e8%a1%a8/"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    all_programmes = {}
    for cid in channels_ltv:
        all_programmes[cid] = []
        div = soup.find("div", id=cid)
        if not div:
            continue
        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            time_tag = item.select_one(".timetable-time")
            desc_tag = item.select_one(".timetable-desc")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            if not title_tag or not time_tag or not popup_href:
                continue
            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True) if desc_tag else ""
            popup_id = popup_href.lstrip("#")
            popup = soup.find("div", id=popup_id)
            if not popup:
                continue
            time_info_tag = popup.select_one(".timetable-time")
            if not time_info_tag:
                continue
            date_part = time_info_tag.get_text(strip=True).split()[0].strip()
            start_epg, end_epg = parse_time_range(date_part, time_range)
            if start_epg and end_epg:
                all_programmes[cid].append((start_epg, end_epg, title, desc))

    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x[0])

    return all_programmes


def fetch_json_schedule():
    programmes = []
    for ch_id, info in channels_json.items():
        try:
            data = requests.get(info['url'], timeout=10).json()
            for day in data['list']:
                programme_list = day['values']
                if programme_list and programme_list[0]['time'] != "00:00":
                    programme_list.insert(0, {
                        "name": "無節目資料",
                        "date": day['key'],
                        "time": "00:00"
                    })
                for i, p in enumerate(programme_list):
                    start = datetime.strptime(f"{p['date']} {p['time']}", "%Y-%m-%d %H:%M")
                    if i + 1 < len(programme_list):
                        next_p = programme_list[i + 1]
                        end = datetime.strptime(f"{next_p['date']} {next_p['time']}", "%Y-%m-%d %H:%M")
                    else:
                        end = start + timedelta(hours=2)
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
            print(f"[錯誤] 無法抓取 {ch_id}：{e}")
    return programmes


def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S") + " +0800"


def write_xml(root_element, filepath):
    tree = ElementTree(root_element)
    with open(filepath, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True, short_empty_elements=False)


def main():
    epg_programmes = []
    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if not real_id:
            continue
        try:
            xml_today = fetch_epg(real_id, date_str_api)
            xml_yesterday = fetch_epg(real_id, yesterday_str_api)
            today_programmes = parse_epg(xml_today, date_str_api, mode='today')
            carryover_programmes = parse_epg(xml_yesterday, date_str_api, mode='carry')
            if today_programmes:
                first_start = today_programmes[0][0]
                if not first_start.endswith("0000"):
                    if carryover_programmes:
                        last_prog = carryover_programmes[-1]
                        carry_start = date_str_api + "000000"
                        carry_end = first_start
                        title, desc = last_prog[2], last_prog[3]
                        today_programmes.insert(0, (carry_start, carry_end, title, desc))
            for start, stop, title, desc in today_programmes:
                epg_programmes.append({
                    "channel": real_id,
                    "start": start,
                    "stop": stop,
                    "title": title,
                    "desc": desc
                })
        except Exception as e:
            print(f"[錯誤] {name} 失敗：{e}")

    ltv_programmes = fetch_ltv_programmes()
    json_programmes = fetch_json_schedule()
    ls_time = fetch_ls_time_programmes()

    # === epg.xml ===
    tv_epg = Element("tv")

    # API 頻道 + 節目
    epg_by_channel = {}
    for p in epg_programmes:
        epg_by_channel.setdefault(p['channel'], []).append(p)

    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if real_id:
            ch_el = SubElement(tv_epg, "channel", id=real_id)
            SubElement(ch_el, "display-name").text = name
            for p in epg_by_channel.get(real_id, []):
                prog_el = SubElement(tv_epg, "programme", start=p['start'], stop=p['stop'], channel=p['channel'])
                SubElement(prog_el, "title").text = p['title']
                SubElement(prog_el, "desc").text = p['desc']

    # LTV 頻道 + 節目
    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_epg, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        for start, stop, title, desc in ltv_programmes.get(cid, []):
            p = SubElement(tv_epg, "programme", start=start, stop=stop, channel=cid)
            SubElement(p, "title").text = title
            SubElement(p, "desc").text = desc

    # JSON 頻道 + 節目
    json_by_channel = {}
    for p in json_programmes:
        json_by_channel.setdefault(p['channel'], []).append(p)

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_epg, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
        for p in sorted(json_by_channel.get(ch_id, []), key=lambda x: x['start']):
            prog_el = SubElement(tv_epg, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ch_id)
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = p['desc']

    # LS-Time 加入 epg.xml
    if ls_time:
        ch_el = SubElement(tv_epg, "channel", id=ls_time["id"])
        SubElement(ch_el, "display-name").text = ls_time["name"]
        for p in sorted(ls_time["programmes"], key=lambda x: x['start']):
            prog_el = SubElement(tv_epg, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ls_time["id"])
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = p['desc']

    write_xml(tv_epg, "epg.xml")

    # === boss.xml（無描述） ===
    tv_boss = Element("tv")

    for cid, cname in channels_ltv.items():
        ch_el = SubElement(tv_boss, "channel", id=cid)
        SubElement(ch_el, "display-name").text = cname
        for start, stop, title, _ in ltv_programmes.get(cid, []):
            p = SubElement(tv_boss, "programme", start=start, stop=stop, channel=cid)
            SubElement(p, "title").text = title
            SubElement(p, "desc").text = ""

    for ch_id, info in channels_json.items():
        ch_el = SubElement(tv_boss, "channel", id=ch_id)
        SubElement(ch_el, "display-name").text = info['name']
        for p in sorted(json_by_channel.get(ch_id, []), key=lambda x: x['start']):
            prog_el = SubElement(tv_boss, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ch_id)
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = ""

    if ls_time:
        ch_el = SubElement(tv_boss, "channel", id=ls_time["id"])
        SubElement(ch_el, "display-name").text = ls_time["name"]
        for p in sorted(ls_time["programmes"], key=lambda x: x['start']):
            prog_el = SubElement(tv_boss, "programme",
                                 start=fmt(p['start']),
                                 stop=fmt(p['end']),
                                 channel=ls_time["id"])
            SubElement(prog_el, "title").text = p['title']
            SubElement(prog_el, "desc").text = ""

    write_xml(tv_boss, "boss.xml")


if __name__ == "__main__":
    main()
