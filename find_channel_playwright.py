#!/usr/bin/env python3
"""Use Playwright to search YouTube and find channel IDs.
Works from GitHub Actions (Playwright bypasses bot detection for browsing).
"""
import asyncio, json, sys, re

SEARCHES = [
    "מאסטר שף ישראל עונה 12",
    "masterchef israel season 12",
    "רשת 13 מאסטר שף",
]


async def find_channel(query):
    from playwright.async_api import async_playwright
    found = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="he-IL",
            timezone_id="Asia/Jerusalem"
        )
        page = await ctx.new_page()

        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp=EgIQAg%253D%253D"
        print(f"\nSearching: {query}", file=sys.stderr)
        print(f"URL: {search_url}", file=sys.stderr)

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"Nav error: {e}", file=sys.stderr)

        await asyncio.sleep(5)

        # Extract channel links and IDs from page content
        content = await page.content()

        # Find channel IDs in page HTML
        channel_ids = re.findall(r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', content)
        channel_names = re.findall(r'"ownerText"\s*:\s*\{"runs"\s*:\s*\[\{"text"\s*:\s*"([^"]+)"', content)
        channel_urls = re.findall(r'"canonicalBaseUrl"\s*:\s*"(/channel/[^"]+|/@[^"]+)"', content)

        print(f"Channel IDs found: {set(channel_ids)}", file=sys.stderr)
        print(f"Channel names found: {channel_names[:5]}", file=sys.stderr)
        print(f"Channel URLs found: {channel_urls[:5]}", file=sys.stderr)

        # Also look for video items with channel info
        items = re.findall(
            r'"videoId"\s*:\s*"([^"]+)".*?"ownerText".*?"text"\s*:\s*"([^"]+)".*?"canonicalBaseUrl"\s*:\s*"([^"]+)"',
            content[:200000]
        )
        for vid_id, owner, url in items[:5]:
            print(f"  Video {vid_id} | Channel: {owner} | URL: {url}", file=sys.stderr)

        for cid in channel_ids:
            found[cid] = found.get(cid, 0) + 1

        await browser.close()

    return found


async def main():
    all_found = {}
    for query in SEARCHES[:2]:  # Limit to 2 searches to save time
        result = await find_channel(query)
        for cid, count in result.items():
            all_found[cid] = all_found.get(cid, 0) + count

    print("\n=== Channel IDs found ===")
    if all_found:
        for cid, count in sorted(all_found.items(), key=lambda x: -x[1]):
            print(f"  {cid} (seen {count} times)")
            # Test RSS for this channel
            import urllib.request
            try:
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
                with urllib.request.urlopen(rss_url, timeout=10) as r:
                    content = r.read().decode()
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    title_el = root.find("atom:title", ns)
                    entries = root.findall("atom:entry", ns)
                    print(f"    RSS: {len(entries)} videos | Name: {title_el.text if title_el is not None else '?'}")
            except Exception as e:
                print(f"    RSS error: {e}")
    else:
        print("  No channels found")

    # Output JSON result
    result = {"channels": all_found}
    print("\n" + json.dumps(result))


asyncio.run(main())
