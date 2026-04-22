import requests
import re
from bs4 import BeautifulSoup

# ===== CONFIG =====
BASE_URL = "https://hoadaotv.info"
BACKUP_M3U = "https://raw.githubusercontent.com/nhanb2004798/watchfbfree/refs/heads/main/watchfrhd.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL
}


# ===== FETCH =====
def fetch(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        return res.text
    except:
        return ""


# ===== HOADAO (FLV CHUẨN) =====
def get_hoadao():
    data = []

    html = fetch(BASE_URL)
    if not html:
        return data

    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/truc-tiep/" in href or "xem-bong-da" in href:
            url = href if href.startswith("http") else BASE_URL + href
            if url not in links:
                links.append(url)

    print(f"[HoaDao] {len(links)} pages")

    for url in links:
        try:
            html = fetch(url)
            if not html:
                continue

            # lấy FLV (chuẩn nhất)
            flv = re.search(r'"flv":"([^"]+)"', html)
            hls = re.search(r'"hd":"([^"]+)"', html)

            stream = None
            if hls:
                stream = hls.group(1).replace("\\/", "/")
            elif flv:
                stream = flv.group(1).replace("\\/", "/")

            if not stream:
                continue

            title = "HoaDao TV"
            s = BeautifulSoup(html, "html.parser")
            h1 = s.find("h1")
            if h1:
                title = h1.get_text(strip=True)

            data.append({
                "title": title,
                "logo": BASE_URL + "/favicon.ico",
                "url": stream
            })

            print("✅ HoaDao:", title)

        except:
            continue

    return data


# ===== BACKUP M3U =====
def get_backup():
    data = []

    text = fetch(BACKUP_M3U)
    if not text:
        return data

    title = "Channel"
    logo = ""

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("#EXTINF"):
            parts = line.split(",", 1)
            title = parts[1] if len(parts) > 1 else "Channel"

            m = re.search(r'tvg-logo="([^"]+)"', line)
            logo = m.group(1) if m else ""

        elif line.startswith("http"):
            url = line

            if any(x in url for x in ["udp://", "rtp://"]):
                continue

            data.append({
                "title": title,
                "logo": logo,
                "url": url
            })

    print(f"[Backup] {len(data)} channels")
    return data


# ===== CLEAN =====
def clean(data):
    seen = set()
    out = []

    for item in data:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        out.append(item)

    return out


# ===== SORT =====
def sort_data(data):
    return sorted(data, key=lambda x: (
        ".m3u8" not in x["url"],
        ".flv" not in x["url"]
    ))


# ===== WRITE =====
def write(data):
    content = "#EXTM3U\n"

    for item in data:
        content += f'#EXTINF:-1 tvg-logo="{item["logo"]}",{item["title"]}\n'
        content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
        content += f'{item["url"]}\n\n'

    with open("hoadaopro.m3u", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📺 DONE: {len(data)} channels")


# ===== MAIN =====
if __name__ == "__main__":
    hoadao = get_hoadao()
    backup = get_backup()

    all_data = hoadao + backup

    if not all_data:
        print("❌ NO DATA → dùng fallback cứng")
        all_data = [{
            "title": "Test Channel",
            "logo": "",
            "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        }]

    all_data = clean(all_data)
    all_data = sort_data(all_data)

    write(all_data)
