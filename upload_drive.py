#!/usr/bin/env python3
import json, os, sys, glob, requests

def get_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["DRIVE_CLIENT_ID"],
        "client_secret": os.environ["DRIVE_CLIENT_SECRET"],
        "refresh_token": os.environ["DRIVE_REFRESH_TOKEN"],
        "grant_type": "refresh_token"
    }, timeout=30)
    return r.json()["access_token"]

def get_or_create_folder(token, name):
    hdrs = {"Authorization": f"Bearer {token}"}
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    res = requests.get("https://www.googleapis.com/drive/v3/files",
                      params={"q": q, "fields": "files(id,name)"}, headers=hdrs, timeout=30)
    folders = res.json().get("files", [])
    if folders:
        return folders[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    res = requests.post("https://www.googleapis.com/drive/v3/files", json=body, headers=hdrs, timeout=30)
    return res.json()["id"]

def upload_file(token, filepath, folder_id):
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    mime = "video/mp4"
    hdrs = {"Authorization": f"Bearer {token}"}
    meta = {"name": filename, "parents": [folder_id]}
    print(f"Uploading {filename} ({filesize/1024/1024:.0f} MB)...")
    init = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
        headers={**hdrs, "Content-Type": "application/json",
                 "X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(filesize)},
        json=meta, timeout=60)
    upload_url = init.headers.get("Location")
    if not upload_url:
        print(f"  No upload URL: {init.text[:200]}")
        return None
    with open(filepath, "rb") as f:
        up = requests.put(upload_url, data=f,
                          headers={"Content-Type": mime, "Content-Length": str(filesize)},
                          timeout=7200)
    if up.ok:
        fid = up.json().get("id", "?")
        print(f"  Uploaded! Drive ID: {fid}")
        return fid
    print(f"  Upload failed: {up.status_code}")
    return None

if __name__ == "__main__":
    folder_name = sys.argv[1] if len(sys.argv) > 1 else "Downloaded Videos"
    token = get_token()
    folder_id = get_or_create_folder(token, folder_name)
    print(f"Drive folder: {folder_name} ({folder_id})")
    video_files = []
    for ext in ["*.mp4", "*.mkv", "*.webm"]:
        video_files.extend(glob.glob(f"/tmp/videos/{ext}"))
    if not video_files:
        print("No video files found in /tmp/videos/")
        sys.exit(0)
    for vf in sorted(video_files):
        fid = upload_file(token, vf, folder_id)
        if fid:
            os.remove(vf)
    print("Done!")
