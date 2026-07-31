#!/usr/bin/env python3
"""Test YouTube download methods from this IP."""
import subprocess, sys, json, os

TEST_VIDEO = "jNQXAC9IVRw"  # Me at the zoo — first YouTube video, public


def run(cmd, timeout=35):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_method(name, extra_args):
    print(f"\n=== {name} ===")
    cmd = (
        ["yt-dlp", "--no-download", "--print", "%(title)s|%(duration)s",
         "--no-warnings"]
        + extra_args
        + [f"https://www.youtube.com/watch?v={TEST_VIDEO}"]
    )
    try:
        rc, out, err = run(cmd, timeout=30)
        if rc == 0:
            print(f"OK: {out}")
            return True
        else:
            print(f"FAIL: {err[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


results = {}
results["basic"] = test_method("Basic", [])
results["ios"] = test_method("iOS", ["--extractor-args", "youtube:player_client=ios"])
results["tv_embedded"] = test_method(
    "TV embedded", ["--extractor-args", "youtube:player_client=tv_embedded"]
)
results["web_creator"] = test_method(
    "Web creator", ["--extractor-args", "youtube:player_client=web_creator"]
)
results["mweb"] = test_method("mweb", ["--extractor-args", "youtube:player_client=mweb"])
results["android"] = test_method(
    "Android", ["--extractor-args", "youtube:player_client=android"]
)

# po-token approach
if os.path.exists("/tmp/yt_tokens.json"):
    with open("/tmp/yt_tokens.json") as f:
        tokens = json.load(f)
    pt = tokens.get("po_token")
    vd = tokens.get("visitor_data")
    print(f"\nTokens: po_token={'YES' if pt else 'NO'}, visitor_data={'YES' if vd else 'NO'}")
    if pt and vd:
        ea_web = f"youtube:player_client=web;po_token=WEB+{pt};visitor_data={vd}"
        results["po_token_web"] = test_method("po-token web", ["--extractor-args", ea_web])
        ea_ios = f"youtube:player_client=ios;po_token=IOS+{pt};visitor_data={vd}"
        results["po_token_ios"] = test_method("po-token ios", ["--extractor-args", ea_ios])
else:
    print("\nNo /tmp/yt_tokens.json found — skipping po-token test")

print("\n" + "=" * 50)
print("SUMMARY:")
for m, ok in results.items():
    print(f"  {m}: {'OK' if ok else 'FAIL'}")

working = [m for m, ok in results.items() if ok]
if working:
    print(f"\nWorking methods: {working}")
    sys.exit(0)
else:
    print("\nAll methods fail — bot detection in effect.")
    sys.exit(1)
