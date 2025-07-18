import os
import json
import requests
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree

# 加载本地频道映射文件（只使用左边中文名）
with open('epg/channel-map.json', encoding='utf-8') as f:
    channel_map = json.load(f)

# 自定义要生成 EPG 的频道（只填中文名）
channels = [
  "凤凰中文",
  "凤凰资讯",
  "凤凰香港"
  "A&E_East",
  "ACC-Network"
]

# 当前日期（北京时间）
today = datetime.utcnow() + timedelta(hours=8)
date_str = today.strftime('%Y%m%d')
yesterday_str = (today - timedelta(days=1)).strftime('%Y%m%d')

# XML 根节点
tv = Element('tv')

# 拉取 EPG
def fetch_epg(channel_id, date_str):
    url = f"https://epg.pw/api/epg.xml?lang=zh-hans&timezone=QXNpYS9TaGFuZ2hhaQ==&date={date_str}&channel_id={channel_id}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

# 解析 XML 字符串提取节目（只要指定日期的）
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

# 遍历频道
for name in channels:
    # 找到 channel id
    real_id = None
    for cid, names in channel_map.items():
        if name in names:
            real_id = cid
            break
    if not real_id:
        continue

    # 添加 channel 元素
    channel_el = SubElement(tv, 'channel', id=real_id)
    display_name = SubElement(channel_el, 'display-name')
    display_name.text = name

    try:
        # 获取今天和昨天的节目数据
        xml_today = fetch_epg(real_id, date_str)
        xml_yesterday = fetch_epg(real_id, yesterday_str)

        today_programmes = parse_epg(xml_today, date_str, mode='today')
        carryover_programmes = parse_epg(xml_yesterday, date_str, mode='carry')

        # 判断是否需要补全 00:00 节目
        if today_programmes:
            first_start = today_programmes[0][0]
            if not first_start.endswith("0000"):  # 如果不是 00:00 开始
                if carryover_programmes:
                    last_prog = carryover_programmes[-1]
                    carry_start = date_str + "000000"
                    carry_end = first_start
                    title, desc = last_prog[2], last_prog[3]
                    # 插入补全节目到最前
                    today_programmes.insert(0, (carry_start, carry_end, title, desc))

        # 添加到 XML
        for start, stop, title, desc in today_programmes:
            programme = SubElement(tv, 'programme', start=start, stop=stop, channel=real_id)
            title_el = SubElement(programme, 'title')
            title_el.text = title
            if desc:
                desc_el = SubElement(programme, 'desc')
                desc_el.text = desc

    except Exception as e:
        print(f"[错误] 获取频道 {name} 失败：{e}")

# 写入 epg.xml
tree = ElementTree(tv)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
