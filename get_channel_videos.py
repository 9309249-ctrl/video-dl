#!/usr/bin/env python3
"""Get YouTube channel videos via RSS feed (no auth required)"""
import requests, json, sys, subprocess
from xml.etree import ElementTree as ET

RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id="


def get_channel_videos_rss(channel_id):
    url = f"{RSS_BASE}{channel_id}"
    r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
    if r.status_code != 200:
        print(f"RSS HTTP {r.status_code}")
        return []

    ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
    root = ET.fromstring(r.content)
    entries = root.findall('atom:entry', ns)
    print(f"RSS: {len(entries)} recent videos")

    videos = []
    for entry in entries:
        vid_id_el = entry.find('yt:videoId', ns)
        title_el = entry.find('atom:title', ns)
        if vid_id_el is not None:
            videos.append({
                'id': vid_id_el.text,
                'title': title_el.text if title_el is not None else '',
                'duration': 0
            })
    return videos


if __name__ == "__main__":
    channel_id = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else '/tmp/video_list.json'
    min_dur = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    if not channel_id:
        print("Usage: get_channel_videos.py CHANNEL_ID output.json [min_seconds]")
        sys.exit(1)

    videos = get_channel_videos_rss(channel_id)
    print(f"Found {len(videos)} videos")
    for v in videos[:5]:
        print(f"  {v['id']} | {v['title'][:70]}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(videos)} to {output_file}")
