import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from html.parser import HTMLParser
import urllib.request
import re

# 频道映射加载
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

channels = [
  "凤凰中文",
  "凤凰资讯",
  "凤凰香港"
]

today = datetime.utcnow() + timedelta(hours=8)
date_str = today.strftime('%Y%m%d')
yesterday_str = (today - timedelta(days=1)).strftime('%Y%m%d')

# 创建根节点（epg.xml）
tv_epg = Element('tv')
added_channels_epg = set()

# 创建根节点（boss.xml）
tv_boss = Element('tv')
added_channels_boss = set()

# --------- 原有拉取EPG部分 ---------
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

for name in channels:
    real_id = None
    for cid, names in channel_map.items():
        if name in names:
            real_id = cid
            break
    if not real_id:
        continue

    # 写入 epg.xml 的频道
    if real_id not in added_channels_epg:
        channel_el = SubElement(tv_epg, 'channel', id=real_id)
        display_name = SubElement(channel_el, 'display-name')
        display_name.text = name
        added_channels_epg.add(real_id)

    try:
        xml_today = fetch_epg(real_id, date_str)
        xml_yesterday = fetch_epg(real_id, yesterday_str)

        today_programmes = parse_epg(xml_today, date_str, mode='today')
        carryover_programmes = parse_epg(xml_yesterday, date_str, mode='carry')

        if today_programmes:
            first_start = today_programmes[0][0]
            if not first_start.endswith("0000"):
                if carryover_programmes:
                    last_prog = carryover_programmes[-1]
                    carry_start = date_str + "000000"
                    carry_end = first_start
                    title, desc = last_prog[2], last_prog[3]
                    today_programmes.insert(0, (carry_start, carry_end, title, desc))

        # 写入 epg.xml 的节目
        for start, stop, title, desc in today_programmes:
            programme = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=real_id)
            title_el = SubElement(programme, 'title')
            title_el.text = title
            if desc:
                desc_el = SubElement(programme, 'desc')
                desc_el.text = desc

    except Exception as e:
        print(f"[错误] 获取频道 {name} 失败：{e}")

# --------- LTV 解析部分 ---------
URL = "https://www.ltv.com.tw/ott%e7%af%80%e7%9b%ae%e8%a1%a8/"

class LtvParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_column = None
        self.timetable_column_id = None
        self.channels = {}
        self.in_item = False
        self.in_name = False
        self.in_time = False
        self.in_desc = False
        self.buffer = ''
        self.current_program = {}
        self.programs = []
        self.in_popup = False
        self.current_popup_id = None
        self.popups = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'class' in attrs:
            if 'timetable-column' in attrs['class']:
                self.timetable_column_id = attrs.get('id','')
                if self.timetable_column_id == 'ott-animation':
                    self.in_column = 'ott-animation'
                    self.channels['ott-animation'] = '龍華卡通台'
                elif self.timetable_column_id == 'ott-motion':
                    self.in_column = 'ott-motion'
                    self.channels['ott-motion'] = '龍華日韓台'
                else:
                    self.in_column = None

            if 'timetable-popup' in attrs.get('class',''):
                self.in_popup = True
                self.current_popup_id = attrs.get('id','')
                self.popups[self.current_popup_id] = {'desc': '', 'time': ''}

        if tag == 'a' and self.in_column and 'class' in attrs and 'timetable-title' in attrs['class']:
            self.in_item = True
            href = attrs.get('href','')
            popup_id = href.replace('#','') if href.startswith('#') else ''
            self.current_program = {
                'channel': self.in_column,
                'popup_id': popup_id,
                'title': '',
                'time_str': '',
                'desc': ''
            }
            self.buffer = ''

        if self.in_item and tag == 'div' and 'class' in attrs:
            if attrs['class'] == 'timetable-name':
                self.in_name = True
                self.buffer = ''
            elif attrs['class'] == 'timetable-time':
                self.in_time = True
                self.buffer = ''

        if self.in_popup and tag == 'div' and 'class' in attrs:
            if attrs['class'] == 'timetable-time':
                self.in_time = True
                self.buffer = ''
            elif attrs['class'] == 'timetable-desc':
                self.in_desc = True
                self.buffer = ''

    def handle_endtag(self, tag):
        if self.in_name and tag == 'div':
            self.in_name = False
            self.current_program['title'] = self.buffer.strip()

        if self.in_time and tag == 'div':
            self.in_time = False
            if self.in_popup and self.current_popup_id:
                self.popups[self.current_popup_id]['time'] = self.buffer.strip()
            else:
                self.current_program['time_str'] = self.buffer.strip()

        if self.in_desc and tag == 'div':
            self.in_desc = False
            if self.in_popup and self.current_popup_id:
                self.popups[self.current_popup_id]['desc'] = self.buffer.strip()

        if self.in_item and tag == 'a':
            pid = self.current_program.get('popup_id','')
            if pid and pid in self.popups:
                if self.popups[pid]['time']:
                    self.current_program['time_str'] = self.popups[pid]['time']
                if self.popups[pid]['desc']:
                    self.current_program['desc'] = self.popups[pid]['desc']
            if self.current_program.get('title',''):
                self.programs.append(self.current_program)
            self.in_item = False
            self.current_program = {}

        if self.in_popup and tag == 'div':
            self.in_popup = False
            self.current_popup_id = None

    def handle_data(self, data):
        if self.in_name or self.in_time or self.in_desc:
            self.buffer += data

def parse_time_range(date_str, time_range_str):
    try:
        start_str, end_str = [t.strip() for t in time_range_str.split('-')]
    except:
        return None, None
    dt_format = "%Y/%m/%d %H:%M"

    start_dt = datetime.strptime(f"{date_str} {start_str}", dt_format)
    end_dt = datetime.strptime(f"{date_str} {end_str}", dt_format)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt

def format_xml_datetime(dt):
    return dt.strftime('%Y%m%d%H%M%S') + " +0800"

# 抓取并添加LTV节目到两个tv根节点
def add_ltv_programmes():
    print("抓取LTV节目单中...")
    resp = urllib.request.urlopen(URL)
    html = resp.read().decode('utf-8')
    parser = LtvParser()
    parser.feed(html)

    today_date = datetime.now().strftime('%Y/%m/%d')

    # 先加入频道
    for ch_id, ch_name in parser.channels.items():
        # epg.xml频道添加
        if ch_id not in added_channels_epg:
            ch_el = SubElement(tv_epg, 'channel', id=ch_id)
            dn_el = SubElement(ch_el, 'display-name')
            dn_el.text = ch_name
            added_channels_epg.add(ch_id)

        # boss.xml频道添加
        if ch_id not in added_channels_boss:
            ch_el_boss = SubElement(tv_boss, 'channel', id=ch_id)
            dn_el_boss = SubElement(ch_el_boss, 'display-name')
            dn_el_boss.text = ch_name
            added_channels_boss.add(ch_id)

    for p in parser.programs:
        timestr = p.get('time_str', '')
        m = re.search(r'(\d{4}/\d{2}/\d{2})\s*(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})', timestr)
        if m:
            date_str = m.group(1)
            time_range = m.group(2)
        else:
            date_str = today_date
            time_range = timestr

        start_dt, end_dt = parse_time_range(date_str, time_range)
        if start_dt and end_dt:
            start = format_xml_datetime(start_dt)
            stop = format_xml_datetime(end_dt)
        else:
            start = ''
            stop = ''

        ch_id = p.get('channel','')

        # epg.xml 节目添加
        prog_el = SubElement(tv_epg, 'programme', start=start, stop=stop, channel=ch_id)
        title_el = SubElement(prog_el, 'title')
        title_el.text = p.get('title','')
        desc_text = p.get('desc','')
        if desc_text:
            desc_el = SubElement(prog_el, 'desc')
            desc_el.text = desc_text

        # boss.xml 节目添加
        prog_el_boss = SubElement(tv_boss, 'programme', start=start, stop=stop, channel=ch_id)
        title_el_boss = SubElement(prog_el_boss, 'title')
        title_el_boss.text = p.get('title','')
        if desc_text:
            desc_el_boss = SubElement(prog_el_boss, 'desc')
            desc_el_boss.text = desc_text

    print("LTV节目单添加完成。")

add_ltv_programmes()

# 写入 epg.xml (所有频道)
tree_epg = ElementTree(tv_epg)
tree_epg.write('epg.xml', encoding='utf-8', xml_declaration=True)

# 写入 boss.xml (仅LTV频道)
tree_boss = ElementTree(tv_boss)
tree_boss.write('boss.xml', encoding='utf-8', xml_declaration=True)

print("epg.xml 和 boss.xml 已生成。")
