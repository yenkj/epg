import os
import json
import re
import requests
from datetime import datetime, timedelta, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bs4 import BeautifulSoup

# Global channel data
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels_api = [
  "凤凰中文",
  "凤凰资讯",
  "凤凰香港",
  "北京卫视",
  "北京卫视4K",
  "湖南卫视",
  "湖南卫视4K",
  "江苏卫视",
  "江苏卫视4K",
  "东方卫视",
  "东方卫视4K",
  "浙江卫视",
  "浙江卫视4K",
  "湖北卫视",
  "天津卫视",
  "山东卫视",
  "山东卫视4K",
  "辽宁卫视",
  "安徽卫视",
  "黑龙江卫视",
  "贵州卫视",
  "东南卫视",
  "重庆卫视",
  "江西卫视",
  "广东卫视",
  "广东卫视4K",
  "河北卫视",
  "深圳卫视",
  "深圳卫视4K",
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
  "愛爾達體育2台",    
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
  "MTV-90s",
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
  "鳳凰衛視中文台",
  "鳳凰衛視資訊台",
  "鳳凰衛視香港台",
  "八度空间",
  "天映經典台",
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

channels_ottltv = {
    "ott-animation": "龍華卡通台",
    "ott-motion": "龍華日韓台",
    "ott-idol": "龍華偶像台"
}

channels_celestial = {
    "celestial-movies-hd": {
        "name": "天映頻道",
        "url": "https://www.celestialmovies.com/schedule.php?location/ID"
    }
}

# --- GLOBAL DATE VARIABLES (MODIFIED FOR 3 DAYS) ---
now = datetime.now(timezone.utc) + timedelta(hours=8)
date_str_api = now.strftime('%Y%m%d')
yesterday_str_api = (now - timedelta(days=1)).strftime('%Y%m%d')
tomorrow_str_api = (now + timedelta(days=1)).strftime('%Y%m%d')
three_day_list = [yesterday_str_api, date_str_api, tomorrow_str_api]
date_str_html = now.strftime('%Y-%m-%d')

# --- HELPER FUNCTIONS ---

def fetch_epg(channel_id, date_str=None):
    """Fetches EPG XML data from the external API."""
    url = f"https://epg.pw/api/epg.xml?channel_id={channel_id}"
    if date_str:
        url += f"&date={date_str}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

# --- MODIFIED API FETCH FUNCTION ---

def fetch_api_programmes(channels_api, channel_map, date_list):
    """
    Fetches EPG data for the specified channels across a list of dates.
    The original complex carry-over logic is removed and replaced by a simple 
    multi-day fetch and deduplication, relying on the API providing complete data 
    for the requested dates.
    """
    from datetime import datetime, timedelta, timezone
    from xml.etree import ElementTree as ET

    # Simplified parse_epg: removes mode/date_prefix filtering
    def parse_epg(xml, channel_id=None):
        root = ET.fromstring(xml)
        programmes = []
        for prog in root.findall('programme'):
            start_raw = prog.attrib.get('start', '')
            stop_raw = prog.attrib.get('stop', '')
            if not start_raw or not stop_raw:
                continue
            try:
                # Use timezone aware parsing
                start_dt = datetime.strptime(start_raw, "%Y%m%d%H%M%S %z").astimezone(timezone(timedelta(hours=8)))
                stop_dt = datetime.strptime(stop_raw, "%Y%m%d%H%M%S %z").astimezone(timezone(timedelta(hours=8)))
            except Exception:
                continue

            if channel_id == '368371':
                # Hardcoded time zone adjustment (retained from original)
                start_dt += timedelta(hours=1)
                stop_dt += timedelta(hours=1)

            title = prog.findtext('title') or ''
            desc = prog.findtext('desc') or ''
            programmes.append((start_dt, stop_dt, title, desc))
        return programmes

    epg_programmes = []

    for name in channels_api:
        real_id = next((cid for cid, names in channel_map.items()
                        if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)), None)
        if not real_id:
            continue
        
        channel_programs = []
        try:
            # Fetch data for all three days
            for date_str in date_list:
                xml_data = fetch_epg(real_id, date_str)
                channel_programs.extend(parse_epg(xml_data, channel_id=real_id))

            # Deduplication for the channel: (channel_id, start_time, title) is the key
            unique_programmes = {}
            for start_dt, stop_dt, title, desc in channel_programs:
                 # Key: Channel ID, Start Time (to the second), Program Title
                 key = (real_id, start_dt, title)
                 if key not in unique_programmes:
                     unique_programmes[key] = {
                        "channel": real_id,
                        "start": start_dt,
                        "end": stop_dt,
                        "title": title,
                        "desc": desc
                    }

            # Add unique programs to the main list
            epg_programmes.extend(list(unique_programmes.values()))

        except Exception as e:
            print(f"[錯誤] {name} 抓取多日API失敗：{e}")

    # Sort by start time before returning
    return sorted(epg_programmes, key=lambda x: x['start'])

# --- UNMODIFIED SCRAPING FUNCTIONS (Retaining single-day behavior where multi-day is not trivial) ---

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

def fetch_ottltv_programmes():
    url = "https://www.ltv.com.tw/ott%e7%af%80%e7%9b%ae%e8%a1%a8/"
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    all_programmes = {}
    for cid in channels_ottltv:
        all_programmes[cid] = []
        div = soup.find("div", id=cid)
        if not div:
            continue
        items = div.select(".timetable-item")
        for item in items:
            title_tag = item.select_one(".timetable-name")
            time_tag = item.select_one(".timetable-time")
            popup_href = item.select_one("a")["href"] if item.select_one("a") else None
            if not title_tag or not time_tag or not popup_href:
                continue
            title = title_tag.get_text(strip=True)
            time_range = time_tag.get_text(strip=True)
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
                all_programmes[cid].append({
                    "channel": cid,
                    "start": start_epg,
                    "end": end_epg,
                    "title": title,
                    "desc": ""
                })
    for cid in all_programmes:
        all_programmes[cid].sort(key=lambda x: x["start"])
    return all_programmes

def fetch_ls_time_programmes():
    url = "https://tvking.funorange.com.tw/channel/108"
    ch_id = "LS-Time"
    ch_name = "LS-Time電影台"
    programmes = []
    try:
        res = requests.get(url)
        res.raise_for_status()
        html = res.text
        match = re.search(r"scheduleList\s*:\s*(\[[\s\S]+?\])\s*,\s*\n", html)
        if not match:
            raise ValueError("未找到 scheduleList")
        raw_json = match.group(1)
        raw_json = re.sub(r'{\s*"program"\s*:\s*"ads"\s*}', '{"program": "[廣告]"}', raw_json)
        schedule_list = json.loads(raw_json)

        for i, day in enumerate(schedule_list):
            date = day["date"]
            prog_list = day.get('programList', [])
            fixed_list = []

            # 檢查是否需要補00:00節目
            if prog_list:
                first_time = prog_list[0].get("timeS", "")
                if first_time != "00:00:00":
                    need_patch = True
                    if i > 0:
                        prev_day = schedule_list[i - 1]
                        prev_list = prev_day.get('programList', [])
                        if prev_list:
                            last_prog = prev_list[-1]
                            try:
                                prev_start = datetime.strptime(f"{prev_day['date']} {last_prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                                prev_end = datetime.strptime(f"{prev_day['date']} {last_prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                                if prev_end <= prev_start:
                                    prev_end += timedelta(days=1)
                                today_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                                if prev_end > today_start:
                                    need_patch = False
                            except:
                                pass
                    if need_patch:
                        fixed_list.append({
                            "program": "無節目資料",
                            "timeS": "00:00:00",
                            "timeE": first_time
                        })

            fixed_list.extend(prog_list)

            for prog in fixed_list:
                if 'timeS' not in prog or 'timeE' not in prog:
                    continue
                try:
                    start_dt = datetime.strptime(f"{date} {prog['timeS']}", "%Y-%m-%d %H:%M:%S")
                    end_dt = datetime.strptime(f"{date} {prog['timeE']}", "%Y-%m-%d %H:%M:%S")
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                except Exception as time_err:
                    print(f"[時間錯誤] {prog.get('program')} 日期解析失敗: {time_err}")
                    continue

                # 如果跨天，先生成第一段到 00:00，再補第二天副本
                if end_dt.date() > start_dt.date():
                    midnight = datetime.combine(end_dt.date(), datetime.min.time())  # 次日 00:00:00
                    # 第一天节目（结尾为 00:00:00）
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": start_dt,
                        "end": midnight,
                        "desc": ""
                    })
                    # 第二天补上副本
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": midnight,
                        "end": end_dt,
                        "desc": ""
                    })
                else:
                    # 非跨天，正常添加
                    programmes.append({
                        "channel": ch_id,
                        "title": prog["program"],
                        "start": start_dt,
                        "end": end_dt,
                        "desc": ""
                    })

        # 確保順序正確
        programmes.sort(key=lambda x: x["start"])

        return {
            "id": ch_id,
            "name": ch_name,
            "programmes": programmes
        }

    except Exception as e:
        print(f"[錯誤] 抓取 LS-Time 失敗：{e}")
        return None
        
def fetch_celestial_programmes():
    from bs4 import BeautifulSoup
    import requests
    from datetime import datetime, timedelta

    channels = [
        ("天映頻道", "https://www.celestialmovies.com/schedule.php?location/ID", "celestial-movies-hd"),
    ]

    celestial_by_channel = {}

    for name, url, ch_id in channels:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            items = soup.select("div.schedule-item")
            now_date = datetime.now() + timedelta(hours=8)
            today_str = now_date.strftime("%Y-%m-%d")

            programmes = []
            for i, item in enumerate(items):
                time_tag = item.select_one(".schedule-time")
                if not time_tag:
                    continue
                time_str = time_tag.get_text(strip=True)

                title_tag = item.select_one(".programme-title")
                desc_tag = item.select_one(".schedule-description")

                title = title_tag.get_text(strip=True) if title_tag else "無節目資料"
                desc = desc_tag.get_text(strip=True) if desc_tag else ""

                try:
                    if "am" in time_str.lower() or "pm" in time_str.lower():
                        start = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %I:%M%p")
                    else:
                        start = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %H:%M")
                except Exception:
                    print(f"[錯誤] 無法解析時間：{time_str}（頻道：{name}）")
                    continue
                start = start + timedelta(hours=1)# 将开始时间推迟 1 小时
                if i + 1 < len(items):
                    next_time_str = items[i + 1].select_one(".schedule-time").get_text(strip=True)
                    try:
                        if "am" in next_time_str.lower() or "pm" in next_time_str.lower():
                            end = datetime.strptime(f"{today_str} {next_time_str}", "%Y-%m-%d %I:%M%p")
                        else:
                            end = datetime.strptime(f"{today_str} {next_time_str}", "%Y-%m-%d %H:%M")
                        if end <= start:
                            end += timedelta(days=1)
                    except Exception:
                        end = start + timedelta(hours=2)
                else:
                    end = start + timedelta(hours=2)
                end = end + timedelta(hours=1)# 将结束时间推迟 1 小时
                if end.date() > start.date():
                    midnight = datetime.combine(end.date(), datetime.min.time())
                    programmes.append({
                        "channel": ch_id,
                        "start": start,
                        "end": midnight,
                        "title": title,
                        "desc": desc,
                        "name": name,
                    })
                    programmes.append({
                        "channel": ch_id,
                        "start": midnight,
                        "end": end,
                        "title": title,
                        "desc": desc,
                        "name": name,
                    })
                else:
                    programmes.append({
                        "channel": ch_id,
                        "start": start,
                        "end": end,
                        "title": title,
                        "desc": desc,
                        "name": name,
                    })

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
                        "name": name,
                    })

            celestial_by_channel[ch_id] = programmes

        except Exception as e:
            print(f"[錯誤] 抓取 {name} 失敗：{e}")
            celestial_by_channel[ch_id] = []

    return celestial_by_channel

# --- XML UTILITY FUNCTIONS ---

def fmt(dt):
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y%m%d%H%M%S") + " +0800"

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i
        
def write_xml(root_element, filepath):
    indent(root_element)
    tree = ElementTree(root_element)
    with open(filepath, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True, short_empty_elements=False)

def parse_xmltv_time(timestr):
    timestr = timestr.replace(" ", "")  # 去掉空格
    if len(timestr) > 14 and (timestr[-5] in ['+', '-']):
        # 有时区的格式
        return datetime.strptime(timestr, "%Y%m%d%H%M%S%z")
    else:
        # 没有时区，解析后补时区（+0800）
        dt = datetime.strptime(timestr, "%Y%m%d%H%M%S")
        return dt.replace(tzinfo=timezone(timedelta(hours=8)))

def p_time(p):
    return p['start'] if isinstance(p['start'], datetime) else parse_xmltv_time(p['start'])

def write_channel_and_programmes(xml_root, ch_id, ch_name, programmes, with_desc=True):
    ch_el = SubElement(xml_root, "channel", id=ch_name)
    SubElement(ch_el, "display-name").text = ch_name
    for p in sorted(programmes, key=lambda x: p_time(x)):
        prog_el = SubElement(xml_root, "programme",
                             start=fmt(p['start']),
                             stop=fmt(p['end']),
                             channel=ch_name)
        SubElement(prog_el, "title").text = p['title']
        SubElement(prog_el, "desc").text = p['desc'] if with_desc else ""

# --- MAIN EXECUTION ---

def main():
    # --- FETCH DATA (API now fetches 3 days) ---
    epg_programmes = fetch_api_programmes(channels_api, channel_map, three_day_list)
    ottltv_programmes = fetch_ottltv_programmes()
    ls_time = fetch_ls_time_programmes()
    celestial_programmes = fetch_celestial_programmes()

    tv_epg = Element("tv")
    tv_boss = Element("tv")

    epg_by_channel = {}
    for p in epg_programmes:
        epg_by_channel.setdefault(p['channel'], []).append(p)

    all_channels = []

    # --- AGGREGATE API CHANNELS ---
    for name in channels_api:
        real_id = next(
            (cid for cid, names in channel_map.items()
             if (isinstance(names, list) and name in names) or (isinstance(names, str) and name == names)),
            None
        )
        if not real_id:
            continue
        programmes = epg_by_channel.get(real_id, [])
        all_channels.append((real_id, name, programmes, True))

    # --- AGGREGATE OTHER CHANNELS ---
    for cid, cname in channels_ottltv.items():
        programmes = ottltv_programmes.get(cid, [])
        all_channels.append((cid, cname, programmes, False))

    if ls_time:
        all_channels.append((ls_time['id'], ls_time['name'], ls_time['programmes'], True))

    for ch_id, ch_name in {
        "celestial-movies-hd": "天映頻道",
    }.items():
        if ch_id in celestial_programmes:
            all_channels.append((ch_id, ch_name, celestial_programmes[ch_id], True))

    # --- WRITE XML FILES ---
    for ch_id, ch_name, programmes, with_desc in all_channels:
        write_channel_and_programmes(tv_epg, ch_id, ch_name, programmes, with_desc)

    for ch_id, ch_name, programmes, with_desc in all_channels:
        if (
            ch_id in channels_ottltv
            or ch_id == "LS-Time"
            or ch_id in celestial_programmes
        ):
            write_channel_and_programmes(tv_boss, ch_id, ch_name, programmes, with_desc)

    write_xml(tv_epg, "epg.xml")
    write_xml(tv_boss, "boss.xml")
    
if __name__ == "__main__":
    main()
