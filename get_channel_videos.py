#!/usr/bin/env python3
"""Get YouTube channel videos via Invidious API"""
import requests, json, sys, os

INVIDIOUS = [
    "https://inv.tux.pizza",
    "https://invidious.privacydev.net",
    "https://invidious.fdn.fr",
    "https://yt.artemislena.eu",
    "https://invidious.io.lol"
]

def get_channel_videos(channel_id, min_duration=1800, max_pages=3):
    videos = []
    for instance in INVIDIOUS:
        try:
            for page in range(1, max_pages+1):
                url = f"{instance}/api/v1/channels/{channel_id}/videos?page={page}&sort_by=newest"
                r = requests.get(url, timeout=15)
                if r.status_code != 200:
                    break
                data = r.json()
                vids = data.get('videos', [])
                if not vids:
                    break
                for v in vids:
                    if v.get('lengthSeconds', 0) >= min_duration:
                        videos.append({
                            'id': v.get('videoId'),
                            'title': v.get('title', ''),
                            'duration': v.get('lengthSeconds', 0),
                            'published': v.get('published', 0)
                        })
            if videos:
                print(f"OK: {instance} -> {len(videos)} full episodes")
                break
        except Exception as e:
            print(f"FAIL: {instance}: {e}")
    return videos

if __name__ == "__main__":
    channel_id = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else '/tmp/video_list.json'
    min_dur = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    
    if not channel_id:
        print("Usage: get_channel_videos.py CHANNEL_ID output.json [min_seconds]")
        sys.exit(1)
    
    videos = get_channel_videos(channel_id, min_dur)
    print(f"Total episodes found: {len(videos)}")
    for v in videos[:10]:
        print(f"  [{v['duration']//60}m] {v['id']} | {v['title'][:70]}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")
