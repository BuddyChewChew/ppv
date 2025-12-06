import html
import aiohttp
import asyncio
import gzip
from datetime import datetime, timezone

API_URL = "https://ppv.to/api/streams"

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def to_xml_date(timestamp):
    """Convert Unix timestamp to XMLTV format."""
    if not timestamp:
        return ""
    dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S +0000")

def escape_xml(text):
    """Escape XML-friendly text."""
    if not text:
        return ""
    return html.escape(str(text))


# ---------------------------------------------------------
# Fetch streams directly from PPV.to API
# ---------------------------------------------------------
async def get_streams():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://ppvs.su",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(API_URL, timeout=20) as resp:
                if resp.status != 200:
                    print("❌ API error:", resp.status)
                    return []
                data = await resp.json()
                return data.get("streams", [])
    except Exception as e:
        print("❌ Error fetching streams:", e)
        return []


# ---------------------------------------------------------
# Build XML EPG
# ---------------------------------------------------------
def build_epg(flat_streams):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tv>'
    ]

    used_ids = set()

    for s in flat_streams:
        sid = s["id"]
        if sid in used_ids:
            continue
        used_ids.add(sid)

        channel_id = f"ppv-{sid}"
        name = escape_xml(s["name"])
        category = escape_xml(s.get("category", ""))

        xml.append(f'  <channel id="{channel_id}">')
        xml.append(f'    <display-name>{name}</display-name>')
        xml.append(f'  </channel>')

        start_ts = s.get("starts_at")
        end_ts   = s.get("ends_at")

        start = to_xml_date(start_ts)

        # Fallback: +3 hours
        if not end_ts and start_ts:
            end_ts = start_ts + (3 * 3600)

        end = to_xml_date(end_ts)

        poster = escape_xml(s.get("poster", ""))

        if start and end:
            xml.append(f'  <programme start="{start}" stop="{end}" channel="{channel_id}">')
            xml.append(f'    <title lang="en">{name}</title>')
            xml.append(f'    <sub-title>{category}</sub-title>')
            xml.append(f'    <category>{category}</category>')
            if poster:
                xml.append(f'    <icon src="{poster}" />')
            xml.append(f'  </programme>')

    xml.append('</tv>')
    return "\n".join(xml)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
async def main():
    print("🚀 Fetching PPV events…")

    categories = await get_streams()
    flat = []

    # Flatten each category into one list
    for cat in categories:
        cat_name = cat.get("category", "")
        for s in cat.get("streams", []):
            flat.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "category": cat_name,
                "poster": s.get("poster"),
                "starts_at": s.get("starts_at"),
                "ends_at": s.get("ends_at"),
            })

    if not flat:
        print("❌ No streams found.")
        return

    print(f"📡 Building EPG for {len(flat)} events…")

    epg_xml = build_epg(flat)

    # WRITE .xml.gz
    with gzip.open("PPVLand.xml.gz", "wb") as f:
        f.write(epg_xml.encode("utf-8"))

    print("✅ EPG saved as PPVLand.xml.gz")


if __name__ == "__main__":
    asyncio.run(main())