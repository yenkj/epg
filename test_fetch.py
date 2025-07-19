"""
fetch.py - 抓取天映頻道與天映經典台的 EPG 節目表
"""

from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

def fetch_celestial_programmes():
    """
    抓取两个 Celestial 频道（天映頻道 和 天映經典台）的节目，
    解析 HTML，处理跨天和补 00:00 无节目数据，
    返回格式为 {channel_id: [节目列表]} 的字典。
    """
    channels = [
        ("天映頻道", "https://www.celestialmovies.com/schedule.php?lang=tc", "celestial-movies-hd"),
        ("天映經典台", "https://www.cmclassic.tv/schedule.php?lang=tc", "celestial-classic-hd"),
    ]

    celestial_by_channel = {}

    for name, url, ch_id in channels:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            items = soup.select("div.schedule-item")
            now_date = datetime.now() + timedelta(hours=8)  # +8 时区偏移
            today_str = now_date.strftime("%Y-%m-%d")

            programmes = []
            for i, item in enumerate(items):
                time_tag = item.select_one(".schedule-time")
                if not time_tag:
                    continue
                time_str = time_tag.get_text(strip=True).lower().replace(" ", "")
                
                title_tag = item.select_one(".programme-title")
                desc_tag = item.select_one(".schedule-description")
                
                title = title_tag.get_text(strip=True) if title_tag else "無節目資料"
                desc = desc_tag.get_text(strip=True) if desc_tag else ""

                # 解析时间
                try:
                    if "am" in time_str or "pm" in time_str:
                        start = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d%I:%M%p")
                    else:
                        start = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d%H:%M")
                except Exception:
                    print(f"[錯誤] 無法解析時間：{time_str}（频道：{name}）")
                    continue

                # 计算结束时间
                if i + 1 < len(items):
                    next_time_str = items[i + 1].select_one(".schedule-time").get_text(strip=True).lower().replace(" ", "")
                    try:
                        if "am" in next_time_str or "pm" in next_time_str:
                            end = datetime.strptime(f"{today_str} {next_time_str}", "%Y-%m-%d%I:%M%p")
                        else:
                            end = datetime.strptime(f"{today_str} {next_time_str}", "%Y-%m-%d%H:%M")
                        if end <= start:
                            end += timedelta(days=1)
                    except Exception:
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

            # 补 00:00 无节目资料
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
