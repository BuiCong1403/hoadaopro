import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://hoadaotv.info"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL
}


def extract_streams(html):
    streams = []

    # ✅ 1. Bắt JSON dạng "hd" / "flv"
    for key in ["hd", "hls", "flv"]:
        matches = re.findall(rf'"{key}":"([^"]+)"', html)
        for m in matches:
            streams.append(m.replace("\\/", "/"))

    # ✅ 2. Regex trực tiếp m3u8 + flv (fallback)
    direct = re.findall(r'https?://[^"\']+\.(m3u8|flv)', html)
    for d in direct:
        if isinstance(d, tuple):
            continue

    direct_full = re.findall(r'https?://[^"\']+\.(?:m3u8|flv)', html)
    streams.extend(direct_full)

    # ❌ loại trùng
    return list(set(streams))


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


def process_hoadao_pro():
    matches = []

    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        links = set()

        # ✅ quét rộng để không miss
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if any(x in href for x in ["truc-tiep", "xem-bong-da", "live"]):
                url = href if href.startswith("http") else BASE_URL + href
                links.add(url)

        print(f"[HoaDao] Found {len(links)} pages")

        for url in links:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                html = r.text

                streams = extract_streams(html)
                if not streams:
                    continue

                best = pick_best(streams)
                if not best:
                    continue

                s = BeautifulSoup(html, "html.parser")

                title = "HoaDao TV"
                h1 = s.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

                matches.append({
                    "time": datetime.now(),
                    "group": "🔥 HOA ĐÀO PRO",
                    "title": title,
                    "logo": BASE_URL + "/favicon.ico",
                    "url": best
                })

                print("OK:", title)

            except Exception as e:
                print("Item lỗi:", e)
                continue

    except Exception as e:
        print("Lỗi hoadao:", e)

    return matches
