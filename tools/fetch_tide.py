"""물때 자료 받아 오기 → site/data/tide.json

국립해양조사원 조석예보(고·저조) API (공공데이터포털)에서
강화대교·교동대교·영종대교·인천송도(시화방조제 탭) 관측소의 오늘부터 열흘치 만조/간조를 받아
홈페이지가 읽는 JSON 한 개로 저장한다.

  실제 자료:  KHOA_SERVICE_KEY=발급키  python tools/fetch_tide.py
  예시 자료:  python tools/fetch_tide.py --sample   (키 없이 화면 확인용)

GitHub Actions(.github/workflows/tide.yml)가 매일 새벽 이 스크립트를 돌린다.
인증키는 코드에 넣지 않고 GitHub 저장소의 Secrets(KHOA_SERVICE_KEY)에만 둔다.
표준 라이브러리만 쓴다(설치할 것 없음).
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
API = "https://apis.data.go.kr/1192136/tideFcstHghLw/GetTideFcstHghLwApiService"
STATIONS = [  # (관측소 코드, 탭 이름, 실제 관측소 이름) 순서대로 화면 탭에 나온다. 첫 번째가 기본.
    ("DT_0032", "강화대교", "강화대교"),
    ("DT_0064", "교동대교", "교동대교"),
    ("DT_0044", "영종대교", "영종대교"),
    ("DT_0052", "시화방조제", "인천송도"),  # 방조제 앞엔 관측소가 없어 가장 가까운 송도(약 4~5km) 기준
]
DAYS = 10
SUN_AT = (37.70, 126.45)  # 일출·일몰 계산 위치(강화도 가운데쯤)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tide.json")


# ── 음력 날짜와 물때 ──────────────────────────────────────────
# 합삭(새달) 시각을 천문 계산(Meeus)으로 구해, 합삭이 든 날(한국 시간)을 음력 1일로 친다.
def _new_moon_jde(k):
    T = k / 1236.85
    jde = 2451550.09766 + 29.530588861 * k + 0.00015437 * T * T
    M = math.radians((2.5534 + 29.10535670 * k) % 360)
    Mp = math.radians((201.5643 + 385.81693528 * k + 0.0107582 * T * T) % 360)
    F = math.radians((160.7108 + 390.67050284 * k - 0.0016118 * T * T) % 360)
    Om = math.radians((124.7746 - 1.56375588 * k + 0.0020672 * T * T) % 360)
    E = 1 - 0.002516 * T
    jde += (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M) + 0.01608 * math.sin(2 * Mp)
            + 0.01039 * math.sin(2 * F) + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M)
            + 0.00208 * E * E * math.sin(2 * M) - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F)
            + 0.00056 * E * math.sin(2 * Mp + M) - 0.00042 * math.sin(3 * Mp) + 0.00042 * E * math.sin(M + 2 * F)
            + 0.00038 * E * math.sin(M - 2 * F) - 0.00024 * E * math.sin(2 * Mp - M) - 0.00017 * math.sin(Om))
    return jde


def _jde_to_kst_date(jde):
    unix = (jde - 2440587.5) * 86400 - 69  # TT→UTC 대략 보정(69초)
    return datetime.fromtimestamp(unix, KST).date()


def lunar_day(d):
    k = math.floor((d.year + (d.timetuple().tm_yday - 1) / 365.25 - 2000) * 12.3685) + 1
    while _jde_to_kst_date(_new_moon_jde(k)) > d:
        k -= 1
    return (d - _jde_to_kst_date(_new_moon_jde(k))).days + 1


# 서해 7물때식: 음력 1·16일 = 7물(사리 무렵), 8·23일 = 조금, 9·24일 = 무시
def mulddae(lday):
    n = (lday - 1) % 15  # 0 → 7물
    names = ["7물", "8물", "9물", "10물", "11물", "12물", "13물", "조금", "무시",
             "1물", "2물", "3물", "4물", "5물", "6물"]
    return names[n]


# ── 일출·일몰 (NOAA 간이식, 분 단위면 충분) ─────────────────────
def sun_times(d, lat, lon):
    n = d.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                   - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(decl))
                                - math.tan(la) * math.tan(decl)))
    def fmt(utc_min):
        m = round(utc_min + 540) % 1440
        return f"{m // 60:02d}:{m % 60:02d}"
    return fmt(720 - 4 * (lon + ha) - eq), fmt(720 - 4 * (lon - ha) - eq)


# ── API 호출 ──────────────────────────────────────────────────
def fetch_day(key, code, d):
    q = urllib.parse.urlencode({"obsCode": code, "reqDate": d.strftime("%Y%m%d"),
                                "type": "json", "numOfRows": "20", "pageNo": "1"})
    # 공공데이터포털 키는 이미 인코딩된 형태로 받는 경우가 많아 그대로 붙인다
    url = f"{API}?serviceKey={key if '%' in key else urllib.parse.quote(key, safe='')}&{q}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                body = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:  # 일시 오류는 두 번 더 시도
            if attempt == 2:
                raise RuntimeError(f"{code} {d}: {e}")
            time.sleep(2)
    head = body.get("header") or body.get("response", {}).get("header") or {}
    if head.get("resultCode") not in (None, "00"):
        raise RuntimeError(f"{code} {d}: {head.get('resultCode')} {head.get('resultMsg')}")
    b = body.get("body") or body.get("response", {}).get("body") or {}
    items = (b.get("items") or {}).get("item") or []
    if isinstance(items, dict):
        items = [items]
    out = []
    for it in items:
        dt = str(it.get("predcDt", ""))  # "YYYY-MM-DD HH:MM"
        if not dt.startswith(d.isoformat()):
            continue
        try:
            level = round(float(it.get("predcTdlvVl")))
        except (TypeError, ValueError):
            level = None
        out.append({"t": "H" if str(it.get("extrSe")) in ("1", "3") else "L", "time": dt[11:16], "level": level})
    return sorted(out, key=lambda x: x["time"])


# ── 키 없이 화면 확인용 예시(진짜 물때 아님) ────────────────────
def sample_day(code, d):
    shift = {"DT_0032": 70, "DT_0064": 40, "DT_0044": 10, "DT_0052": 15}.get(code, 0)
    lday = lunar_day(d)
    amp = 0.6 + 0.4 * math.cos(2 * math.pi * (lday - 2) / 14.77)  # 사리에 크고 조금에 작게
    first = (lday * 50 + 180 + shift) % 745
    out, m = [], first
    while m < 1440:
        for kind in ("H", "L"):
            if m < 1440:
                lvl = 450 + (330 if kind == "H" else -330) * amp
                out.append({"t": kind, "time": f"{int(m) // 60:02d}:{int(m) % 60:02d}", "level": round(lvl)})
            m += 372.5
    return out


def main():
    sample = "--sample" in sys.argv
    key = os.environ.get("KHOA_SERVICE_KEY", "").strip()
    if not sample and not key:
        sys.exit("KHOA_SERVICE_KEY가 없습니다. 예시로 보려면 --sample 을 붙이세요.")
    today = datetime.now(KST).date()
    dates = [today - timedelta(days=1) + timedelta(days=i) for i in range(DAYS + 1)]  # 어제부터(자정 넘긴 곡선용)
    data = {"generated": datetime.now(KST).isoformat(timespec="minutes"), "sample": sample,
            "source": "국립해양조사원 조석예보", "days": {}, "stations": []}
    for d in dates:
        ld = lunar_day(d)
        rise, set_ = sun_times(d, *SUN_AT)
        data["days"][d.strftime("%Y%m%d")] = {"lunar": ld, "mul": mulddae(ld), "sunrise": rise, "sunset": set_}
    failed = 0
    for code, name, obs in STATIONS:
        st = {"code": code, "name": name, "obs": obs, "ext": {}}
        for d in dates:
            try:
                st["ext"][d.strftime("%Y%m%d")] = sample_day(code, d) if sample else fetch_day(key, code, d)
            except RuntimeError as e:
                failed += 1
                print("실패:", e, file=sys.stderr)
            if not sample:
                time.sleep(0.2)
        data["stations"].append(st)
    if not sample and failed == len(STATIONS) * len(dates):
        sys.exit("모두 실패해서 기존 파일을 그대로 둡니다.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장: {OUT} ({'예시' if sample else '실제'}, 실패 {failed}건)")


if __name__ == "__main__":
    main()
