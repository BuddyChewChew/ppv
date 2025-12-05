import asyncio
from playwright.async_api import async_playwright
import aiohttp
from datetime import datetime, timezone
import html

API_URL = "https://ppv.to/api/streams"

CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://ppvs.su',
    '#EXTVLCOPT:http-referrer=https://ppvs.su',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'
]

ALLOWED_CATEGORIES = {
    "24/7 Streams", "Wrestling", "Football", "Basketball", "Baseball",
    "Combat Sports", "Motorsports", "Miscellaneous", "Boxing", "Darts",
    "American Football", "Ice Hockey", "Cricket"
}

CATEGORY_LOGOS = {
    "24/7 Streams": "https://github.com/PaauullI/ppv/blob/main/assets/24-7.png?raw=true",
    "Wrestling": "https://github.com/PaauullI/ppv/blob/main/assets/wwe.png?raw=true",
    "Football": "https://github.com/PaauullI/ppv/blob/main/assets/football.png?raw=true",
    "Basketball": "https://github.com/PaauullI/ppv/blob/main/assets/nba.png?raw=true",
    "Baseball": "https://github.com/PaauullI/ppv/blob/main/assets/baseball.png?raw=true",
    "Combat Sports": "https://github.com/PaauullI/ppv/blob/main/assets/mma.png?raw=true",
    "Motorsports": "https://github.com/PaauullI/ppv/blob/main/assets/f1.png?raw=true",
    "Miscellaneous": "https://github.com/PaauullI/ppv/blob/main/assets/24-7.png?raw=true",
    "Boxing": "https://github.com/PaauullI/ppv/blob/main/assets/boxing.png?raw=true",
    "Darts": "https://github.com/PaauullI/ppv/blob/main/assets/darts.png?raw=true",
    "Ice Hockey": "https://github.com/PaauullI/ppv/blob/main/assets/hockey.png?raw=true",
    "American Football": "https://github.com/PaauullI/ppv/blob/main/assets/nfl.png?raw=true",
    "Cricket": "https://github.com/PaauullI/ppv/blob/main/assets/cricket.png?raw=true"
}

GROUP_RENAME_MAP = {
    "24/7 Streams": "PPVLand - Live Channels 24/7",
    "Wrestling": "PPVLand - Wrestling Events",
    "Football": "PPVLand - Global Football Streams",
    "Basketball": "PPVLand - Basketball Hub",
    "Baseball": "PPVLand - Baseball Action HD",
    "Combat Sports": "PPVLand - MMA & Fight Nights",
    "Motorsports": "PPVLand - Motorsport Live",
    "Miscellaneous": "PPVLand - Random Events",
    "Boxing": "PPVLand - Boxing",
    "Ice Hockey": "PPVLand - Ice Hockey",
    "Darts": "PPVLand - Darts",
    "American Football": "PPVLand - NFL Action",
    "Cricket": "PPVLand - Cricket"
}

URI_LEAGUE_MAP = {
    "epl": "🇬🇧 Premier League",
    "laliga": "🇪🇸 La Liga",
    "bundesliga": "🇩🇪 Bundesliga",
    "serie-a": "🇮🇹 Serie A",
    "ligue-1": "🇫🇷 Ligue 1",
    "ucl": "🇪🇺 UEFA Champions League",
    "uel": "🇪🇺 UEFA Europa League",
    "uefa-conference-league": "🇪🇺 UEFA Conference League",
    "eredivisie": "🇳🇱 Eredivisie",
    "mls": "🇺🇸 MLS",
    "fa-cup": "🇬🇧 FA Cup",
    "nfl": "🏈 NFL",
    "nba": "🏀 NBA",
    "nhl": "🏒 NHL",
    "mlb": "⚾ MLB",
    "cfb": "🏈 NCAA College Football",
    "wnba": "🏀 WNBA",
    "f1": "🏎️ Formula 1",
    "formula-1": "🏎️ Formula 1",
    "motogp": "🏍️ MotoGP",
    "nascar": "🏁 NASCAR",
    "ufc": "🥊 UFC",
    "boxing": "🥊 Boxing",
    "wwe": "🤼 WWE",
    "aew": "🤼 AEW",
    "darts": "🎯 Darts",
    "snooker": "🎱 Snooker",
    "tennis": "🎾 Tennis",
    "rugby": "🏉 Rugby",
    "cricket": "🏏 Cricket"
}

def to_xml_date(timestamp):
    """Convert Unix-Timestamp to XMLTV (YYYYMMDDhhmmss +0000)"""
    if not timestamp:
        return ""
    dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S +0000")

def escape_xml(text):
    if not text: 
        return ""
    return html.escape(str(text))

# --- Core Logic ---

async def check_m3u8_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://ppvs.su",
            "Origin": "https://ppvs.su"
        }
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                return resp.status == 200
    except Exception as e:
        print(f"❌ Error checking {url}: {e}")
        return False

async def get_streams():
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            print(f"🌐 Fetching streams from {API_URL}")
            async with session.get(API_URL) as resp:
                print(f"🔍 Response status: {resp.status}")
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as e:
        print(f"❌ Error in get_streams: {str(e)}")
        return None

async def grab_m3u8_from_iframe(page, iframe_url):
    found_streams = set()

    def handle_response(response):
        if ".m3u8" in response.url:
            found_streams.add(response.url)

    page.on("response", handle_response)
    print(f"🌐 Navigating to iframe: {iframe_url}")

    try:
        await page.goto(iframe_url, timeout=30000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"❌ Failed to load iframe: {e}")
        page.remove_listener("response", handle_response)
        return set()

    await asyncio.sleep(2)

    try:
        box = page.viewport_size or {"width": 1280, "height": 720}
        cx, cy = box["width"] / 2, box["height"] / 2
        for i in range(4):
            if found_streams:
                break
            print(f"🖱️ Click #{i + 1}")
            try:
                await page.mouse.click(cx, cy)
            except Exception:
                pass
            await asyncio.sleep(0.3)
    except Exception as e:
        print(f"❌ Mouse click error: {e}")

    print("⏳ Waiting 5s for final stream load...")
    await asyncio.sleep(5)
    page.remove_listener("response", handle_response)

    valid_urls = set()
    for url in found_streams:
        if await check_m3u8_url(url):
            valid_urls.add(url)
        else:
            print(f"❌ Invalid or unreachable URL: {url}")
    return valid_urls

def get_group_title(stream):
    orig_category = stream["category"].strip()
    uri_name = stream.get("uri_name", "").lower()
    
    uri_parts = uri_name.split('/')
    if uri_parts and uri_parts[0]:
        league_key = uri_parts[0]
        if league_key in URI_LEAGUE_MAP:
            return URI_LEAGUE_MAP[league_key]
        
        if orig_category in ["Football", "Basketball", "American Football", "Ice Hockey", "Baseball", "Motorsports", "Combat Sports"]:
             return league_key.replace("-", " ").upper()

    return GROUP_RENAME_MAP.get(orig_category, orig_category)

def build_m3u(streams, url_map):
    lines = ['#EXTM3U url-tvg="PPVLand.xml"']
    
    seen_ids = set()

    for s in streams:
        unique_key = f"{s['name']}::{s['category']}::{s['iframe']}"
        urls = url_map.get(unique_key, [])

        if not urls:
            continue
        
        if s['id'] in seen_ids:
            continue
        seen_ids.add(s['id'])

        final_group = get_group_title(s)
        orig_category = s["category"].strip()
        
        api_poster = s.get("poster")
        logo = api_poster.strip() if api_poster and api_poster.strip() else CATEGORY_LOGOS.get(orig_category, "")
        
        tvg_id = f"ppv-{s['id']}"

        url = next(iter(urls))
        
        title = s["name"]
        
        lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{title}" tvg-logo="{logo}" group-title="{final_group}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)

    return "\n".join(lines)

def build_epg(streams, url_map):
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
      
    processed_ids = set()

    for s in streams:
        unique_key = f"{s['name']}::{s['category']}::{s['iframe']}"
        if unique_key not in url_map or not url_map[unique_key]:
            continue

        if s['id'] in processed_ids:
            continue
        processed_ids.add(s['id'])

        channel_id = f"ppv-{s['id']}"
        display_name = escape_xml(s['name'])
        
        xml_lines.append(f'  <channel id="{channel_id}">')
        xml_lines.append(f'    <display-name>{display_name}</display-name>')
        xml_lines.append(f'  </channel>')

        start_time = to_xml_date(s.get('starts_at'))
        end_time = to_xml_date(s.get('ends_at'))
        
        # Fallback
        if not end_time and s.get('starts_at'):
             end_time = to_xml_date(s.get('starts_at') + (3 * 3600))

        poster = escape_xml(s.get('poster', ''))
        category = escape_xml(s.get('category', ''))
        
        if start_time and end_time:
            xml_lines.append(f'  <programme start="{start_time}" stop="{end_time}" channel="{channel_id}">')
            xml_lines.append(f'    <title lang="en">{display_name}</title>')
            xml_lines.append(f'    <sub-title>{category}</sub-title>')
            xml_lines.append(f'    <category>{category}</category>')
            if poster:
                xml_lines.append(f'    <icon src="{poster}" />')
            xml_lines.append(f'  </programme>')

    xml_lines.append('</tv>')
    return "\n".join(xml_lines)

async def main():
    print("🚀 Starting PPV Stream Fetcher")
    data = await get_streams()
    
    if not data or 'streams' not in data:
        print("❌ No valid data received from the API")
        return
        
    print(f"✅ Found {len(data['streams'])} categories")
    streams = []

    for category in data.get("streams", []):
        cat = category.get("category", "").strip()
        if cat not in ALLOWED_CATEGORIES:
            continue
        for stream in category.get("streams", []):
            iframe = stream.get("iframe")
            if iframe:
                streams.append({
                    "id": stream.get("id"),
                    "name": stream.get("name", "Unnamed Event"), 
                    "iframe": iframe, 
                    "category": cat, 
                    "poster": stream.get("poster"),
                    "uri_name": stream.get("uri_name"),
                    "starts_at": stream.get("starts_at"),
                    "ends_at": stream.get("ends_at"),
                    "description": stream.get("description", "")
                })

    # Deduping Logic
    seen_names = set()
    deduped_streams = []
    for s in streams:
        name_key = s["name"].strip().lower()
        if name_key not in seen_names:
            seen_names.add(name_key)
            deduped_streams.append(s)
    streams = deduped_streams

    if not streams:
        print("🚫 No valid streams found.")
        return
    
    print(f"🔍 Found {len(streams)} unique streams from {len({s['category'] for s in streams})} categories")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        url_map = {}
        for s in streams:
            key = f"{s['name']}::{s['category']}::{s['iframe']}"
            print(f"\n🔍 Scraping: {s['name']} ({s['category']})")
            urls = await grab_m3u8_from_iframe(page, s["iframe"])
            if urls:
                print(f"✅ Got {len(urls)} stream(s)")
            url_map[key] = urls

        await browser.close()

    print("\n💾 Writing playlist and EPG...")
    
    playlist = build_m3u(streams, url_map)
    with open("PPVLand.m3u8", "w", encoding="utf-8") as f:
        f.write(playlist)
        
    epg_xml = build_epg(streams, url_map)
    with open("PPVLand.xml", "w", encoding="utf-8") as f:
        f.write(epg_xml)

    print(f"✅ Done! Saved M3U8 and XML at {datetime.now(timezone.utc).isoformat()} UTC")

if __name__ == "__main__":
    asyncio.run(main())
