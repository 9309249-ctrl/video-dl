#!/usr/bin/env python3
"""Download videos from JSON list using yt-dlp, filter by minimum duration"""
import json, subprocess, os, glob, sys

YT_EXTRA = [
    '--extractor-args', 'youtube:player_client=ios,web',
    '--sleep-interval', '1',
    '--max-sleep-interval', '3',
    '--user-agent', 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iPhone OS 17_5_1 like Mac OS X)',
]

# Set via __main__ before calling download functions
COOKIES_FILE = None


def _cookies_args():
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        return ['--cookies', COOKIES_FILE]
    return []


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
        *_cookies_args(),
        *YT_EXTRA,
        f'https://www.youtube.com/watch?v={vid_id}'
    ]
    result = subprocess.run(cmd, timeout=7200)
    return result.returncode == 0


def check_duration(vid_id):
    result = subprocess.run(
        ['yt-dlp', '--no-download', '--print', '%(duration)s',
         '--no-warnings', *_cookies_args(), *YT_EXTRA,
         f'https://www.youtube.com/watch?v={vid_id}'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return -1
    try:
        return int(float(result.stdout.strip()))
    except Exception:
        return -1


if __name__ == "__main__":
    import download_from_list as _mod

    list_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/video_list.json'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/videos'
    max_ep = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    min_dur = int(sys.argv[4]) if len(sys.argv) > 4 else 1800

    # Optional 5th arg: cookies file path or "--cookies /path/to/file"
    raw = sys.argv[5] if len(sys.argv) > 5 else ""
    if raw.startswith('--cookies'):
        _mod.COOKIES_FILE = raw.split()[-1]
    elif raw and not raw.startswith('-'):
        _mod.COOKIES_FILE = raw
    # else COOKIES_FILE stays None

    if _mod.COOKIES_FILE:
        print(f"Using cookies: {_mod.COOKIES_FILE}")

    os.makedirs(out_dir, exist_ok=True)

    try:
        with open(list_file, encoding='utf-8') as f:
            videos = json.load(f)
    except Exception as e:
        print(f"Error reading list: {e}")
        sys.exit(1)

    videos = videos[:max_ep * 3]  # check more than max_ep in case some are short
    print(f"Checking {len(videos)} videos (downloading up to {max_ep} full episodes > {min_dur//60}min)...")

    ok = 0
    for i, v in enumerate(videos, 1):
        if ok >= max_ep:
            break
        vid_id = v['id']
        title = v.get('title', vid_id)[:60]
        print(f"\n[{i}] {title}")

        dur = v.get('duration', 0)
        if dur == 0:
            dur = _mod.check_duration(vid_id)

        if dur < min_dur and dur != -1:
            print(f"  Skip: {dur//60}m (min {min_dur//60}m)")
            continue
        elif dur == -1:
            print(f"  Skip: can't get duration (bot detection?)")
            continue

        print(f"  Duration: {dur//60}m - downloading...")
        if _mod.download_video(vid_id, out_dir, ok + 1):
            files = glob.glob(f'{out_dir}/{ok+1:03d}_*')
            if files:
                size = os.path.getsize(files[0]) / 1024 / 1024
                print(f"  OK: {size:.0f} MB")
                ok += 1
        else:
            print(f"  FAILED")

    all_files = glob.glob(f'{out_dir}/*.mp4')
    print(f"\nDone: {ok} episodes downloaded | {len(all_files)} total files")
    total_gb = sum(os.path.getsize(f) for f in all_files) / 1024**3
    print(f"Total size: {total_gb:.1f} GB")
