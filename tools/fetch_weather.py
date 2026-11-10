"""바람·날씨 받아 오기 → site/data/weather.json

기상청 단기예보(공공데이터포털 '기상청_단기예보 조회서비스')에서
물때 관측소 탭마다 그 동네 격자의 오늘·내일 시간별 예보(바람·하늘·기온·강수확률)를 받는다.

  실제 자료:  KHOA_SERVICE_KEY=발급키  python tools/fetch_weather.py
  예시 자료:  python tools/fetch_weather.py --sample   (키 없이 화면 확인용)

공공데이터포털 인증키는 계정에 하나라 물때와 같은 키(Secrets의 KHOA_SERVICE_KEY)를 쓴다.
단, 포털에서 이 서비스를 '활용신청'해 두어야 한다.
GitHub Actions(.github/workflows/weather.yml)가 3시간마다 돌린다. 표준 라이브러리만 쓴다.
"""
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
API = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
# 물때 탭과 같은 코드로 묶는다. 위치는 탭 이름의 장소(다리·방조제) 근처.
PLACES = [
    ("DT_0032", "강화대교", 37.731, 126.522),
    ("DT_0064", "교동대교", 37.770, 126.308),
    ("DT_0044", "영종대교", 37.545, 126.584),
    ("DT_0052", "시화방조제", 37.312, 126.620),
]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "weather.json")


# 경위도 → 기상청 격자(nx, ny). 기상청이 공개한 람베르트 정각원추도법 변환식.
def to_grid(lat, lon):
    RE, GRID, SLAT1, SLAT2, OLON, OLAT, XO, YO = 6371.00877, 5.0, 30.0, 60.0, 126.0, 38.0, 43, 136
    d = math.pi / 180.0
    re = RE / GRID
    s1, s2, olon, olat = SLAT1 * d, SLAT2 * d, OLON * d, OLAT * d
    sn = math.log(math.cos(s1) / math.cos(s2)) / math.log(math.tan(math.pi / 4 + s2 / 2) / math.tan(math.pi / 4 + s1 / 2))
    sf = math.tan(math.pi / 4 + s1 / 2) ** sn * math.cos(s1) / sn
    ro = re * sf / math.tan(math.pi / 4 + olat / 2) ** sn
    ra = re * sf / math.tan(math.pi / 4 + lat * d / 2) ** sn
    theta = lon * d - olon
    if theta > math.pi:
        theta -= 2 * math.pi
    if theta < -math.pi:
        theta += 2 * math.pi
    theta *= sn
    return int(ra * math.sin(theta) + XO + 0.5), int(ro - ra * math.cos(theta) + YO + 0.5)


# 발표 시각: 02·05·08·11·14·17·20·23시, 발표 후 10분쯤부터 받을 수 있다 → 15분 여유
def latest_base(now):
    t = now - timedelta(minutes=15)
    for h in (23, 20, 17, 14, 11, 8, 5, 2):
        if t.hour >= h:
            return t.strftime("%Y%m%d"), f"{h:02d}00"
    y = t - timedelta(days=1)
    return y.strftime("%Y%m%d"), "2300"


def fetch(key, nx, ny, base_date, base_time):
    q = urllib.parse.urlencode({"pageNo": "1", "numOfRows": "1000", "dataType": "JSON",
                                "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny})
    url = f"{API}?serviceKey={key if '%' in key else urllib.parse.quote(key, safe='')}&{q}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                raw = r.read().decode("utf-8")
            body = json.loads(raw)
            break
        except Exception as e:  # 일시 오류·XML 오류 응답은 두 번 더 시도
            if attempt == 2:
                raise RuntimeError(f"{nx},{ny}: {e}")
            time.sleep(3)
    res = body.get("response", {})
    head = res.get("header", {})
    if head.get("resultCode") != "00":
        raise RuntimeError(f"{nx},{ny}: {head.get('resultCode')} {head.get('resultMsg')}")
    items = ((res.get("body") or {}).get("items") or {}).get("item") or []
    hours = {}
    for it in items:
        k = (it["fcstDate"], it["fcstTime"][:2])
        hours.setdefault(k, {})[it["category"]] = it["fcstValue"]
    return hours


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pack(hours, days):
    out = []
    for (d, h), v in sorted(hours.items()):
        if d not in days or "WSD" not in v:
            continue
        out.append({"d": d, "h": h, "wsd": num(v.get("WSD")), "vec": num(v.get("VEC")),
                    "tmp": num(v.get("TMP")), "sky": int(num(v.get("SKY")) or 0), "pty": int(num(v.get("PTY")) or 0),
                    "pop": num(v.get("POP"))})
    return out


def sample_hours(days):
    rnd = random.Random(days[0])
    hours = {}
    for d in days:
        for h in range(24):
            w = 3 + 4 * math.sin((h - 6) / 24 * 2 * math.pi) ** 2 + rnd.random() * 2
            hours[(d, f"{h:02d}")] = {"WSD": round(w, 1), "VEC": 300 + rnd.randint(-30, 30),
                                     "TMP": round(8 + 6 * math.sin((h - 9) / 24 * 2 * math.pi)),
                                     "SKY": rnd.choice([1, 1, 3, 4]), "PTY": 0, "POP": rnd.choice([0, 10, 20, 30])}
    return hours


def main():
    sample = "--sample" in sys.argv
    key = os.environ.get("KHOA_SERVICE_KEY", "").strip()
    if not sample and not key:
        sys.exit("KHOA_SERVICE_KEY가 없습니다. 예시로 보려면 --sample 을 붙이세요.")
    now = datetime.now(KST)
    days = [now.strftime("%Y%m%d"), (now + timedelta(days=1)).strftime("%Y%m%d")]
    base_date, base_time = latest_base(now)
    data = {"generated": now.isoformat(timespec="minutes"), "sample": sample,
            "source": "기상청 단기예보", "base": f"{base_date} {base_time}", "places": {}}
    failed = 0
    for code, name, lat, lon in PLACES:
        nx, ny = to_grid(lat, lon)
        try:
            hours = sample_hours(days) if sample else fetch(key, nx, ny, base_date, base_time)
            data["places"][code] = {"name": name, "nx": nx, "ny": ny, "hours": pack(hours, days)}
        except RuntimeError as e:
            failed += 1
            print("실패:", name, e, file=sys.stderr)
        if not sample:
            time.sleep(0.3)
    if failed == len(PLACES):
        sys.exit("모두 실패해서 기존 파일을 그대로 둡니다.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장: {OUT} ({'예시' if sample else '실제'}, 발표 {base_date} {base_time}, 실패 {failed}곳)")


if __name__ == "__main__":
    main()
