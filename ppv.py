import asyncio
from playwright.async_api import async_playwright
import aiohttp
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
import html

# --- 🎨 VISUALS ---
class Col:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

def print_banner():
    print(f"\n{Col.CYAN}{'='*60}{Col.RESET}")
    print(f"🚀  {Col.BOLD}PPV.TO LIVE INTERCEPTOR (REAL LIVE NOW){Col.RESET}")
    print(f"{Col.CYAN}{'='*60}{Col.RESET}\n")

# --- CONFIG ---
API_URL = "https://api.ppv.to/api/streams"
PLAYLIST_FILE = "PPVLand.m3u8"

STREAM_HEADERS = [
    '#EXTVLCOPT:http-referrer=https://ppv.to/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
]

BACKUP_LOGOS = {
    "24/7 Streams": "http://drewlive2423.duckdns.org:9000/Logos/247.png",
    "Wrestling": "http://drewlive2423.duckdns.org:9000/Logos/Wrestling.png",
    "Football": "http://drewlive2423.duckdns.org:9000/Logos/Football.png",
    "Basketball": "http://drewlive2423.duckdns.org:9000/Logos/Basketball.png",
    "Baseball": "http://drewlive2423.duckdns.org:9000/Logos/Baseball.png",
    "American Football": "http://drewlive2423.duckdns.org:9000/Logos/NFL3.png",
    "Combat Sports": "http://drewlive2423.duckdns.org:9000/Logos/CombatSports2.png",
    "Darts": "http://drewlive2423.duckdns.org:9000/Logos/Darts.png",
    "Motorsports": "http://drewlive2423.duckdns.org:9000/Logos/Motorsports2.png",
    "Live Now": "http://drewlive2423.duckdns.org:9000/Logos/DrewLiveSports.png",
    "Ice Hockey": "http://drewlive2423.duckdns.org:9000/Logos/Hockey.png",
    "Cricket": "http://drewlive2423.duckdns.org:9000/Logos/Cricket.png",
}

GROUP_RENAME_MAP = {
    "24/7 Streams": "PPVLand - Live Channels 24/7",
    "Wrestling": "PPVLand - Wrestling Events",
    "Football": "PPVLand - Global Football Streams",
    "Basketball": "PPVLand - Basketball Hub",
    "Baseball": "PPVLand - MLB",
    "American Football": "PPVLand - NFL Action",
    "Combat Sports": "PPVLand - Combat Sports",
    "Darts": "PPVLand - Darts",
    "Motorsports": "PPVLand - Racing Action",
    "Live Now": "PPVLand - Live Now",
    "Ice Hockey": "PPVLand - NHL Action",
    "Cricket": "PPVLand - Cricket"
}

ICONS = {
    "American Football": "🏈", "Basketball": "🏀", "Ice Hockey": "🏒",
    "Baseball": "⚾", "Combat Sports": "🥊", "Wrestling": "🤼",
    "Football": "⚽", "Motorsports": "🏎️", "Darts": "🎯",
    "Live Now": "📡", "24/7 Streams": "📺", "default": "📺"
}

def get_icon(name):
    return ICONS.get(name, ICONS["default"])

def get_display_time(timestamp):
    if not timestamp or timestamp <= 0:
        return ""
    try:
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        dt_mt  = dt_utc.astimezone(ZoneInfo("America/Denver"))
        dt_uk  = dt_utc.astimezone(ZoneInfo("Europe/London"))
        return f"{dt_est.strftime('%I:%M %p ET')} / {dt_mt.strftime('%I:%M %p MT')} / {dt_uk.strftime('%H:%M UK')}"
    except:
        return ""

# SCRAPING HELPERS
async def safe_grab(page, iframe_url, timeout=8):
    try:
        return await asyncio.wait_for(grab_m3u8_from_iframe(page, iframe_url), timeout=timeout)
    except asyncio.TimeoutError:
        return set()

async def grab_m3u8_from_iframe(page, iframe_url):
    first_url = None

    await page.route("**/*", lambda route: (
        route.abort() if route.request.resource_type in ["image","stylesheet","font","media"]
        else route.continue_()
    ))

    def handle_response(response):
        nonlocal first_url
        if ".m3u8" in response.url and first_url is None:
            first_url = response.url

    page.on("response", handle_response)

    try:
        await page.goto(iframe_url, timeout=6000, wait_until="domcontentloaded")
    except:
        pass

    for _ in range(120):
        if first_url:
            break
        await asyncio.sleep(0.05)

    return {first_url} if first_url else set()

async def get_streams():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            resp = await session.get(API_URL, timeout=30)
            if resp.status != 200:
                print(f"{Col.RED}❌ API Error {resp.status}{Col.RESET}")
                return []
            data = await resp.json()
            return data.get("streams", [])
    except Exception as e:
        print(f"{Col.RED}❌ API Fetch Error: {e}{Col.RESET}")
        return []

# MAIN
async def main():
    start_time = time.time()
    print_banner()

    categories = await get_streams()
    if not categories:
        print(f"{Col.RED}❌ No categories received{Col.RESET}")
        return

    now_ts = int(time.time())
    streams = []

    # flatten
    for cat_obj in categories:
        original_cat = cat_obj.get("category", "")
        cat_always_live = cat_obj.get("always_live") == 1

        for s in cat_obj.get("streams", []):
            starts_at = s.get("starts_at", 0)
            is_live_event = (starts_at > 0 and starts_at <= now_ts)
            stream_always_live = s.get("always_live") == 1

            final_category = original_cat
            if not cat_always_live and not stream_always_live and is_live_event:
                final_category = "Live Now"

            if s.get("iframe"):
                streams.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "iframe": s.get("iframe"),
                    "category": final_category,
                    "poster": s.get("poster"),
                    "starts_at": starts_at,
                    "ends_at": s.get("ends_at"),
                    "clock_time": get_display_time(starts_at)
                })

    streams.sort(key=lambda x: x["starts_at"] or 0)
    valid_streams = []

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        total = len(streams)

        for idx, s in enumerate(streams, start=1):
            page = await browser.new_page()

            icon = get_icon(s["category"])
            print(f"[{idx}/{total}] {Col.YELLOW}Scanning:{Col.RESET} {icon} {s['name']} [{s['category']}]")

            urls = await safe_grab(page, s["iframe"])
            await page.close()

            if urls:
                found = next(iter(urls))
                print(f"   {Col.GREEN}⚡ FOUND:{Col.RESET} {found}")

                final_logo = s.get("poster") or BACKUP_LOGOS.get(s["category"], "")

                valid_streams.append({
                    "id": s["id"],
                    "name": s["name"],
                    "category": s["category"],
                    "poster": final_logo,
                    "starts_at": s["starts_at"],
                    "ends_at": s["ends_at"],
                    "url": found,
                    "time": s["clock_time"]
                })
            else:
                print(f"   {Col.DIM}❌ Signal Lost{Col.RESET}")

        await browser.close()

    # SAVE PLAYLIST
    print(f"\n{Col.YELLOW}💾 Saving playlist to {PLAYLIST_FILE}...{Col.RESET}")
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in valid_streams:
            tvg_id = f"ppv-{item['id']}"
            group_title = GROUP_RENAME_MAP.get(item["category"], item["category"])

            clean_title = item["name"]
            if item["time"]:
                clean_title += f" - {item['time']}"

            f.write(
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{item["name"]}" '
                f'tvg-logo="{item["poster"]}" group-title="{group_title}",{clean_title}\n'
            )

            for h in STREAM_HEADERS:
                f.write(h + "\n")

            f.write(item["url"] + "\n")

    print(f"\n{Col.CYAN}{'='*60}{Col.RESET}")
    print(f"✅ {Col.BOLD}MISSION COMPLETE{Col.RESET}")
    print(f"📊 {Col.BOLD}WORKING STREAMS:{Col.RESET} {len(valid_streams)} / {total}")
    print(f"⏱️ {Col.BOLD}TIME:{Col.RESET} {time.time()-start_time:.2f}s")
    print(f"📺 Playlist: {PLAYLIST_FILE}")
    print(f"{Col.CYAN}{'='*60}{Col.RESET}")


if __name__ == "__main__":
    asyncio.run(main())