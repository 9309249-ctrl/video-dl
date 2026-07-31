#!/usr/bin/env python3
"""Find MasterChef Israel YouTube channel ID via RSS."""
import requests
from xml.etree import ElementTree as ET

CANDIDATES = [
    ("UCrOvNizOg3TUfC7fBfZuDzw", "Original guess"),
    ("UCIvUJ_TjFBL7nT4BSWPG9Wg", "Keshet 12"),
    ("UCy5EIKi9xIhRlFqZeQMV1Jg", "Reshet 13"),
    ("UCsT0YIqwnpJCM-mx7-gSA4Q", "Keshet VOD"),
    ("UCQHvCWVq1nwDLMSWbHaMfSQ", "Reshet13 alt"),
    ("UC8N5WtNzV5pZYHE4lLwrpbQ", "MasterChef Israel guess 2"),
    ("UCHDeHYhAzfMYblww3m7I8wQ", "MasterChef Israel guess 3"),
]

RSS = "https://www.youtube.com/feeds/videos.xml?channel_id="
ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

for cid, label in CANDIDATES:
    try:
        r = requests.get(RSS + cid, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"{label} ({cid}): HTTP {r.status_code}")
            continue
        root = ET.fromstring(r.content)
        entries = root.findall("atom:entry", ns)
        title_el = root.find("atom:title", ns)
        feed_title = title_el.text if title_el is not None else "?"
        print(f"\n{label} ({cid}): {len(entries)} videos | Feed: {feed_title}")
        for entry in entries[:3]:
            vid_id = entry.find("yt:videoId", ns)
            title = entry.find("atom:title", ns)
            if vid_id is not None:
                t = title.text[:70] if title is not None else "?"
                print(f"  - {t}")
    except Exception as e:
        print(f"{label} ({cid}): ERROR {e}")

# Try oembed for handles
print("\n--- Handle lookups via oEmbed ---")
handles = ["masterchefisrael", "masterchefil", "keshet12"]
for h in handles:
    try:
        r = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/@{h}&format=json",
            timeout=10
        )
        print(f"@{h}: HTTP {r.status_code} | {r.text[:150]}")
    except Exception as e:
        print(f"@{h}: ERROR {e}")
