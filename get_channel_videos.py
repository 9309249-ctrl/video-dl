#!/usr/bin/env python3
"""Get YouTube channel videos via RSS feed (no auth required)"""
import requests, json, sys, re
from xml.etree import ElementTree as ET

RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id="

def get_channel_videos_rss(channel_id, min_duration=1800):
    """Get video IDs from YouTube RSS feed, then check duration via yt-dlp"""
    videos = []
    try:
        url = f"{RSS_BASE}{channel_id}"
        r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            print(f"RSS failed: HTTP {r.status_code}")
            return []
        
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        root = ET.fromstring(r.content)
        entries = root.findall('atom:entry', ns)
        print(f"RSS found {len(entries)} recent videos")
        
        for entry in entries:
            vid_id_el = entry.find('yt:videoId', ns)
            title_el = entry.find('atom:title', ns)
            if vid_id_el is not None:
                vid_id = vid_id_el.text
                title = title_el.text if title_el is not None else ''
                videos.append({'id': vid_id, 'title': title, 'duration': 0})
        
        return videos
    except Exception as e:
        print(f"RSS error: {e}")
        return []

def filter_by_duration(videos, min_duration=1800):
    """Use yt-dlp to check duration of each video"""
    import subprocess
    filtered = []
    for v in videos:
        try:
            result = subprocess.run(
                ['yt-dlp', '--no-download', '--print', '%(duration)s',
                 '--no-warnings', f"https://www.youtube.com/watch?v={v['id']}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                dur_str = result.stdout.strip()
                try:
                    dur = int(float(dur_str))
                    v['duration'] = dur
                    if dur >= min_duration:
                        filtered.append(v)
                        print(f"  KEEP [{dur//60}m] {v['id']} | {v['title'][:60]}")
                    else:
                        print(f"  SKIP [{dur//60}m] {v['title'][:50]}")
                except:
                    pass
        except Exception as e:
            print(f"  Error checking {v['id']}: {e}")
    return filtered

if __name__ == "__main__":
    channel_id = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else '/tmp/video_list.json'
    min_dur = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    check_dur = '--check-duration' in sys.argv
    
    if not channel_id:
        print("Usage: get_channel_videos.py CHANNEL_ID output.json [min_seconds] [--check-duration]")
        sys.exit(1)
    
    videos = get_channel_videos_rss(channel_id, min_dur)
    print(f"RSS: found {len(videos)} videos total")
    
    if check_dur and videos:
        print("Checking durations via yt-dlp (may take a while)...")
        videos = filter_by_duration(videos, min_dur)
    
    print(f"Saving {len(videos)} videos to {output_file}")
    for v in videos[:10]:
        dur = v.get('duration', 0)
        dur_str = f"{dur//60}m" if dur else "?"
        print(f"  [{dur_str}] {v['id']} | {v['title'][:70]}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
