# 임시 확인용(공개 전에 지움): 새 관측소·격자가 실제 자료를 주는지 data/_check.txt에 적는다.
import os, sys, json, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(__file__))
import fetch_tide as T, fetch_weather as W
key = os.environ["KHOA_SERVICE_KEY"].strip()
KST = timezone(timedelta(hours=9)); today = datetime.now(KST).date()
out = []
for code in ["DT_0067", "DT_0025", "DT_0032"]:
    try:
        q = urllib.parse.urlencode({"obsCode": code, "reqDate": today.strftime("%Y%m%d"), "type": "json", "numOfRows": "20", "pageNo": "1"})
        url = f"{T.API}?serviceKey={key if '%' in key else urllib.parse.quote(key, safe='')}&{q}"
        body = json.loads(urllib.request.urlopen(url, timeout=20).read().decode())
        b = body.get("body") or body.get("response", {}).get("body") or {}
        items = (b.get("items") or {}).get("item") or []
        if isinstance(items, dict): items = [items]
        first = {k: v for k, v in (items[0] if items else {}).items() if k != "serviceKey"}
        out.append(f"{code}: {len(items)}건 {json.dumps(first, ensure_ascii=False)}")
        out.append(f"  {code} 파싱: {T.fetch_day(key, code, today)}")
    except Exception as e:
        out.append(f"{code}: 오류 {e}")
now = datetime.now(KST) - timedelta(minutes=15)
bt = max([h for h in (2, 5, 8, 11, 14, 17, 20, 23) if h <= now.hour] or [23])
bd = now if now.hour >= 2 else now - timedelta(days=1)
for name, la, lo in [("태안", 36.745, 126.298), ("안면도", 36.510, 126.352)]:
    nx, ny = W.to_grid(la, lo)
    try:
        hours = W.fetch(key, nx, ny, bd.strftime("%Y%m%d"), f"{bt:02d}00")
        out.append(f"{name} ({nx},{ny}): {len(hours)}개 시간, 첫 값 {json.dumps(hours[0] if isinstance(hours, list) else str(hours)[:200], ensure_ascii=False)[:200]}")
    except Exception as e:
        out.append(f"{name} ({nx},{ny}): 오류 {e}")
os.makedirs("data", exist_ok=True)
open("data/_check.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
