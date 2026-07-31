#!/usr/bin/env python3
"""Extract YouTube po_token and visitor_data using Playwright.
Outputs JSON: {"po_token": "...", "visitor_data": "..."}
"""
import asyncio, json, sys, re

VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

async def extract_tokens():
    from playwright.async_api import async_playwright
    po_token = None
    visitor_data = None

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

        async def on_request(req):
            nonlocal po_token, visitor_data
            if "youtubei/v1" in req.url:
                try:
                    body = req.post_data
                    if body:
                        data = json.loads(body)
                        c = data.get("context", {})
                        cl = c.get("client", {})
                        if "visitorData" in cl and not visitor_data:
                            visitor_data = cl["visitorData"]
                            print(f"visitor_data: {visitor_data[:30]}...", file=sys.stderr)
                        sid = c.get("serviceIntegrityDimensions", {})
                        if "poToken" in sid and not po_token:
                            po_token = sid["poToken"]
                            print(f"po_token (req): {po_token[:30]}...", file=sys.stderr)
                except Exception:
                    pass

        async def on_response(resp):
            nonlocal po_token, visitor_data
            if "youtubei" not in resp.url:
                return
            try:
                body = await resp.text()
                m = re.search(r'"poToken"\s*:\s*"([^"]+)"', body)
                if m and not po_token:
                    po_token = m.group(1)
                    print(f"po_token (resp): {po_token[:30]}...", file=sys.stderr)
                m2 = re.search(r'"visitorData"\s*:\s*"([^"]+)"', body)
                if m2 and not visitor_data:
                    visitor_data = m2.group(1)
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        print("Loading YouTube...", file=sys.stderr)
        try:
            await page.goto(VIDEO_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Nav error: {e}", file=sys.stderr)

        await asyncio.sleep(10)

        if not visitor_data:
            try:
                vd = await page.evaluate(
                    "() => { try { return window.yt && window.yt.config_ "
                    "&& window.yt.config_.VISITOR_DATA; } catch(e) { return null; } }"
                )
                if vd:
                    visitor_data = vd
                    print(f"visitor_data (JS): {vd[:30]}...", file=sys.stderr)
            except Exception:
                pass

        await browser.close()
    return po_token, visitor_data


if __name__ == "__main__":
    po_token, visitor_data = asyncio.run(extract_tokens())
    result = {"po_token": po_token, "visitor_data": visitor_data}
    print(json.dumps(result))
    if not po_token:
        print("WARNING: no po_token extracted", file=sys.stderr)
        sys.exit(1)
