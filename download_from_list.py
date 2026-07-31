#!/usr/bin/env python3
"""Download videos from JSON list using yt-dlp"""
import json, subprocess, os, glob, sys

def download_video(vid_id, out_dir, index):
    cmd = [
        'yt-dlp',
        '-f', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '-o', f'{out_dir}/{index:03d}_%(title).60s.%(ext)s',
        '--retries', '5',
        '--fragment-retries', '5',
        '--socket-timeout', '60',
        '--no-warnings',
        '--ignore-errors',
        f'https://www.youtube.com/watch?v={vid_id}'
    ]
    result = subprocess.run(cmd, timeout=7200)
    return result.returncode == 0

if __name__ == "__main__":
    list_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/video_list.json'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/videos'
    max_ep = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        with open(list_file, encoding='utf-8') as f:
            videos = json.load(f)
    except Exception as e:
        print(f"Error reading list: {e}")
        sys.exit(1)
    
    videos = videos[:max_ep]
    print(f"Downloading {len(videos)} episodes to {out_dir}")
    
    ok = 0
    for i, v in enumerate(videos, 1):
        vid_id = v['id']
        title = v.get('title', vid_id)[:60]
        dur = v.get('duration', 0)
        print(f"\n[{i}/{len(videos)}] {title} ({dur//60}min)")
        if download_video(vid_id, out_dir, i):
            files = glob.glob(f'{out_dir}/{i:03d}_*.mp4')
            if files:
                size = os.path.getsize(files[-1]) / 1024 / 1024
                print(f"  OK: {size:.0f} MB")
                ok += 1
        else:
            print(f"  FAILED")
    
    all_files = glob.glob(f'{out_dir}/*.mp4')
    print(f"\nSuccess: {ok}/{len(videos)} | Total files: {len(all_files)}")
    total_size = sum(os.path.getsize(f) for f in all_files) / 1024 / 1024 / 1024
    print(f"Total size: {total_size:.1f} GB")
