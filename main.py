import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
import time

BASE_URL = "https://hoadaotv.info"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": BASE_URL,
    "Accept": "*/*"
}


# ✅ retry fetch (chống bị block)
def fetch(url):
    for i in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                return res.text
        except:
            time.sleep(1)
    return ""


# ✅ quét mạnh tất cả stream
def extract_streams(html):
    return list(set(
        re.findall(r'https?://[^"\']+\.(?:m3u8|flv)', html)
    ))


# ✅ chọn link tốt nhất
def pick_best(streams):
    m3u8_hd = None
    m3u8 = None
    flv = None

    for url in streams:
        u = url.lower()

        if ".m3u8" in u:
            if "hd" in u or "fhd" in u:
                m3u8_hd = url
            else:
                m3u8 = url
        elif ".flv" in u:
            flv = url

    return m3u8_hd or m3u8 or flv


# ✅ crawl hoadao
def process_hoadao():
    results = []

    html = fetch(BASE_URL)
    if not html:
        print("❌ Không load được trang chủ")
        return results

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    # quét rộng để tránh miss
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(x in href for x in ["truc-tiep", "xem", "live"]):
            url = href if href.startswith("http") else BASE_URL + href
            links.add(url)

    print(f"🔎 Found {len(links)} match pages")

    for url in links:
        page = fetch(url)
        if not page:
            continue

        streams = extract_streams(page)

        print("👉", url)
        print("   streams:", len(streams))

        if not streams:
            continue

        best = pick_best(streams)
        if not best:
            continue

        s = BeautifulSoup(page, "html.parser")

        title = "HoaDao TV"
        h1 = s.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        results.append({
            "title": title,
            "logo": BASE_URL + "/favicon.ico",
            "url": best
        })

    print(f"✅ Hoadao lấy được: {len(results)} kênh")
    return results


# ✅ fallback nếu hoadao die
def fallback():
    print("⚠️ Dùng fallback")

    return [{
        "title": "Fallback Channel",
        "logo": "",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    }]


# ✅ ghi file
def write_m3u(data):
    content = "#EXTM3U\n"

    for item in data:
        content += f'#EXTINF:-1 tvg-logo="{item["logo"]}",{item["title"]}\n'
        content += f'{item["url"]}\n\n'

    with open("hoadaopro.m3u", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📺 Ghi file thành công: {len(data)} kênh")


# 🚀 MAIN
if __name__ == "__main__":
    data = process_hoadao()

    # ❗ chống rỗng
    if not data:
        data = fallback()

    write_m3u(data)

    print("✅ DONE")
