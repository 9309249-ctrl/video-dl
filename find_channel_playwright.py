#!/usr/bin/env python3
"""Use Playwright to find Israeli YouTube channel IDs.
Works from GitHub Actions (Playwright bypasses bot detection for browsing).
"""
import asyncio, json, sys, re
from xml.etree import ElementTree as ET
import urllib.request

RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id="


def check_rss(channel_id):
    try:
        url = RSS_BASE + channel_id
        with urllib.request.urlopen(url, timeout=10) as r:
            content = r.read().decode()
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        title_el = root.find("atom:title", ns)
        entries = root.findall("atom:entry", ns)
        titles = []
        for entry in entries[:5]:
            t = entry.find("atom:title", ns)
            if t is not None:
                titles.append(t.text[:60])
        return {
            "name": title_el.text if title_el is not None else "?",
            "count": len(entries),
            "titles": titles
        }
    except Exception as e:
        return {"error": str(e)}


async def visit_page(url, browser):
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
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        print(f"  Nav error for {url}: {e}", file=sys.stderr)

    await asyncio.sleep(4)
    content = await page.content()
    await ctx.close()
    return content


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-blink-features=AutomationControlled"]
        )

        # Step 1: Try known Israeli channel handles directly
        handles_to_try = [
            ("reshet13", "Reshet 13"),
            ("keshet12", "Keshet 12"),
            ("kan11", "Kan 11"),
            ("reshet13official", "Reshet 13 official"),
            ("reshet", "Reshet"),
            ("masterchefisrael", "MasterChef Israel"),
            ("masterchefil", "MC Israel alt"),
        ]

        print("\n=== Direct handle lookups ===")
        found_channels = {}

        for handle, label in handles_to_try:
            url = f"https://www.youtube.com/@{handle}"
            print(f"\nVisiting {url} ({label})...", file=sys.stderr)
            content = await visit_page(url, browser)

            # Extract channel ID from page
            cids = re.findall(r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', content)
            external_id = re.findall(r'"externalId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', content)
            all_ids = list(set(cids + external_id))

            if all_ids:
                for cid in all_ids[:2]:
                    rss = check_rss(cid)
                    print(f"  @{handle} = {cid} | {rss.get('name', '?')} | {rss.get('count', 0)} videos")
                    if rss.get('titles'):
                        for t in rss['titles'][:2]:
                            print(f"    - {t}")
                    found_channels[cid] = {"handle": handle, "label": label, "rss": rss}
            else:
                # Check if we got a 404 or redirect
                if "404" in content[:500] or "not found" in content[:500].lower():
                    print(f"  @{handle}: 404 not found")
                else:
                    print(f"  @{handle}: loaded but no channel ID found")

        # Step 2: Search YouTube for videos and extract channels
        print("\n=== Video search for מרוץ למיליון ===")
        search_url = "https://www.youtube.com/results?search_query=מרוץ+למיליון+עונה+2+פרק"
        content = await visit_page(search_url, browser)
        cids = re.findall(r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', content)
        ch_names_raw = re.findall(r'"longBylineText".*?"text"\s*:\s*"([^"]+)"', content[:100000])
        print(f"  Channel IDs in results: {set(cids)}", file=sys.stderr)
        print(f"  Channel names: {ch_names_raw[:5]}", file=sys.stderr)
        for cid in set(cids):
            if cid not in found_channels:
                rss = check_rss(cid)
                if rss.get('name') and 'מרוץ' in str(rss.get('titles', [])):
                    print(f"  {cid}: {rss.get('name')} | {rss.get('count')} videos")
                    print(f"    Titles: {rss.get('titles', [])[:2]}")
                    found_channels[cid] = {"context": "marotz_search", "rss": rss}

        print("\n=== Video search for מאסטר שף ===")
        search_url2 = "https://www.youtube.com/results?search_query=מאסטר+שף+ישראל+עונה+12+פרק+1"
        content2 = await visit_page(search_url2, browser)
        cids2 = re.findall(r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', content2)
        print(f"  Channel IDs: {set(cids2)}", file=sys.stderr)
        for cid in set(cids2):
            if cid not in found_channels:
                rss = check_rss(cid)
                if rss.get('count', 0) > 5:
                    print(f"  {cid}: {rss.get('name')} | {rss.get('count')} videos")
                    print(f"    Titles: {rss.get('titles', [])[:2]}")
                    found_channels[cid] = {"context": "masterchef_search", "rss": rss}

        await browser.close()

    print("\n=== FINAL RESULTS ===")
    print(json.dumps(found_channels, ensure_ascii=False, indent=2))


asyncio.run(main())
