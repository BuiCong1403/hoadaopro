import requests
import re
from bs4 import BeautifulSoup

BASE_URL = "https://hoadaotv.info"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": BASE_URL
}


def fetch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        return res.text
    except:
        return ""


def get_match_data():
    matches = []

    html = fetch(BASE_URL)
    if not html:
        print("❌ Không load được trang chủ")
        return matches

    soup = BeautifulSoup(html, "html.parser")

    links = []

    # ✅ lấy link trận (giống coder kia - QUAN TRỌNG)
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/truc-tiep/" in href or "xem-bong-da" in href:
            url = href if href.startswith("http") else BASE_URL + href
            if url not in links:
                links.append(url)

    print(f"🔎 Found {len(links)} match pages")

    # ✅ vào từng trận để lấy flv
    for url in links:
        try:
            html = fetch(url)
            if not html:
                continue

            # 🔥 KEY QUAN TRỌNG: lấy đúng flv trong JS
            flv_match = re.search(r'"flv":"([^"]+)"', html)

            if not flv_match:
                continue

            stream_url = flv_match.group(1).replace("\\/", "/")

            soup_detail = BeautifulSoup(html, "html.parser")

            title = "HoaDao TV"
            h1 = soup_detail.find("h1")
            if h1:
                title = h1.get_text(strip=True)

            matches.append({
                "title": title,
                "logo": BASE_URL + "/favicon.ico",
                "url": stream_url
            })

            print("✅ OK:", title)

        except Exception as e:
            print("❌ lỗi:", e)
            continue

    print(f"📊 Tổng kênh: {len(matches)}")
    return matches


def fallback():
    print("⚠️ dùng fallback")
    return [{
        "title": "Test Channel",
        "logo": "",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    }]


def write_m3u(data):
    content = "#EXTM3U\n"

    for m in data:
        content += f'#EXTINF:-1 tvg-logo="{m["logo"]}",{m["title"]}\n'
        content += f'#EXTVLCOPT:http-referrer={BASE_URL}/\n'
        content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
        content += f'{m["url"]}\n\n'

    with open("hoadaopro.m3u", "w", encoding="utf-8") as f:
        f.write(content)

    print("📺 Đã ghi file hoadaopro.m3u")


if __name__ == "__main__":
    data = get_match_data()

    # ❗ chống rỗng
    if not data:
        data = fallback()

    write_m3u(data)

    print("✅ DONE")
