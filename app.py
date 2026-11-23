# -*- coding: utf-8 -*-
"""
금산군 농어촌·공공형 버스 & 대전 외곽버스 34번 심플 시간표 안내 앱
- 단일 화면 · 모바일 큰 버튼 최적화 · 거짓 실시간/정체 시뮬레이션 전면 제거
- 데이터 기준:
  1) 금산군 농어촌·공공형 버스 공식 시간표 (2026. 7. 1. 시행)
  2) 대전광역시 외곽버스 34번 공식 시간표 및 정류장 (2026. 2. 26. 기준, 서남부터미널 ↔ 복수 ↔ 진산 ↔ 대둔산휴게소)
"""

import html
import json
import math
import os
from urllib.parse import quote, unquote, urlencode
from urllib.request import Request, urlopen
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="금산 붕붕이",
    page_icon="🚌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 브라우저 새로고침 시 처음 마운트되는 시작 화면.
# 같은 렌더 위치를 유지해 일반 위젯 조작 때 애니메이션을 다시 시작하지 않습니다.
splash_html = '<style>\n  .bb-splash { position:fixed; inset:0; z-index:999999; display:grid; place-items:center;\n    background:#eff6ff; color:#0f2851; text-align:center; pointer-events:none;\n    animation:bb-dismiss .3s ease 1.3s both; }\n  .bb-splash-badge { width:92px; height:92px; margin:0 auto 18px; border-radius:26px;\n    background:#1d4ed8; display:grid; place-items:center; }\n  .bb-splash-title { font:900 33px/1.2 system-ui,sans-serif; letter-spacing:-.06em; }\n  .bb-splash-sub { margin-top:8px; font:600 14px/1.5 system-ui,sans-serif; color:#42597a; }\n  @keyframes bb-dismiss { from { opacity:1; visibility:visible; } to { opacity:0; visibility:hidden; } }\n  @media (prefers-reduced-motion:reduce) { .bb-splash { animation-duration:.01s; } }\n</style>\n<div class="bb-splash" aria-hidden="true"><div>\n  <div class="bb-splash-badge"><svg width="56" height="56" viewBox="0 0 56 56" fill="none">\n    <rect x="9" y="6" width="38" height="42" rx="10" fill="#fff"/>\n    <rect x="14" y="13" width="28" height="16" rx="4" fill="#bfdbfe"/>\n    <path d="M28 13v16" stroke="#fff" stroke-width="2"/>\n    <circle cx="18" cy="37" r="3" fill="#1d4ed8"/><circle cx="38" cy="37" r="3" fill="#1d4ed8"/>\n    <path d="M16 46v5m24-5v5" stroke="#fff" stroke-width="5" stroke-linecap="round"/>\n  </svg></div>\n  <div class="bb-splash-title">금산 붕붕이</div>\n  <div class="bb-splash-sub">우리 동네 버스, 한눈에</div>\n</div></div>'
if hasattr(st, "html"):
    st.html(splash_html)
else:
    st.markdown(splash_html, unsafe_allow_html=True)



GEUMSAN_TAGO_ROUTES: dict[str, list[str]] = json.loads(r'''{"15": ["CNB292000006"], "68": ["CNB292000097"], "73": ["CNB292000104", "CNB292000105"], "73-1": ["CNB292000105"], "77": ["CNB292000118"], "81": ["CNB292000122"], "100": ["CNB292000001"], "101": ["CNB292000002"], "102": ["CNB292000003"], "110": ["CNB292000004"], "120": ["CNB292000005"], "150": ["CNB292000007"], "160": ["CNB292000008"], "161": ["CNB292000009"], "162": ["CNB292000010"], "163": ["CNB292000011"], "170": ["CNB292000012"], "171": ["CNB292000013"], "172": ["CNB292000014"], "200": ["CNB292000015"], "201": ["CNB292000016"], "202": ["CNB292000017"], "210": ["CNB292000018"], "211": ["CNB292000019"], "212": ["CNB292000020"], "220": ["CNB292000021"], "221": ["CNB292000022"], "222": ["CNB292000023"], "223": ["CNB292000024"], "230": ["CNB292000025"], "231": ["CNB292000026"], "232": ["CNB292000027"], "240": ["CNB292000028"], "250": ["CNB292000029"], "300": ["CNB292000030"], "310": ["CNB292000031"], "311": ["CNB292000032"], "320": ["CNB292000033"], "321": ["CNB292000034"], "322": ["CNB292000035"], "323": ["CNB292000036"], "324": ["CNB292000037"], "330": ["CNB292000038"], "331": ["CNB292000039"], "332": ["CNB292000040"], "333": ["CNB292000041"], "334": ["CNB292000042"], "335": ["CNB292000043"], "336": ["CNB292000044"], "340": ["CNB292000045"], "350": ["CNB292000046"], "351": ["CNB292000047"], "352": ["CNB292000048"], "360": ["CNB292000049"], "361": ["CNB292000050"], "400": ["CNB292000051"], "401": ["CNB292000052"], "410": ["CNB292000053"], "411": ["CNB292000054"], "420": ["CNB292000055"], "421": ["CNB292000056"], "422": ["CNB292000057"], "430": ["CNB292000058"], "431": ["CNB292000059"], "440": ["CNB292000060"], "441": ["CNB292000061"], "442": ["CNB292000062"], "443": ["CNB292000063"], "444": ["CNB292000064"], "500": ["CNB292000065"], "501": ["CNB292000066"], "510": ["CNB292000067"], "511": ["CNB292000068"], "520": ["CNB292000069"], "521": ["CNB292000070"], "522": ["CNB292000071"], "523": ["CNB292000072"], "530": ["CNB292000073"], "531": ["CNB292000074"], "532": ["CNB292000075"], "540": ["CNB292000076"], "541": ["CNB292000077"], "542": ["CNB292000078"], "550": ["CNB292000079"], "551": ["CNB292000080"], "560": ["CNB292000081"], "561": ["CNB292000082"], "600": ["CNB292000083"], "610": ["CNB292000084"], "611": ["CNB292000085"], "620": ["CNB292000086"], "630": ["CNB292000087"], "631": ["CNB292000088"], "632": ["CNB292000089"], "640": ["CNB292000090"], "641": ["CNB292000091"], "650": ["CNB292000092"], "651": ["CNB292000093"], "652": ["CNB292000094"], "653": ["CNB292000095"], "670": ["CNB292000096"], "700": ["CNB292000098"], "710": ["CNB292000099"], "711": ["CNB292000100"], "712": ["CNB292000101"], "720": ["CNB292000102"], "721": ["CNB292000103"], "730": ["CNB292000106"], "731": ["CNB292000107"], "732": ["CNB292000108"], "740": ["CNB292000109"], "750": ["CNB292000110"], "751": ["CNB292000111"], "760": ["CNB292000112"], "761": ["CNB292000113"], "762": ["CNB292000114"], "763": ["CNB292000115"], "764": ["CNB292000116"], "765": ["CNB292000117"], "800": ["CNB292000119"], "801": ["CNB292000120"], "802": ["CNB292000121"], "810": ["CNB292000123"], "811": ["CNB292000124"], "812": ["CNB292000125"], "813": ["CNB292000126"], "814": ["CNB292000127"], "900": ["CNB292000128"], "901": ["CNB292000129"], "910": ["CNB292000130"], "911": ["CNB292000131"], "912": ["CNB292000132"], "920": ["CNB292000133"], "921": ["CNB292000134"], "922": ["CNB292000135"], "923": ["CNB292000136"], "930": ["CNB292000137"], "931": ["CNB292000138"], "932": ["CNB292000139"], "940": ["CNB292000140"]}''')



@st.cache_data(ttl=25, show_spinner=False)
def fetch_gps(key, city, route):
    query = urlencode(dict(serviceKey=unquote(key), cityCode=city, routeId=route,
                           numOfRows=100, pageNo=1, _type="json"))
    try:
        with urlopen("https://apis.data.go.kr/1613000/BusLcInfoInqireService/getRouteAcctoBusLcList?" + query, timeout=4) as response:
            data = json.load(response)["response"]
        if str(data["header"]["resultCode"]) not in ("0", "00"):
            return None
        items = (data.get("body") or {}).get("items") or {}
        rows = items.get("item") or []
        return [rows] if isinstance(rows, dict) else rows
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def ordered_route_stops(rows):
    stops = []
    for row in rows:
        try:
            order = int(row["nodeord"])
            lat, lon = float(row["gpslati"]), float(row["gpslong"])
            if 33 <= lat <= 39 and 124 <= lon <= 132:
                stops.append((order, lon, lat, str(row.get("nodenm") or "정류장")))
        except (ValueError, TypeError, KeyError):
            continue
    return sorted(set(stops))


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_route_stops(key, city, route):
    query = urlencode(dict(serviceKey=unquote(key), cityCode=city, routeId=route,
                           numOfRows=1000, pageNo=1, _type="json"))
    try:
        endpoint = "https://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList"
        with urlopen(endpoint + "?" + query, timeout=4) as response:
            data = json.load(response)["response"]
        if str(data["header"]["resultCode"]) not in ("0", "00"):
            return []
        rows = ((data.get("body") or {}).get("items") or {}).get("item") or []
        return ordered_route_stops([rows] if isinstance(rows, dict) else rows)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []


def show_gps(city, routes, bus_no):
    st.markdown(f"#### 🗺️ {bus_no}번 노선과 버스 위치")
    try:
        key = st.secrets.get("DATA_GO_KR_API_KEY", "")
    except (FileNotFoundError, KeyError):
        key = ""
    key = str(key or os.getenv("DATA_GO_KR_API_KEY", "")).strip()
    if not key:
        st.info("관리자가 GPS 조회 키를 설정하면 사용할 수 있습니다.")
        return
    if not routes:
        st.info("이 노선은 GPS 조회가 연결되어 있지 않습니다.")
        return
    results = [fetch_gps(key, city, rid) for rid in routes]
    rows = [row for result in results if result for row in result if isinstance(row, dict)]
    if any(result is None for result in results):
        st.info("일부 또는 전체 차량 위치를 조회하지 못했습니다. 시간표는 아래에서 확인할 수 있습니다.")
    elif not rows:
        st.info("현재 API에서 이 노선의 차량 위치가 반환되지 않았습니다.")
    seen = set()
    pins = []
    for row in rows:
        stop = str(row.get("nodenm") or "").strip()
        try:
            lat, lon = float(row.get("gpslati")), float(row.get("gpslong"))
            coords = f"{lat:.5f}, {lon:.5f}" if 33 <= lat <= 39 and 124 <= lon <= 132 else ""
        except (TypeError, ValueError):
            coords = ""
        identity = (row.get("vehicleno"), stop, coords)
        if identity not in seen:
            seen.add(identity)
            if stop:
                st.text(f"🚏 {stop}")
            if coords:
                pins.append({"lat": lat, "lon": lon, "label": str(bus_no), "stop": stop or "정류장 정보 없음"})
    paths, stops = [], []
    for rid in routes:
        route_stops = fetch_route_stops(key, city, rid)
        if len(route_stops) >= 2:
            paths.append({"path": [[lon, lat] for _, lon, lat, _ in route_stops]})
            stops.extend({"lat": lat, "lon": lon, "description": name} for _, lon, lat, name in route_stops)
    if paths or pins:
        layers = []
        if paths:
            layers.extend([
                pdk.Layer("PathLayer", paths, get_path="path", get_color=[37, 99, 235, 210], width_min_pixels=3),
                pdk.Layer("ScatterplotLayer", stops, get_position="[lon, lat]", get_radius=4,
                          radius_min_pixels=3, radius_max_pixels=5, get_fill_color=[255, 255, 255],
                          stroked=True, get_line_color=[37, 99, 235], line_width_min_pixels=1, pickable=True),
            ])
        if pins:
            frame = pd.DataFrame(pins).assign(description=lambda df: df.label + "번 버스 · " + df.stop)
            layers.extend([
            pdk.Layer("ScatterplotLayer", frame, get_position="[lon, lat]", get_radius=14,
                      radius_units='"pixels"', radius_min_pixels=13, radius_max_pixels=16, get_fill_color=[220, 38, 38, 245],
                      stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=3, pickable=True),
            pdk.Layer("TextLayer", frame, get_position="[lon, lat]", get_text="label",
                      get_size=12, get_color=[255, 255, 255], get_alignment_baseline='"center"'),
            ])
        points = stops + pins
        lats = [pt["lat"] for pt in points]
        lons = [pt["lon"] for pt in points]
        span = max(max(lats)-min(lats), max(lons)-min(lons), 0.01)
        zoom = min(13, max(6, math.log2(0.25 / span) + 9.8))
        deck = pdk.Deck(layers=layers, map_provider="carto", map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", initial_view_state=pdk.ViewState(
            latitude=(min(lats)+max(lats))/2, longitude=(min(lons)+max(lons))/2, zoom=zoom),
            tooltip={"text": "{description}"})
        st.pydeck_chart(deck, height=300)
        if paths:
            st.caption("🔵 경유 정류장 연결선 · ⚪ 정류장 · 🔴 실시간 버스. 연결선은 실제 도로 궤적과 다를 수 있습니다.")
        else:
            st.caption("노선 정보를 불러오지 못해 실시간 차량 위치만 표시합니다.")
    elif rows:
        st.caption("지도에 표시할 GPS 좌표가 없습니다.")
    if not paths and not pins:
        st.caption("노선을 표시하려면 공공데이터포털에서 TAGO 버스노선정보 활용 신청을 확인하세요.")
    if rows:
        st.caption("노선 전체에서 조회된 위치입니다. 선택한 방향의 도착 예정 시간은 아닙니다.")


def taxi_distance_fare(distance_km, pickup):
    base, included_m, step_m = (4000, 1000, 75) if pickup == "금산" else (4800, 1800, 125)
    return base + 100 * (max(0, round(distance_km * 1000) - included_m) // step_m)


@st.cache_data(ttl=3600, show_spinner=False)
def taxi_api_json(url, key, **params):
    request = Request(url + "?" + urlencode(params), headers={"Authorization": "KakaoAK " + key})
    with urlopen(request, timeout=6) as response:
        return json.load(response)


def taxi_stop_choices(name, region, key):
    query = f"{region} {name.removesuffix('종점')} 정류장"
    data = taxi_api_json("https://dapi.kakao.com/v2/local/search/keyword.json", key, query=query)
    return [item for item in data.get("documents", []) if item.get("x") and item.get("y")]


def show_taxi_comparison():
    st.markdown("### 🚕 택시 vs 🚌 버스")
    mode = st.radio("비교할 버스", ["금산 버스", "대전 34번"], horizontal=True)
    now = get_kst_now()
    minute = now.hour * 60 + now.minute
    if mode == "금산 버스":
        origin, dest = st.session_state.g_origin, st.session_state.g_dest
        options = find_all_geumsan_options(origin, dest, minute)
        bus = options[0] if options else None
    else:
        origin, dest = st.session_state.dj_origin, st.session_state.dj_dest
        bus = evaluate_daejeon_34(st.session_state.dj_dir, origin, dest, minute)
    st.caption(f"버스 메뉴에서 선택한 구간: {origin} → {dest}")
    pool = sorted(NODES) if mode == "금산 버스" else list(dict.fromkeys([origin, dest] + [x["name"] for x in bus["stops"]]))
    start = st.selectbox("🚏 출발 정류장", pool, index=pool.index(origin), key=f"taxi_start_{mode}_{origin}")
    end = st.selectbox("🏁 도착 정류장", pool, index=pool.index(dest), key=f"taxi_end_{mode}_{dest}")
    if mode == "금산 버스":
        options = find_all_geumsan_options(start, end, minute)
        bus = options[0] if options else None
    else:
        bus = None
        for direction in (st.session_state.dj_dir, "to_daejeon", "to_daedun"):
            candidate = evaluate_daejeon_34(direction, start, end, minute)
            names = [item["name"] for item in candidate["stops"]]
            if start in names and end in names and names.index(start) < names.index(end):
                bus = candidate
                break
    try:
        key = st.secrets.get("KAKAO_REST_API_KEY", "")
    except (FileNotFoundError, KeyError):
        key = ""
    key = str(key or os.getenv("KAKAO_REST_API_KEY", "")).strip()
    distance = None
    if start == end:
        st.info("출발과 도착 정류장을 다르게 선택하세요.")
    elif not key:
        st.info("관리자가 KAKAO_REST_API_KEY를 설정하면 정류장 사이 도로 거리와 요금을 자동으로 계산합니다.")
    else:
        coords = []
        try:
            for label, name in (("출발", start), ("도착", end)):
                region = "금산" if mode == "금산 버스" or "진산" in name or "복수" in name or "대둔산" in name else ""
                choices = taxi_stop_choices(name, region, key)
                if not choices:
                    st.warning(f"{label} 정류장 ‘{name}’을 지도에서 찾지 못했습니다.")
                    break
                selected = st.selectbox(f"{label} 위치 확인", range(len(choices)), index=0 if len(choices) == 1 else None,
                                        format_func=lambda i, choices=choices: choices[i]["place_name"] + " · " + choices[i].get("address_name", ""),
                                        key=f"taxi_match_{label}_{name}")
                if selected is None:
                    break
                item = choices[selected]
                coords.append(f"{item['x']},{item['y']}")
            if len(coords) == 2 and coords[0] != coords[1]:
                route = taxi_api_json("https://apis-navi.kakaomobility.com/v1/directions", key, origin=coords[0], destination=coords[1], priority="RECOMMEND")["routes"][0]
                if route.get("result_code") == 0:
                    distance = route["summary"]["distance"] / 1000
                    st.caption(f"자동차 경로 약 {distance:.1f} km")
            if len(coords) == 2 and distance is None:
                st.info("두 위치 사이의 자동차 경로를 확인하지 못했습니다.")
        except (OSError, ValueError, TypeError, KeyError, IndexError):
            st.warning("지도 검색 또는 길찾기에 실패했습니다. 잠시 후 다시 시도하거나 API 설정을 확인해 주세요.")
    pickup = st.radio("택시 운임 기준 (택시 출발 지역)", ["금산", "대전"], horizontal=True,
                      index=int("대전" in start or "서남부" in start), key=f"taxi_region_{start}")
    left, right = st.columns(2)
    with left:
        if bus:
            wait, ride = max(0, bus["wait_from_now"]), bus["ride_min"]
            st.metric("🚌 버스 예상 총 시간", f"{wait + ride:,}분")
            st.caption(f"시간표 기준 · 대기 {wait:,}분 + 탑승 약 {ride}분")
        else:
            st.metric("🚌 버스 예상 총 시간", "직행 정보 없음")
    with right:
        st.metric("🚕 택시 예상 요금", f"약 {taxi_distance_fare(distance, pickup):,}원" if distance is not None else "경로 확인 필요")
        st.caption("주간 중형택시 거리 요금만 반영합니다. 정체·할증·통행료는 포함하지 않습니다.")



def _supports_width_stretch() -> bool:
    try:
        parts = [int(p) for p in st.__version__.split(".")[:2] if p.isdigit()]
        return tuple(parts) >= (1, 45)
    except Exception:
        return False


STRETCH_KW = {"width": "stretch"} if _supports_width_stretch() else {"use_container_width": True}

NODES = {'금산읍': {'x': 56, 'y': 18, 'hub': True, 'region': '금산읍(시외·군내터미널)'},
 '제원': {'x': 68, 'y': 13, 'hub': True, 'region': '제원면'},
 '군북': {'x': 75, 'y': 35, 'hub': True, 'region': '군북면'},
 '마전': {'x': 58, 'y': 56, 'hub': True, 'region': '추부면(마전)'},
 '복수': {'x': 52, 'y': 50, 'hub': True, 'region': '복수면'},
 '진산': {'x': 48, 'y': 50, 'hub': True, 'region': '진산면'},
 '금성': {'x': 53, 'y': 29, 'hub': True, 'region': '금성면'},
 '하금': {'x': 23, 'y': 55, 'hub': True, 'region': '남이면(하금)'},
 '남일(초현)': {'x': 26, 'y': 28, 'hub': True, 'region': '남일면'},
 '부리': {'x': 22, 'y': 15, 'hub': True, 'region': '부리면'},
 '사달': {'x': 62, 'y': 15, 'hub': False, 'region': '제원면'},
 '송림': {'x': 62, 'y': 20, 'hub': False, 'region': '제원면'},
 '수당': {'x': 65, 'y': 22, 'hub': False, 'region': '제원면'},
 '명곡리': {'x': 69, 'y': 24, 'hub': False, 'region': '제원면'},
 '구래기': {'x': 79, 'y': 10, 'hub': False, 'region': '제원면'},
 '닥실': {'x': 79, 'y': 8, 'hub': False, 'region': '제원면'},
 '금성리': {'x': 77, 'y': 6, 'hub': False, 'region': '제원면'},
 '용화': {'x': 78, 'y': 5, 'hub': False, 'region': '제원면'},
 '천내': {'x': 85, 'y': 8, 'hub': False, 'region': '제원면'},
 '원골': {'x': 89, 'y': 11, 'hub': False, 'region': '제원면'},
 '가선리': {'x': 90, 'y': 7, 'hub': False, 'region': '제원면'},
 '구역': {'x': 75, 'y': 20, 'hub': False, 'region': '제원면'},
 '대산': {'x': 79, 'y': 18, 'hub': False, 'region': '제원면'},
 '길곡': {'x': 83, 'y': 26, 'hub': False, 'region': '제원면'},
 '신안사': {'x': 89, 'y': 31, 'hub': False, 'region': '제원면'},
 '화골': {'x': 89, 'y': 29, 'hub': False, 'region': '제원면'},
 '재두': {'x': 88, 'y': 26, 'hub': False, 'region': '제원면'},
 '구상리': {'x': 75, 'y': 24, 'hub': False, 'region': '군북면'},
 '천을리': {'x': 75, 'y': 29, 'hub': False, 'region': '군북면'},
 '내부리': {'x': 62, 'y': 31, 'hub': False, 'region': '군북면'},
 '산안2리': {'x': 84, 'y': 36, 'hub': False, 'region': '군북면'},
 '상곡2리': {'x': 88, 'y': 46, 'hub': False, 'region': '군북면'},
 '보광리': {'x': 83, 'y': 52, 'hub': False, 'region': '군북면'},
 '동평': {'x': 75, 'y': 39, 'hub': False, 'region': '군북면'},
 '조정리': {'x': 75, 'y': 43, 'hub': False, 'region': '군북면'},
 '서대리': {'x': 75, 'y': 47, 'hub': False, 'region': '추부면'},
 '신평': {'x': 75, 'y': 51, 'hub': False, 'region': '추부면'},
 '성당리': {'x': 79, 'y': 55, 'hub': False, 'region': '추부면'},
 '서대산': {'x': 81, 'y': 59, 'hub': False, 'region': '추부면'},
 '비례리': {'x': 69, 'y': 56, 'hub': False, 'region': '추부면'},
 '자부리': {'x': 64, 'y': 55, 'hub': False, 'region': '추부면'},
 '메데기': {'x': 79, 'y': 22, 'hub': False, 'region': '군북면'},
 '의총리': {'x': 58, 'y': 27, 'hub': False, 'region': '금성면'},
 '새터': {'x': 58, 'y': 34, 'hub': False, 'region': '금성면'},
 '대암리': {'x': 60, 'y': 38, 'hub': False, 'region': '금성면'},
 '마수': {'x': 56, 'y': 35, 'hub': False, 'region': '금성면'},
 '파초': {'x': 55, 'y': 32, 'hub': False, 'region': '금성면'},
 '장목골': {'x': 55, 'y': 24, 'hub': False, 'region': '금성면'},
 '두곡': {'x': 56, 'y': 26, 'hub': False, 'region': '금성면'},
 '오룡': {'x': 52, 'y': 25, 'hub': False, 'region': '금성면'},
 '하신': {'x': 58, 'y': 43, 'hub': False, 'region': '추부면'},
 '추정': {'x': 58, 'y': 48, 'hub': False, 'region': '추부면'},
 '장대리': {'x': 60, 'y': 61, 'hub': False, 'region': '추부면'},
 '상지말': {'x': 53, 'y': 34, 'hub': False, 'region': '복수면'},
 '알미': {'x': 52, 'y': 38, 'hub': False, 'region': '복수면'},
 '초미동': {'x': 52, 'y': 44, 'hub': False, 'region': '진산면'},
 '목소리': {'x': 51, 'y': 47, 'hub': False, 'region': '복수면'},
 '백암': {'x': 54, 'y': 54, 'hub': False, 'region': '복수면'},
 '신대(복수)': {'x': 53, 'y': 58, 'hub': False, 'region': '복수면'},
 '서남부터미널(대전)': {'x': 50, 'y': 65, 'hub': False, 'region': '대전 연계(공공형)'},
 '양촌': {'x': 54, 'y': 22, 'hub': False, 'region': '금성면'},
 '상촌': {'x': 50, 'y': 31, 'hub': False, 'region': '금성면'},
 '어동골': {'x': 47, 'y': 34, 'hub': False, 'region': '금산읍'},
 '상탄': {'x': 48, 'y': 38, 'hub': False, 'region': '금성면'},
 '엄정리': {'x': 48, 'y': 43, 'hub': False, 'region': '진산면'},
 '부암': {'x': 47, 'y': 46, 'hub': False, 'region': '진산면'},
 '원터': {'x': 50, 'y': 46, 'hub': False, 'region': '진산면'},
 '만악': {'x': 50, 'y': 42, 'hub': False, 'region': '진산면'},
 '태고사': {'x': 45, 'y': 56, 'hub': False, 'region': '진산면'},
 '도산': {'x': 47, 'y': 59, 'hub': False, 'region': '진산면'},
 '행정': {'x': 49, 'y': 57, 'hub': False, 'region': '진산면'},
 '지방리': {'x': 50, 'y': 55, 'hub': False, 'region': '진산면'},
 '당디': {'x': 48, 'y': 54, 'hub': False, 'region': '진산면'},
 '성곡': {'x': 48, 'y': 21, 'hub': False, 'region': '금산읍'},
 '보석사입구': {'x': 43, 'y': 23, 'hub': False, 'region': '남이면'},
 '서당골': {'x': 40, 'y': 31, 'hub': False, 'region': '금산읍'},
 '와정': {'x': 43, 'y': 35, 'hub': False, 'region': '남이면'},
 '석동': {'x': 37, 'y': 33, 'hub': False, 'region': '남이면'},
 '원석동': {'x': 31, 'y': 40, 'hub': False, 'region': '남이면'},
 '자연휴양림': {'x': 28, 'y': 48, 'hub': False, 'region': '남이면'},
 '역평리': {'x': 27, 'y': 52, 'hub': False, 'region': '남이면'},
 '건천리': {'x': 33, 'y': 55, 'hub': False, 'region': '남이면'},
 '석막': {'x': 40, 'y': 52, 'hub': False, 'region': '남이면'},
 '활골': {'x': 36, 'y': 51, 'hub': False, 'region': '남이면'},
 '대양리': {'x': 29, 'y': 56, 'hub': False, 'region': '남이면'},
 '흑암리': {'x': 14, 'y': 55, 'hub': False, 'region': '남이면'},
 '광대정': {'x': 11, 'y': 53, 'hub': False, 'region': '남이면'},
 '신천사거리': {'x': 21, 'y': 35, 'hub': False, 'region': '남일면'},
 '매곡': {'x': 27, 'y': 39, 'hub': False, 'region': '남일면'},
 '양대': {'x': 20, 'y': 40, 'hub': False, 'region': '남일면'},
 '음대리': {'x': 17, 'y': 36, 'hub': False, 'region': '남일면'},
 '신동': {'x': 15, 'y': 41, 'hub': False, 'region': '남일면'},
 '사기소': {'x': 15, 'y': 46, 'hub': False, 'region': '남일면'},
 '신정': {'x': 11, 'y': 45, 'hub': False, 'region': '남일면'},
 '원동': {'x': 13, 'y': 36, 'hub': False, 'region': '남일면'},
 '수천리': {'x': 14, 'y': 32, 'hub': False, 'region': '남일면'},
 '장안리': {'x': 11, 'y': 40, 'hub': False, 'region': '무주(부남)연계'},
 '덕천': {'x': 23, 'y': 29, 'hub': False, 'region': '남일면'},
 '평대리': {'x': 21, 'y': 31, 'hub': False, 'region': '남일면'},
 '신대리(금산)': {'x': 48, 'y': 18, 'hub': False, 'region': '금산읍'},
 '황풍': {'x': 37, 'y': 18, 'hub': False, 'region': '부리면'},
 '관천': {'x': 29, 'y': 18, 'hub': False, 'region': '부리면'},
 '호미동': {'x': 29, 'y': 21, 'hub': False, 'region': '부리면'},
 '금고리': {'x': 20, 'y': 20, 'hub': False, 'region': '부리면'},
 '가덕': {'x': 17, 'y': 24, 'hub': False, 'region': '부리면'},
 '상평당': {'x': 17, 'y': 29, 'hub': False, 'region': '부리면'},
 '평촌': {'x': 17, 'y': 16, 'hub': False, 'region': '부리면'},
 '수통리': {'x': 13, 'y': 22, 'hub': False, 'region': '부리면'},
 '어재리': {'x': 11, 'y': 17, 'hub': False, 'region': '부리면'},
 '압수': {'x': 13, 'y': 14, 'hub': False, 'region': '부리면'},
 '물페기': {'x': 18, 'y': 11, 'hub': False, 'region': '부리면'},
 '신촌': {'x': 19, 'y': 7, 'hub': False, 'region': '부리면'},
 '라천': {'x': 58, 'y': 12, 'hub': False, 'region': '부리면'},
 '창평': {'x': 51, 'y': 9, 'hub': False, 'region': '부리면'},
 '갈티': {'x': 42, 'y': 11, 'hub': False, 'region': '부리면'},
 '백일사': {'x': 34, 'y': 13, 'hub': False, 'region': '부리면'}}

BUS_ROUTES = {'15': {'name': '15번 (공공형)',
        'category': '공공형버스',
        'region': '오룡방면',
        'stops': ['금산읍', '양촌', '오룡', '상지말', '알미'],
        'out_times': ['12:40'],
        'in_times': ['13:35'],
        'desc': '금산읍 ↔ 오룡·상지말·알미 공공형버스'},
 '68': {'name': '68번 (공공형)',
        'category': '공공형버스',
        'region': '남이방면',
        'stops': ['금산읍', '성곡', '석동', '원석동', '자연휴양림', '건천리'],
        'out_times': ['09:20', '14:40'],
        'in_times': ['10:50', '16:10'],
        'desc': '금산읍 ↔ 석동·남이자연휴양림 공공형버스'},
 '70': {'name': '70번 (공공형)',
        'category': '공공형버스',
        'region': '진산·복수방면',
        'stops': ['금산읍', '복수', '백암', '신대(복수)', '진산'],
        'out_times': ['14:20', '15:30', '16:40'],
        'in_times': ['14:50', '16:00', '17:00'],
        'desc': '금산발 곡남·수영·복수중·백암·신대 경유'},
 '71': {'name': '71번 (공공형)',
        'category': '공공형버스',
        'region': '복수·진산방면',
        'stops': ['복수', '백암', '신대(복수)', '진산'],
        'out_times': ['07:40'],
        'in_times': ['08:25'],
        'desc': '복수면사무소 ↔ 백암·신대·진산'},
 '72': {'name': '72번 (공공형)',
        'category': '공공형버스',
        'region': '진산방면',
        'stops': ['금산읍', '금성', '만악', '원터', '부암', '진산'],
        'out_times': ['10:20', '13:10'],
        'in_times': ['11:10', '17:30'],
        'desc': '우체국·양전·원터·만악·부암 경유 진산행'},
 '73': {'name': '73번 (공공형)',
        'category': '공공형버스',
        'region': '진산방면',
        'stops': ['금산읍', '양촌', '금성', '원터', '진산'],
        'out_times': ['06:30'],
        'in_times': ['19:50'],
        'desc': '금산읍 ↔ 금성면·원터·진산'},
 '77': {'name': '77번 (공공형)',
        'category': '공공형버스',
        'region': '진산방면',
        'stops': ['금산읍', '금성', '파초', '초미동', '진산'],
        'out_times': ['07:00', '17:50'],
        'in_times': ['08:05', '18:45'],
        'desc': '읍내·파초·초미동 경유 진산행'},
 '81': {'name': '81번 (공공형)',
        'category': '공공형버스',
        'region': '진산↔대전서남부',
        'stops': ['진산', '당디', '행정', '지방리', '신대(복수)', '서남부터미널(대전)'],
        'out_times': ['07:00', '10:25', '13:55', '16:40'],
        'in_times': ['08:45', '12:30', '15:20', '18:40'],
        'desc': '진산 ↔ 당디·행정·지방·신대·안영·대전서남부터미널'},
 '100': {'name': '100번',
         'category': '농어촌버스',
         'region': '서당골·어동골방면',
         'stops': ['금산읍', '성곡', '서당골', '어동골'],
         'out_times': ['10:20', '12:10', '15:00', '18:10'],
         'in_times': ['10:35', '12:25', '15:20', '18:30'],
         'desc': '금산읍 ↔ 서당골·어동골'},
 '102': {'name': '102번',
         'category': '농어촌버스',
         'region': '서당골·와정방면',
         'stops': ['금산읍', '성곡', '서당골', '와정'],
         'out_times': ['07:25'],
         'in_times': ['07:40'],
         'desc': '금산읍 ↔ 서당골·와정'},
 '110': {'name': '110번',
         'category': '농어촌버스',
         'region': '와정방면',
         'stops': ['금산읍', '성곡', '보석사입구', '와정'],
         'out_times': ['14:00', '16:35'],
         'in_times': ['14:15', '16:50'],
         'desc': '금산읍 ↔ 와정'},
 '120': {'name': '120번',
         'category': '농어촌버스',
         'region': '어동골방면',
         'stops': ['금산읍', '양촌', '어동골'],
         'out_times': ['08:10'],
         'in_times': ['08:25'],
         'desc': '금산읍 ↔ 어동골'},
 '150': {'name': '150번',
         'category': '농어촌버스',
         'region': '오룡방면(금성)',
         'stops': ['금산읍', '양촌', '오룡', '장목골'],
         'out_times': ['17:40'],
         'in_times': ['18:10'],
         'desc': '금산읍 ↔ 오룡·장목골'},
 '160': {'name': '160번',
         'category': '농어촌버스',
         'region': '오룡·마수방면(금성)',
         'stops': ['금산읍', '양촌', '장목골', '오룡', '두곡', '금성', '파초', '마수', '새터'],
         'out_times': ['06:20', '08:30', '12:35', '15:30'],
         'in_times': ['06:40', '08:50', '12:50', '15:45'],
         'desc': '금산읍 ↔ 장목골·오룡·두곡·마수·새말'},
 '170': {'name': '170번',
         'category': '농어촌버스',
         'region': '마수방면(금성)',
         'stops': ['금산읍', '의총리', '새터', '마수', '파초', '금성'],
         'out_times': ['06:10', '09:40', '17:00'],
         'in_times': ['06:25', '12:50', '17:15'],
         'desc': '금산읍 ↔ 새말·마수·파초'},
 '200': {'name': '200번',
         'category': '농어촌버스',
         'region': '제원(명곡리)방면',
         'stops': ['금산읍', '송림', '수당', '제원', '명곡리'],
         'out_times': ['07:15', '10:10', '13:00', '16:20', '19:40'],
         'in_times': ['07:35', '10:30', '13:25', '16:50', '20:00'],
         'desc': '금산읍 ↔ 송림·제원·명곡리'},
 '210': {'name': '210번',
         'category': '농어촌버스',
         'region': '제원(신안사)방면',
         'stops': ['금산읍', '사달', '제원', '구역', '대산', '길곡', '재두', '화골', '신안사'],
         'out_times': ['06:00', '13:50', '18:50'],
         'in_times': ['06:30', '14:30', '19:30'],
         'desc': '금산읍 ↔ 제원·대산·재두·화골·신안사'},
 '220': {'name': '220번',
         'category': '농어촌버스',
         'region': '제원(용화·금성리)방면',
         'stops': ['금산읍', '사달', '제원', '구래기', '닥실', '금성리', '용화', '천내'],
         'out_times': ['08:35', '10:10', '14:45', '18:15'],
         'in_times': ['09:00', '10:40', '12:35', '18:45'],
         'desc': '금산읍 ↔ 제원·닥실·금성리·용화·천내'},
 '230': {'name': '230번',
         'category': '농어촌버스',
         'region': '제원(원골·용화)방면',
         'stops': ['금산읍', '사달', '제원', '대산', '구래기', '용화', '천내', '원골'],
         'out_times': ['06:05', '12:05', '19:20'],
         'in_times': ['06:25', '15:10', '19:45'],
         'desc': '금산읍 ↔ 제원·대산·용화·천내·원골'},
 '240': {'name': '240번',
         'category': '농어촌버스',
         'region': '제원(천내)방면',
         'stops': ['금산읍', '사달', '제원', '구래기', '천내'],
         'out_times': ['15:00'],
         'in_times': ['15:25'],
         'desc': '금산읍 ↔ 제원·천내'},
 '250': {'name': '250번',
         'category': '농어촌버스',
         'region': '제원(가선리)방면',
         'stops': ['금산읍', '사달', '제원', '구래기', '천내', '원골', '가선리'],
         'out_times': ['07:40', '10:00', '13:00', '16:10', '18:40'],
         'in_times': ['08:00', '10:30', '13:25', '16:35', '19:05'],
         'desc': '금산읍 ↔ 제원·천내·가선리'},
 '300': {'name': '300번',
         'category': '농어촌버스',
         'region': '부리(라천·가덕)방면',
         'stops': ['금산읍', '사달', '라천', '창평', '부리', '관천', '가덕'],
         'out_times': ['13:20'],
         'in_times': ['13:50'],
         'desc': '금산읍 ↔ 라천·부리·가덕·관천'},
 '310': {'name': '310번',
         'category': '농어촌버스',
         'region': '부리(신촌)방면',
         'stops': ['금산읍', '라천', '창평', '부리', '물페기', '신촌'],
         'out_times': ['08:25', '16:00'],
         'in_times': ['09:00', '16:40'],
         'desc': '금산읍 ↔ 창평·부리·물페기·신촌'},
 '320': {'name': '320번',
         'category': '농어촌버스',
         'region': '부리(어재리)방면',
         'stops': ['금산읍', '신대리(금산)', '황풍', '관천', '부리', '압수', '어재리'],
         'out_times': ['06:10', '09:00', '11:10', '15:00', '17:55', '19:25'],
         'in_times': ['06:40', '09:35', '11:50', '15:40', '18:35', '19:55'],
         'desc': '금산읍 ↔ 황풍·관천·부리·압수·어재리'},
 '330': {'name': '330번',
         'category': '농어촌버스',
         'region': '부리(수통리)방면',
         'stops': ['금산읍', '사달', '라천', '창평', '갈티', '부리', '관천', '물페기', '수통리'],
         'out_times': ['06:00', '08:35', '10:15', '12:30', '14:00', '16:50', '19:00'],
         'in_times': ['06:30', '09:10', '10:55', '13:10', '14:50', '17:35', '19:40'],
         'desc': '금산읍 ↔ 창평·부리·관천·수통리 대표 노선'},
 '340': {'name': '340번',
         'category': '농어촌버스',
         'region': '부리(금고리·평촌)방면',
         'stops': ['금산읍', '라천', '창평', '갈티', '부리', '금고리', '평촌'],
         'out_times': ['07:40'],
         'in_times': ['08:00'],
         'desc': '금산읍 ↔ 갈티·부리·금고리·평촌'},
 '350': {'name': '350번',
         'category': '농어촌버스',
         'region': '부리(백일사)방면',
         'stops': ['금산읍', '사달', '라천', '창평', '갈티', '백일사', '부리', '가덕'],
         'out_times': ['10:30', '12:20', '15:30'],
         'in_times': ['11:05', '12:55', '16:05'],
         'desc': '금산읍 ↔ 창평·갈티·백일사·가덕'},
 '360': {'name': '360번',
         'category': '농어촌버스',
         'region': '부리(상평당)방면',
         'stops': ['금산읍', '신대리(금산)', '황풍', '관천', '부리', '금고리', '가덕', '상평당'],
         'out_times': ['06:20', '08:40', '13:40', '17:40'],
         'in_times': ['06:50', '09:10', '14:20', '18:20'],
         'desc': '금산읍 ↔ 관천·부리·가덕·상평당'},
 '400': {'name': '400번',
         'category': '농어촌버스',
         'region': '군북(내부리)방면',
         'stops': ['금산읍', '의총리', '내부리', '마수', '파초'],
         'out_times': ['07:20', '13:25', '18:30'],
         'in_times': ['07:30', '13:40', '18:45'],
         'desc': '금산읍 ↔ 내부리·마수·파초'},
 '410': {'name': '410번',
         'category': '농어촌버스',
         'region': '군북(내부리·의총리)방면',
         'stops': ['금산읍', '의총리', '새터', '내부리'],
         'out_times': ['10:10', '15:40'],
         'in_times': ['10:20', '16:00'],
         'desc': '금산읍 ↔ 의총리·새터가마실·내부리'},
 '420': {'name': '420번',
         'category': '농어촌버스',
         'region': '군북·마전방면',
         'stops': ['금산읍', '제원', '구역', '구상리', '천을리', '군북', '동평', '조정리', '신평', '비례리', '마전'],
         'out_times': ['07:55', '10:30', '15:45', '16:30'],
         'in_times': ['08:55', '11:10', '16:20', '17:05'],
         'desc': '금산읍 ↔ 제원·군북·조정리·마전 순환연계'},
 '430': {'name': '430번',
         'category': '농어촌버스',
         'region': '군북(메데기)방면',
         'stops': ['금산읍', '제원', '구역', '대산', '메데기', '군북'],
         'out_times': ['09:40', '13:30'],
         'in_times': ['10:10', '14:05'],
         'desc': '금산읍 ↔ 대산·메데기·군북'},
 '440': {'name': '440번',
         'category': '농어촌버스',
         'region': '군북(보광리)방면',
         'stops': ['금산읍', '구상리', '천을리', '군북', '산안2리', '상곡2리', '보광리'],
         'out_times': ['06:00', '08:10', '11:45', '17:40', '19:00'],
         'in_times': ['06:35', '09:05', '13:00', '18:45', '19:50'],
         'desc': '금산읍 ↔ 군북·산안2리·상곡2리·보광리'},
 '500': {'name': '500번',
         'category': '농어촌버스',
         'region': '부리(호미동)방면',
         'stops': ['금산읍', '신대리(금산)', '황풍', '관천', '호미동'],
         'out_times': ['07:15', '14:10'],
         'in_times': ['07:30', '14:30'],
         'desc': '금산읍 ↔ 황풍·관천·호미동'},
 '510': {'name': '510번',
         'category': '농어촌버스',
         'region': '남일(신정)방면',
         'stops': ['금산읍', '남일(초현)', '신천사거리', '음대리', '신정'],
         'out_times': ['09:55', '14:00'],
         'in_times': ['10:25', '14:35'],
         'desc': '금산읍 ↔ 남일·신천·신정'},
 '520': {'name': '520번',
         'category': '농어촌버스',
         'region': '남일(평대·원동)방면',
         'stops': ['금산읍', '남일(초현)', '덕천', '평대리', '신천사거리', '음대리', '원동'],
         'out_times': ['12:20', '15:50', '17:05', '18:50'],
         'in_times': ['12:50', '16:30', '17:40', '19:20'],
         'desc': '금산읍 ↔ 남일(초현)·덕천·평대·음대·원동'},
 '522': {'name': '522번',
         'category': '농어촌버스',
         'region': '남일(원동·사미리)방면',
         'stops': ['금산읍', '남일(초현)', '평대리', '음대리', '원동'],
         'out_times': ['08:30'],
         'in_times': ['09:00'],
         'desc': '금산읍 ↔ 평대리·음대·원동·사미리'},
 '530': {'name': '530번',
         'category': '농어촌버스',
         'region': '남일(신동)방면',
         'stops': ['금산읍', '남일(초현)', '신천사거리', '신정', '신동'],
         'out_times': ['07:10', '16:30', '19:30'],
         'in_times': ['07:40', '17:10', '20:00'],
         'desc': '금산읍 ↔ 남일·신정·신동리'},
 '540': {'name': '540번',
         'category': '농어촌버스',
         'region': '남일(사기소)방면',
         'stops': ['금산읍', '남일(초현)', '평대리', '신천사거리', '신동', '신정', '사기소'],
         'out_times': ['06:00', '12:00', '18:15'],
         'in_times': ['06:30', '12:40', '18:55'],
         'desc': '금산읍 ↔ 평대리·신정·사기소'},
 '550': {'name': '550번',
         'category': '농어촌버스',
         'region': '남일(수천리)방면',
         'stops': ['금산읍', '남일(초현)', '신천사거리', '신동', '수천리'],
         'out_times': ['08:50', '14:40'],
         'in_times': ['09:30', '15:25'],
         'desc': '금산읍 ↔ 신천·신동·수천리'},
 '560': {'name': '560번',
         'category': '농어촌버스',
         'region': '남일·부남(장안리)방면',
         'stops': ['금산읍', '남일(초현)', '신천사거리', '음대리', '원동', '장안리'],
         'out_times': ['10:50', '14:20'],
         'in_times': ['11:30', '15:00'],
         'desc': '금산읍 ↔ 초현·원동·부남·장안리'},
 '600': {'name': '600번',
         'category': '농어촌버스',
         'region': '남이(와정·하금)방면',
         'stops': ['금산읍', '성곡', '와정', '원석동', '하금'],
         'out_times': ['11:05', '19:35'],
         'in_times': ['11:25', '20:00'],
         'desc': '금산읍 ↔ 와정·하금'},
 '610': {'name': '610번',
         'category': '농어촌버스',
         'region': '남이(활골·광대정)방면',
         'stops': ['금산읍', '신천사거리', '양대', '하금', '흑암리', '광대정', '활골'],
         'out_times': ['08:10', '17:50'],
         'in_times': ['09:10', '18:40'],
         'desc': '금산읍 ↔ 양대·광대정·윗관운리·활골'},
 '620': {'name': '620번',
         'category': '농어촌버스',
         'region': '남이(매곡)방면',
         'stops': ['금산읍', '신천사거리', '매곡', '원석동', '하금'],
         'out_times': ['14:35'],
         'in_times': ['15:35'],
         'desc': '금산읍 ↔ 매곡·윗관운리'},
 '630': {'name': '630번',
         'category': '농어촌버스',
         'region': '남이(석동·건천리)방면',
         'stops': ['금산읍', '성곡', '보석사입구', '석동', '원석동', '하금', '대양리', '건천리'],
         'out_times': ['06:00', '11:40', '18:10'],
         'in_times': ['06:40', '12:30', '18:55'],
         'desc': '금산읍 ↔ 석동·하금·대양리·건천리'},
 '640': {'name': '640번',
         'category': '농어촌버스',
         'region': '남이(역평리)방면',
         'stops': ['금산읍', '성곡', '보석사입구', '석동', '원석동', '자연휴양림', '역평리'],
         'out_times': ['08:35', '15:20', '16:30'],
         'in_times': ['09:10', '15:55', '17:10'],
         'desc': '금산읍 ↔ 석동·역평리'},
 '650': {'name': '650번',
         'category': '농어촌버스',
         'region': '남이(양대·대양리)방면',
         'stops': ['금산읍', '신천사거리', '매곡', '양대', '하금', '활골', '대양리'],
         'out_times': ['10:10', '13:05', '13:50', '19:00'],
         'in_times': ['10:50', '14:10', '14:50', '19:30'],
         'desc': '금산읍 ↔ 매곡·양대·활골·대양리'},
 '670': {'name': '670번',
         'category': '농어촌버스',
         'region': '남이(광대정·흑암)방면',
         'stops': ['금산읍', '신천사거리', '매곡', '음대리', '흑암리', '광대정'],
         'out_times': ['06:20'],
         'in_times': ['06:40'],
         'desc': '금산읍 ↔ 매곡리·음대리·흑암리·광대정'},
 '700': {'name': '700번',
         'category': '농어촌버스',
         'region': '진산(상탄·엄정)방면',
         'stops': ['금산읍', '양촌', '금성', '상촌', '상탄', '엄정리'],
         'out_times': ['18:40'],
         'in_times': ['19:10'],
         'desc': '금산읍 ↔ 상탄·하엄정'},
 '710': {'name': '710번',
         'category': '농어촌버스',
         'region': '진산(석막)방면',
         'stops': ['금산읍', '금성', '상탄', '엄정리', '만악', '진산', '석막', '마전', '군북', '천을리'],
         'out_times': ['07:40', '11:30', '13:10', '17:00'],
         'in_times': ['08:30', '08:50', '12:20', '13:50', '14:30', '17:50', '18:10'],
         'desc': '금산읍 ↔ 엄정·만악·진산·석막 (마전·천을리 연계)'},
 '720': {'name': '720번',
         'category': '농어촌버스',
         'region': '진산(건천리)방면',
         'stops': ['금산읍', '금성', '진산', '석막', '건천리'],
         'out_times': ['13:30'],
         'in_times': ['07:00', '07:25', '14:25', '14:50'],
         'desc': '금산읍 ↔ 진산·건천리'},
 '721': {'name': '721번',
         'category': '농어촌버스',
         'region': '진산(석막·건천리)방면',
         'stops': ['금산읍', '금성', '진산', '석막', '건천리'],
         'out_times': ['06:20'],
         'in_times': ['07:00'],
         'desc': '금산읍 ↔ 진산·석막·건천리 첫차 노선'},
 '730': {'name': '730번',
         'category': '농어촌버스',
         'region': '진산방면 대표노선',
         'stops': ['금산읍', '양촌', '금성', '상촌', '상탄', '엄정리', '부암', '진산', '복수', '마전'],
         'out_times': ['06:00', '14:20', '16:20', '17:25'],
         'in_times': ['06:30', '13:20', '15:05', '17:00', '17:50', '18:10'],
         'desc': '금산읍 ↔ 금성·상촌·상탄·엄정·진산·마전 주요 간선'},
 '740': {'name': '740번',
         'category': '농어촌버스',
         'region': '군북·마전·진산방면',
         'stops': ['금산읍', '구상리', '군북', '비례리', '마전', '복수', '진산'],
         'out_times': ['06:40', '07:35', '12:45'],
         'in_times': ['07:05', '07:55', '13:30'],
         'desc': '금산읍 ↔ 군북·마전·진산 순환 간선'},
 '750': {'name': '750번',
         'category': '농어촌버스',
         'region': '마전·장대리·진산방면',
         'stops': ['금산읍', '의총리', '새터', '하신', '추정', '마전', '장대리', '복수', '진산'],
         'out_times': ['11:40', '12:25', '13:10', '14:10'],
         'in_times': ['12:50', '14:35', '15:00'],
         'desc': '금산읍 ↔ 마전·장대리·못골·진산'},
 '760': {'name': '760번',
         'category': '농어촌버스',
         'region': '진산(태고사·도산)방면',
         'stops': ['금산읍', '양촌', '금성', '상탄', '원터', '마전', '진산', '태고사', '도산'],
         'out_times': ['06:50', '08:15', '09:30', '15:00', '15:40', '19:10'],
         'in_times': ['07:40', '08:20', '09:50', '10:55', '16:20', '17:10', '20:00'],
         'desc': '금산읍 ↔ 마전·진산·태고사·도산 주요 노선'},
 '800': {'name': '800번 (농어촌·공공형)',
         'category': '농어촌·공공형',
         'region': '복수방면',
         'stops': ['금산읍', '상지말', '알미', '만악', '초미동', '목소리', '복수'],
         'out_times': ['06:30', '10:10', '18:30'],
         'in_times': ['08:50', '11:05', '19:20'],
         'desc': '금산읍 ↔ 상지말·알미·초미동·목소리·복수면사무소'},
 '810': {'name': '810번',
         'category': '농어촌버스',
         'region': '진산·복수(신대·도산)방면',
         'stops': ['금산읍', '금성', '원터', '만악', '진산', '당디', '지방리', '도산', '백암', '신대(복수)', '마전'],
         'out_times': ['06:10', '08:10', '12:10', '13:40', '15:10', '18:05'],
         'in_times': ['07:15', '07:35', '09:30', '13:55', '15:55', '16:00', '19:20', '19:40'],
         'desc': '금산읍 ↔ 진산·당디·도산·백암·신대·마전 간선'},
 '900': {'name': '900번',
         'category': '농어촌버스',
         'region': '마전·대암리방면',
         'stops': ['금산읍', '의총리', '새터', '대암리', '하신', '추정', '마전'],
         'out_times': ['08:50', '09:35', '19:45'],
         'in_times': ['09:35', '20:05'],
         'desc': '금산읍 ↔ 대암리·하신·추정·마전'},
 '910': {'name': '910번',
         'category': '농어촌버스',
         'region': '초미동·마전·군북방면',
         'stops': ['금산읍', '금성', '초미동', '복수', '마전', '비례리', '신평', '서대리', '군북', '진산'],
         'out_times': ['08:50', '10:15', '11:30', '12:50', '16:40', '19:30'],
         'in_times': ['10:50', '11:20', '12:05', '13:50', '17:15', '20:00'],
         'desc': '금산읍 ↔ 초미동·마전·서대리·군북·진산'},
 '920': {'name': '920번',
         'category': '농어촌버스',
         'region': '마전·서대산방면 대표노선',
         'stops': ['금산읍', '의총리', '새터', '하신', '추정', '마전', '장대리', '자부리', '비례리', '신평', '성당리', '서대산', '군북'],
         'out_times': ['06:40', '07:00', '07:40', '10:00', '12:00', '16:00', '18:10'],
         'in_times': ['07:17',
                      '08:00',
                      '09:10',
                      '09:55',
                      '10:45',
                      '12:50',
                      '13:20',
                      '14:40',
                      '16:45',
                      '17:05',
                      '19:00'],
         'desc': '금산읍 ↔ 마전·성당리·서대산·군북 핵심 간선'},
 '930': {'name': '930번',
         'category': '농어촌버스',
         'region': '마전·군북·진산방면',
         'stops': ['금산읍', '대암리', '마전', '비례리', '신평', '서대리', '조정리', '동평', '군북', '진산', '건천리'],
         'out_times': ['11:00', '14:05', '17:30'],
         'in_times': ['11:50', '12:20', '15:10', '17:10', '17:40', '18:25'],
         'desc': '금산읍 ↔ 대암리·마전·군북·진산·건천리'},
 '940': {'name': '940번',
         'category': '농어촌버스',
         'region': '원터·마전방면',
         'stops': ['금산읍', '양촌', '금성', '원터', '진산', '복수', '마전'],
         'out_times': ['10:00'],
         'in_times': ['10:30', '10:50'],
         'desc': '금산읍 ↔ 원터·진산·마전'}}

OUTBOUND_RURAL = [{'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '신안사,화골,재두',
  'time': '06:00',
  'bus_no': '210'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,수통리,라천',
  'time': '06:00',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '상탄,진산',
  'time': '06:00',
  'bus_no': '730'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '사기소,신정,평대리',
  'time': '06:00',
  'bus_no': '540'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '석동,건천리,대양리',
  'time': '06:00',
  'bus_no': '630'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '성당리',
  'time': '06:40',
  'bus_no': '920'},
 {'category': '농어촌버스',
  'direction': '복수방면',
  'origin': '금산읍',
  'via_dest': '상지말,알미,못안, 둑실,초미동,목소리',
  'time': '06:30',
  'bus_no': '800'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '산안2,상곡2,보광리',
  'time': '06:00',
  'bus_no': '440'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,압수,어재리',
  'time': '06:10',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '도산,신대리,백암',
  'time': '06:10',
  'bus_no': '810'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신정,신동리',
  'time': '07:10',
  'bus_no': '530'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '광대정,흑암리,음대리,매곡리',
  'time': '06:20',
  'bus_no': '670'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전,군북,제원',
  'time': '07:55',
  'bus_no': '420'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '원골,용화,대산',
  'time': '06:05',
  'bus_no': '230'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '상평당,가덕',
  'time': '06:20',
  'bus_no': '360'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '석막,건천리',
  'time': '06:20',
  'bus_no': '721'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '음전,원동,평대리,사미리',
  'time': '08:30',
  'bus_no': '522'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '윗관운리,활골',
  'time': '08:10',
  'bus_no': '610'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전,태고사,도산',
  'time': '08:15',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '복수방면',
  'origin': '금산읍',
  'via_dest': '상지말,알미,못안, 둑실,초미동,목소리',
  'time': '10:10',
  'bus_no': '800'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '군북,마전,진산',
  'time': '06:40',
  'bus_no': '740'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '호미동,삼태리',
  'time': '07:15',
  'bus_no': '500'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '도산,가든',
  'time': '06:50',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신동,수천리',
  'time': '08:50',
  'bus_no': '550'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '석동,역평리',
  'time': '08:35',
  'bus_no': '640'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전,못골,대암리',
  'time': '08:50',
  'bus_no': '900'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '명곡리',
  'time': '07:15',
  'bus_no': '200'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '금고리,갈티,평촌',
  'time': '07:40',
  'bus_no': '340'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '엄정,석막',
  'time': '07:40',
  'bus_no': '710'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신정,신천',
  'time': '09:55',
  'bus_no': '510'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '양대,대양리,시장',
  'time': '10:10',
  'bus_no': '650'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '서대산',
  'time': '10:00',
  'bus_no': '920'},
 {'category': '농어촌버스',
  'direction': '복수방면',
  'origin': '금산읍',
  'via_dest': '상지말,알미,못안, 가칠리,둑실,초미동, 목소리',
  'time': '18:30',
  'bus_no': '800'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '가선리',
  'time': '07:40',
  'bus_no': '250'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,신촌,백암',
  'time': '08:25',
  'bus_no': '310'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '당디,신대',
  'time': '08:10',
  'bus_no': '810'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신정,사기소,시장',
  'time': '12:00',
  'bus_no': '540'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '석동,건천리,시장',
  'time': '11:40',
  'bus_no': '630'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전,군북',
  'time': '11:00',
  'bus_no': '930'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '산안2,상곡2,보광리',
  'time': '08:10',
  'bus_no': '440'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,수통리,예미2,물페기',
  'time': '08:35',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '상탄,도산,원터',
  'time': '09:30',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '평대,원동리,음대',
  'time': '12:20',
  'bus_no': '520'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '양대,활골,대양리,시장',
  'time': '13:05',
  'bus_no': '650'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전,못골,진산',
  'time': '11:40',
  'bus_no': '750'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '닥실,금성리,용화,천내',
  'time': '08:35',
  'bus_no': '220'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,상평당',
  'time': '08:40',
  'bus_no': '360'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '원터,마전',
  'time': '10:00',
  'bus_no': '940'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신정,구시장',
  'time': '14:00',
  'bus_no': '510'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '매곡,양대,대양리',
  'time': '13:50',
  'bus_no': '650'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '서대산',
  'time': '12:00',
  'bus_no': '920'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '메데기,대산',
  'time': '09:40',
  'bus_no': '430'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,어재리',
  'time': '09:00',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '만악,석막',
  'time': '11:30',
  'bus_no': '710'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신천,수천리',
  'time': '14:40',
  'bus_no': '550'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '매곡,윗관운리',
  'time': '14:35',
  'bus_no': '620'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '장대리,진산',
  'time': '13:10',
  'bus_no': '750'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '가선리',
  'time': '10:00',
  'bus_no': '250'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '수통리,관천,시장',
  'time': '10:15',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '원터,신대,도산',
  'time': '12:10',
  'bus_no': '810'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '평대,원동,음대리',
  'time': '15:50',
  'bus_no': '520'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '석동,역평리',
  'time': '15:20',
  'bus_no': '640'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '대암리,마전,군북',
  'time': '14:05',
  'bus_no': '930'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '명곡리',
  'time': '10:10',
  'bus_no': '200'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,백일사,갈티,가덕',
  'time': '10:30',
  'bus_no': '350'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '화림,진산',
  'time': '12:45',
  'bus_no': '740'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '구시장,신동',
  'time': '16:30',
  'bus_no': '530'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '시장,석동,역평리',
  'time': '16:30',
  'bus_no': '640'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '서대산',
  'time': '16:00',
  'bus_no': '920'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '용화,금성리,닥실',
  'time': '10:10',
  'bus_no': '220'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '신촌,어재리,이정리',
  'time': '11:10',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '건천리',
  'time': '13:30',
  'bus_no': '720'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '초현,원동',
  'time': '17:05',
  'bus_no': '520'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '양대,광대정,활골',
  'time': '17:50',
  'bus_no': '610'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '군북,진산,건천리',
  'time': '17:30',
  'bus_no': '930'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '군북,조정리',
  'time': '10:30',
  'bus_no': '420'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,백일사',
  'time': '12:20',
  'bus_no': '350'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '만악1,신대,도산',
  'time': '13:40',
  'bus_no': '810'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신정,사기소',
  'time': '18:15',
  'bus_no': '540'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '석동,건천리',
  'time': '18:10',
  'bus_no': '630'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '서대산',
  'time': '18:10',
  'bus_no': '920'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '산안2,상곡2,안보광리',
  'time': '11:45',
  'bus_no': '440'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,예미2,수통리',
  'time': '12:30',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '상촌,엄정리,진산',
  'time': '14:20',
  'bus_no': '730'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '덕천,평대,원동',
  'time': '18:50',
  'bus_no': '520'},
 {'category': '농어촌버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '양대,대양리',
  'time': '19:00',
  'bus_no': '650'},
 {'category': '농어촌버스',
  'direction': '마전방면',
  'origin': '금산읍',
  'via_dest': '마전',
  'time': '19:45',
  'bus_no': '900'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '용화,금성,천내',
  'time': '12:05',
  'bus_no': '230'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '라천,가덕,관천',
  'time': '13:20',
  'bus_no': '300'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '태고사,도산',
  'time': '15:00',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '남일방면',
  'origin': '금산읍',
  'via_dest': '신동',
  'time': '19:30',
  'bus_no': '530'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '가선리',
  'time': '13:00',
  'bus_no': '250'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,상평당',
  'time': '13:40',
  'bus_no': '360'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '가든,도산',
  'time': '15:40',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '명곡리',
  'time': '13:00',
  'bus_no': '200'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,백암,수통리',
  'time': '14:00',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '상탄,엄정리,목골',
  'time': '16:20',
  'bus_no': '730'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '메데기',
  'time': '13:30',
  'bus_no': '430'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '호미동',
  'time': '14:10',
  'bus_no': '500'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '석막리',
  'time': '17:00',
  'bus_no': '710'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '대산,신안사',
  'time': '13:50',
  'bus_no': '210'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,어재리',
  'time': '15:00',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '당디,지방리,신대',
  'time': '18:05',
  'bus_no': '810'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '서당골,와정',
  'time': '07:25',
  'bus_no': '102'},
 {'category': '농어촌버스',
  'direction': '초미동방면',
  'origin': '금산읍',
  'via_dest': '마전,서대리,군북',
  'time': '08:50',
  'bus_no': '910'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '용화,금성리',
  'time': '14:45',
  'bus_no': '220'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,갈티,백일사',
  'time': '15:30',
  'bus_no': '350'},
 {'category': '농어촌버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '도산',
  'time': '19:10',
  'bus_no': '760'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '어동골',
  'time': '08:10',
  'bus_no': '120'},
 {'category': '농어촌버스',
  'direction': '초미동방면',
  'origin': '금산읍',
  'via_dest': '초미동,마전',
  'time': '11:30',
  'bus_no': '910'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '천내',
  'time': '15:00',
  'bus_no': '240'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '이정리,물페기,신촌',
  'time': '16:00',
  'bus_no': '310'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '서당골',
  'time': '10:20',
  'bus_no': '100'},
 {'category': '농어촌버스',
  'direction': '초미동방면',
  'origin': '금산읍',
  'via_dest': '초미동,마전,진산',
  'time': '12:50',
  'bus_no': '910'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '군북',
  'time': '15:45',
  'bus_no': '420'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '삼태리,수통리',
  'time': '16:50',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '초현,부남, 장안리',
  'origin': '금산읍',
  'via_dest': '장안리',
  'time': '10:50',
  'bus_no': '560'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '와정,하금',
  'time': '11:05',
  'bus_no': '600'},
 {'category': '농어촌버스',
  'direction': '초미동방면',
  'origin': '금산읍',
  'via_dest': '초미동,마전',
  'time': '16:40',
  'bus_no': '910'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '가선리',
  'time': '16:10',
  'bus_no': '250'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '관천,상평당',
  'time': '17:40',
  'bus_no': '360'},
 {'category': '농어촌버스',
  'direction': '초현,부남, 장안리',
  'origin': '금산읍',
  'via_dest': '사미리,장안리',
  'time': '14:20',
  'bus_no': '560'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '서당골,어동골',
  'time': '12:10',
  'bus_no': '100'},
 {'category': '농어촌버스',
  'direction': '초미동방면',
  'origin': '금산읍',
  'via_dest': '초미동,마전',
  'time': '19:30',
  'bus_no': '910'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '윗배원이,명곡리',
  'time': '16:20',
  'bus_no': '200'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,압수,어재리',
  'time': '17:55',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '와정',
  'time': '14:00',
  'bus_no': '110'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '군북',
  'time': '16:30',
  'bus_no': '420'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '가덕,금고리,수통리',
  'time': '19:00',
  'bus_no': '330'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '새말,마수,파초,음전',
  'time': '06:10',
  'bus_no': '170'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '서당골',
  'time': '15:00',
  'bus_no': '100'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '산안2,상곡2,안보광리',
  'time': '17:40',
  'bus_no': '440'},
 {'category': '농어촌버스',
  'direction': '부리방면',
  'origin': '금산읍',
  'via_dest': '창평,어재리',
  'time': '19:25',
  'bus_no': '320'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '새말,마수,파초',
  'time': '09:40',
  'bus_no': '170'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '와정',
  'time': '16:35',
  'bus_no': '110'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '천내,닥실,금성리',
  'time': '18:15',
  'bus_no': '220'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '음전,장목골,두곡,마수,새말',
  'time': '12:35',
  'bus_no': '160'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '서당골,어동골',
  'time': '18:10',
  'bus_no': '100'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '가선리',
  'time': '18:40',
  'bus_no': '250'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '장목골,두곡,마수,새말',
  'time': '15:30',
  'bus_no': '160'},
 {'category': '농어촌버스',
  'direction': '와정,하금',
  'origin': '금산읍',
  'via_dest': '와정,하금',
  'time': '19:35',
  'bus_no': '600'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '대산,재두,화골,신안사',
  'time': '18:50',
  'bus_no': '210'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '파초,마수,새말',
  'time': '17:00',
  'bus_no': '170'},
 {'category': '농어촌버스',
  'direction': '대암리방면',
  'origin': '마전',
  'via_dest': '대암리',
  'time': '09:35',
  'bus_no': '900'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '산안2,보광리',
  'time': '19:00',
  'bus_no': '440'},
 {'category': '농어촌버스',
  'direction': '마수방면(금성면)',
  'origin': '금산읍',
  'via_dest': '내부리,마수,파초',
  'time': '18:30',
  'bus_no': '400'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '용화',
  'time': '19:20',
  'bus_no': '230'},
 {'category': '농어촌버스',
  'direction': '제원/군북방면',
  'origin': '금산읍',
  'via_dest': '명곡리',
  'time': '19:40',
  'bus_no': '200'},
 {'category': '농어촌버스',
  'direction': '오룡방면(금성면)',
  'origin': '금산읍',
  'via_dest': '장목골,오룡,상지말',
  'time': '06:20',
  'bus_no': '160'},
 {'category': '농어촌버스',
  'direction': '오룡방면(금성면)',
  'origin': '금산읍',
  'via_dest': '장목골,오룡,음전',
  'time': '08:30',
  'bus_no': '160'},
 {'category': '농어촌버스',
  'direction': '오룡방면(금성면)',
  'origin': '금산읍',
  'via_dest': '오룡,장목골',
  'time': '17:40',
  'bus_no': '150'},
 {'category': '농어촌버스',
  'direction': '내부리방면',
  'origin': '금산읍',
  'via_dest': '내부리',
  'time': '07:20',
  'bus_no': '400'},
 {'category': '농어촌버스',
  'direction': '내부리방면',
  'origin': '금산읍',
  'via_dest': '새터가마실,내부리,의총리,청용안',
  'time': '10:10',
  'bus_no': '410'},
 {'category': '농어촌버스',
  'direction': '내부리방면',
  'origin': '금산읍',
  'via_dest': '내부리',
  'time': '13:25',
  'bus_no': '400'},
 {'category': '농어촌버스',
  'direction': '내부리방면',
  'origin': '금산읍',
  'via_dest': '청용안,의총리,내부리,새터가마실',
  'time': '15:40',
  'bus_no': '410'},
 {'category': '농어촌버스',
  'direction': '상촌,상탄,엄정',
  'origin': '금산읍',
  'via_dest': '엄정,진산,석막리',
  'time': '07:40',
  'bus_no': '710'},
 {'category': '농어촌버스',
  'direction': '상촌,상탄,엄정',
  'origin': '금산읍',
  'via_dest': '상촌,엄정리,목골,진산',
  'time': '16:20',
  'bus_no': '730'},
 {'category': '농어촌버스',
  'direction': '상촌,상탄,엄정',
  'origin': '금산읍',
  'via_dest': '상탄,하엄정',
  'time': '18:40',
  'bus_no': '700'}]

INBOUND_RURAL = [{'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '06:25', 'via_dest': '원골 발 용화,대산경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '06:30', 'via_dest': '수통리 발 창평,라천경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '06:30', 'via_dest': '사기소 발 신정,평대경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '06:40', 'via_dest': '건천리 발 대양리경유 석동'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '07:00', 'via_dest': '건천리 발 진산(07:25),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '06:30', 'via_dest': '신안사 발 화골,재두경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '06:40', 'via_dest': '어재리 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '07:40', 'via_dest': '(신정경유)신동 발'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '06:40', 'via_dest': '광대정 발 흑암리,음대,매곡경유'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '08:30', 'via_dest': '석막 발 진산(08:50)'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '06:35', 'via_dest': '보광리발(산안,상곡경유),군북(07:05)'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '06:50', 'via_dest': '상평당 발 가덕경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '09:00', 'via_dest': '원동 발 평대,사미경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '09:10', 'via_dest': '(윗관운리경유)활골 발'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '12:20', 'via_dest': '석막 발 진산(12:50),마전'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '07:35', 'via_dest': '명곡리 발 제원(07:50)'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '07:30', 'via_dest': '호미동 발 삼태리경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '09:30', 'via_dest': '수천리 발 신동'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '09:10', 'via_dest': '역평 발 석동'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '14:25', 'via_dest': '건천리 발 진산(14:50),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '08:00', 'via_dest': '가선리 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '08:00', 'via_dest': '금고리 발 갈티,평촌(08:10),관천경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '10:25', 'via_dest': '신정 발 신천경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '10:50', 'via_dest': '대양리 발 양대,구시장'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '17:50', 'via_dest': '석막 발 진산(18:10),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '08:55', 'via_dest': '군북 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '09:00', 'via_dest': '신촌 발 창평,백암경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '12:40', 'via_dest': '사기소 발 구시장경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '12:30', 'via_dest': '건천리 발 석동,구시장'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '19:30', 'via_dest': '건천리 발 건천에서금산직진'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '09:00', 'via_dest': '금성리 발 용화1,2경유,천내경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '09:10', 'via_dest': '수통리 발 예미2,물페기,관천경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '12:50', 'via_dest': '원동 발 음대'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '14:10', 'via_dest': '(활골)대양리 발 양대,구시장'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '09:05', 'via_dest': '보광리 발 군북(09:20)'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '09:10', 'via_dest': '상평당 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '14:35', 'via_dest': '신정리 발 구시장'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '14:50', 'via_dest': '대양리 발 양대'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '10:10', 'via_dest': '메데기 발 군북(10:20) 대산경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '09:35', 'via_dest': '어재리 발 관천경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '15:25', 'via_dest': '수천리 발 신동'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '15:35', 'via_dest': '(매곡)윗관운리 발 양대'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '06:45', 'via_dest': '도산 발 백암,진산(07:15) 마전'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '10:30', 'via_dest': '가선리 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '10:55', 'via_dest': '수통발 관천,구시장경유'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '16:30', 'via_dest': '원동리 발 음대경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '15:55', 'via_dest': '역평 발 석동'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '07:40', 'via_dest': '도산 발 진산(08:00) 마전'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '10:30', 'via_dest': '명곡리 발 송림'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '11:05', 'via_dest': '백일사 발 갈티,가덕 창평'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '17:10', 'via_dest': '신동리 발'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '17:10', 'via_dest': '역평 발 석동'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '09:05', 'via_dest': '신대 발 진산(09:30),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '10:40', 'via_dest': '금성리 발 닥실경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '11:50', 'via_dest': '어재리발 이정리경유 관천'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '17:40', 'via_dest': '원동리 발'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '18:40', 'via_dest': '(광대정)활골 발 양대'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '09:30', 'via_dest': '도산 발 진산(09:50),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '11:10', 'via_dest': '조정리 발 군북경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '12:55', 'via_dest': '백일사 발 창평'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '18:55', 'via_dest': '(신정경유) 사기소 발'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '18:55', 'via_dest': '건천리 발 석동'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '10:35', 'via_dest': '도산 발 진산(10:55),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '12:35', 'via_dest': '금성리 발 닥실,천내경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '13:10', 'via_dest': '수통리 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '19:20', 'via_dest': '원동 발 평대경유'},
 {'category': '농어촌(종점발)', 'direction': '남이방면 ➡ 금산읍', 'time': '19:30', 'via_dest': '대양리 발 양대'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '13:10', 'via_dest': '신대 발 도산(13:35),진산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '13:00', 'via_dest': '보광리 발 군북경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '13:50', 'via_dest': '(라천가덕경유) 관천 발'},
 {'category': '농어촌(종점발)', 'direction': '남일방면 ➡ 금산읍', 'time': '20:00', 'via_dest': '신동리 발'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '14:45', 'via_dest': '신대 발 도산(15:10),진산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '13:25', 'via_dest': '가선리 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '14:20', 'via_dest': '상평당 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '16:00', 'via_dest': '도산 발 진산(16:20),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '13:25', 'via_dest': '명곡리 발 송림'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '14:30', 'via_dest': '호미동 발 황풍'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '16:50', 'via_dest': '도산 발 진산(17:10),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '14:05', 'via_dest': '메데기 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '14:50', 'via_dest': '수통리 발 창평'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '07:17', 'via_dest': '성당 발 마전까지'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '19:00', 'via_dest': '신대 발 진산(19:20),마전'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '14:30', 'via_dest': '신안사 발 대산경유'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '15:40', 'via_dest': '어재리 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '08:00', 'via_dest': '서대산 발 마전,군북'},
 {'category': '농어촌(종점발)', 'direction': '진산방면 ➡ 금산읍', 'time': '19:45', 'via_dest': '도산 발 진산(20:00),금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '15:10', 'via_dest': '용화2 발 금성리(15:15),올때용화로'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '16:05', 'via_dest': '백일사 발 창평'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '09:55', 'via_dest': '서대산 발 마전,군북'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '15:25', 'via_dest': '천내 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '16:40', 'via_dest': '신촌 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '10:45', 'via_dest': '서대산 발 마전,진산,금산'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '16:20', 'via_dest': '군북 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '17:35', 'via_dest': '수통리 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '07:40', 'via_dest': '서당골 발 와정경유'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '12:50', 'via_dest': '서대산 발 마전,금산'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '06:25', 'via_dest': '마수 파초,음전경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '16:35', 'via_dest': '가선리 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '18:20', 'via_dest': '상평당 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '14:40', 'via_dest': '서대산 발 마전,진산'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '06:40', 'via_dest': '장목골 발 오룡,상지말'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '08:25', 'via_dest': '어동골 발'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '16:50', 'via_dest': '명곡리 발 송림'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '18:35', 'via_dest': '어재리 발 창평'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '10:35', 'via_dest': '서당골 발'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '16:45', 'via_dest': '서대산 발 마전,금산'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '07:30', 'via_dest': '내부리 발'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '17:05', 'via_dest': '군북 발'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '19:40', 'via_dest': '수통리 발 관천'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '11:25', 'via_dest': '하금 발 와정'},
 {'category': '농어촌(종점발)', 'direction': '서대산 ➡ 금산', 'time': '19:00', 'via_dest': '서대산 발 마전,군북,내부리'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '08:50', 'via_dest': '장목골 발 오룡,음전경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '18:45', 'via_dest': '보광리 발 군북'},
 {'category': '농어촌(종점발)', 'direction': '부리방면 ➡ 금산읍', 'time': '19:55', 'via_dest': '어재리 발 창평'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '12:25', 'via_dest': '서당골 발 어동골경유'},
 {'category': '농어촌(종점발)',
  'direction': '장목골,오룡,내부,마수 ➡ 금산',
  'time': '10:20',
  'via_dest': '새터가마실 발 내부리,의총리,청용안경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '18:45', 'via_dest': '금성리 발 닥실경유'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '14:15', 'via_dest': '와정 발'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '12:50', 'via_dest': '마수 새말경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '19:05', 'via_dest': '가선리 발'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '15:20', 'via_dest': '서당골 발'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '13:40', 'via_dest': '내부리 발'},
 {'category': '농어촌(종점발)',
  'direction': '복수방면 ➡ 금산',
  'time': '08:50',
  'via_dest': '목소리,초미동, 둑실,가칠리,못안, 알미,상지말'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '19:30', 'via_dest': '신안사 발'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '16:50', 'via_dest': '와정 발'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '15:45', 'via_dest': '마수 새말경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '19:45', 'via_dest': '용화2 발'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '18:30', 'via_dest': '서당골 발 어동골경유'},
 {'category': '농어촌(종점발)', 'direction': '복수방면 ➡ 금산', 'time': '11:05', 'via_dest': '목소리,마전,초미동, 둑실,못안,알미,상지말'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '17:15', 'via_dest': '마수 새말경유'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '19:50', 'via_dest': '보광리 발 군북(20:02)'},
 {'category': '농어촌(종점발)', 'direction': '조정리 ➡ 금산', 'time': '11:10', 'via_dest': '조정리 발 군북'},
 {'category': '농어촌(종점발)', 'direction': '서당,어동,와정 ➡ 금산', 'time': '20:00', 'via_dest': '하금 발 와정'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '18:10', 'via_dest': '장목골 발'},
 {'category': '농어촌(종점발)', 'direction': '제원방면 ➡ 금산읍', 'time': '20:00', 'via_dest': '명곡리 발 송림'},
 {'category': '농어촌(종점발)', 'direction': '복수방면 ➡ 금산', 'time': '19:20', 'via_dest': '목소리,초미동,둑실, 못안,알미,상지말'},
 {'category': '농어촌(종점발)', 'direction': '장목골,오룡,내부,마수 ➡ 금산', 'time': '18:45', 'via_dest': '마수 파초경유'}]

HUB_SCHEDULES = [{'section': '마전 ➡ 금산읍', 'time': '07:35', 'bus_no': '810', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '07:35', 'bus_no': '740', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '08:20', 'bus_no': '420', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '07:00', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '07:15', 'bus_no': '810', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '06:30', 'bus_no': '730', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 초미동', 'time': '10:20', 'bus_no': '920', 'via_dest': '초미동,금산'},
 {'section': '마전 ➡ 장대리', 'time': '09:50', 'bus_no': '920', 'via_dest': '장대리'},
 {'section': '마전 ➡ 군북·천을리', 'time': '13:10', 'bus_no': '710', 'via_dest': '군북·천을리'},
 {'section': '군북 ➡ 마전', 'time': '07:05', 'bus_no': '740', 'via_dest': '마전'},
 {'section': '천을리 ➡ 마전', 'time': '13:50', 'bus_no': '710', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '08:20', 'bus_no': '760', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '08:35', 'bus_no': '760', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '08:30', 'bus_no': '920', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '07:40', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '08:00', 'bus_no': '760', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '07:25', 'bus_no': '720', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 초미동', 'time': '12:05', 'bus_no': '910', 'via_dest': '초미동,금산'},
 {'section': '마전 ➡ 장대리', 'time': '13:30', 'bus_no': '750', 'via_dest': '장대리'},
 {'section': '군북 ➡ 마전', 'time': '09:10', 'bus_no': '920', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '09:35', 'bus_no': '900', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '11:05', 'bus_no': '920', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '10:15', 'bus_no': '910', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '09:35', 'bus_no': '910', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '10:30', 'bus_no': '940', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '07:55', 'bus_no': '740', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 초미동', 'time': '17:15', 'bus_no': '910', 'via_dest': '초미동,금산'},
 {'section': '군북 ➡ 마전', 'time': '10:50', 'bus_no': '910', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '10:50', 'bus_no': '940', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '12:25', 'bus_no': '750', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '11:20', 'bus_no': '930', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '10:25', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '12:50', 'bus_no': '710', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '08:50', 'bus_no': '710', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 초미동', 'time': '20:00', 'bus_no': '910', 'via_dest': '초미동,금산'},
 {'section': '군북 ➡ 마전', 'time': '11:50', 'bus_no': '930', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '11:20', 'bus_no': '910', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '13:25', 'bus_no': '910', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '13:10', 'bus_no': '710', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '12:25', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '13:55', 'bus_no': '810', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '09:30', 'bus_no': '810', 'via_dest': '금산읍'},
 {'section': '군북 ➡ 마전', 'time': '15:10', 'bus_no': '930', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '12:20', 'bus_no': '930', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '14:10', 'bus_no': '750', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '14:35', 'bus_no': '930', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '14:20', 'bus_no': '810', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '14:35', 'bus_no': '750', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '09:50', 'bus_no': '760', 'via_dest': '금산읍'},
 {'section': '군북 ➡ 마전', 'time': '17:10', 'bus_no': '930', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '13:20', 'bus_no': '920', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '15:10', 'bus_no': '810', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '15:50', 'bus_no': '930', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '16:25', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '15:30', 'bus_no': '810', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '10:55', 'bus_no': '760', 'via_dest': '금산읍'},
 {'section': '군북 ➡ 마전', 'time': '18:25', 'bus_no': '930', 'via_dest': '마전'},
 {'section': '마전 ➡ 금산읍', 'time': '14:30', 'bus_no': '710', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '17:25', 'bus_no': '730', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '17:55', 'bus_no': '930', 'via_dest': '군북'},
 {'section': '마전 ➡ 서대산', 'time': '18:40', 'bus_no': '920', 'via_dest': '서대산'},
 {'section': '진산 ➡ 마전', 'time': '17:00', 'bus_no': '730', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '11:30', 'bus_no': '920', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '15:00', 'bus_no': '750', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 진산', 'time': '19:00', 'bus_no': '930', 'via_dest': '진산'},
 {'section': '마전 ➡ 군북', 'time': '19:25', 'bus_no': '920', 'via_dest': '군북'},
 {'section': '진산 ➡ 마전', 'time': '17:50', 'bus_no': '730', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '12:50', 'bus_no': '750', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '16:00', 'bus_no': '810', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 마전', 'time': '19:20', 'bus_no': '810', 'via_dest': '마전'},
 {'section': '진산 ➡ 금산읍', 'time': '13:20', 'bus_no': '730', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '17:05', 'bus_no': '920', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '13:50', 'bus_no': '910', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '17:40', 'bus_no': '930', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '14:50', 'bus_no': '720', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '18:10', 'bus_no': '730', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '15:05', 'bus_no': '730', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '19:40', 'bus_no': '810', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '15:55', 'bus_no': '810', 'via_dest': '금산읍'},
 {'section': '마전 ➡ 금산읍', 'time': '20:05', 'bus_no': '900', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '16:20', 'bus_no': '760', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '17:10', 'bus_no': '760', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '18:10', 'bus_no': '710', 'via_dest': '금산읍'},
 {'section': '진산 ➡ 금산읍', 'time': '20:00', 'bus_no': '760', 'via_dest': '금산읍'}]

PUB_OUTBOUND = [{'category': '공공형버스',
  'direction': '서남부터미널(진산발)',
  'origin': '서남부터미널',
  'via_dest': '당디,행정,지방, 신대,지량,안영',
  'time': '07:00',
  'bus_no': '81'},
 {'category': '공공형버스',
  'direction': '서남부터미널(진산발)',
  'origin': '서남부터미널',
  'via_dest': '당디,행정,지방, 신대,지량,안영',
  'time': '10:25',
  'bus_no': '81'},
 {'category': '공공형버스',
  'direction': '서남부터미널(진산발)',
  'origin': '서남부터미널',
  'via_dest': '당디,행정,지방, 신대,지량,안영',
  'time': '13:55',
  'bus_no': '81'},
 {'category': '공공형버스',
  'direction': '서남부터미널(진산발)',
  'origin': '서남부터미널',
  'via_dest': '당디,행정,지방, 신대,지량,안영',
  'time': '16:40',
  'bus_no': '81'},
 {'category': '공공형버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '금성면,원터',
  'time': '06:30',
  'bus_no': '73'},
 {'category': '공공형버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '읍내,파초,초미동',
  'time': '07:00',
  'bus_no': '77'},
 {'category': '공공형버스',
  'direction': '진산방면',
  'origin': '금산읍',
  'via_dest': '읍내,파초,초미동',
  'time': '17:50',
  'bus_no': '77'},
 {'category': '공공형버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '읍내,석동, 자연휴양림',
  'time': '09:20',
  'bus_no': '68'},
 {'category': '공공형버스',
  'direction': '남이방면',
  'origin': '금산읍',
  'via_dest': '읍내,석동, 자연휴양림',
  'time': '14:40',
  'bus_no': '68'},
 {'category': '공공형버스',
  'direction': '오룡방면',
  'origin': '금산읍',
  'via_dest': '읍내, 상지말,알미',
  'time': '12:40',
  'bus_no': '15'},
 {'category': '공공형버스',
  'direction': '복수면사무소(금산발)',
  'origin': '금산읍',
  'via_dest': '우체국,상지말,알미,못안,둑실,만악,용지,목소리,중두문',
  'time': '06:30',
  'bus_no': '800'},
 {'category': '공공형버스',
  'direction': '복수면사무소(금산발)',
  'origin': '금산읍',
  'via_dest': '우체국,상지말,알미,못안,둑실,만악,용지,목소리,중두문',
  'time': '18:30',
  'bus_no': '800'},
 {'category': '공공형버스',
  'direction': '진산방면(복수면사무소발)',
  'origin': '복수면사무소',
  'via_dest': '곡남,수영,복수중,백암,구례,신대',
  'time': '07:40',
  'bus_no': '71'},
 {'category': '공공형버스',
  'direction': '진산방면(금산발)',
  'origin': '금산읍',
  'via_dest': '우체국,양전,원터,만악,부암',
  'time': '10:20',
  'bus_no': '72'},
 {'category': '공공형버스',
  'direction': '진산방면(금산발)',
  'origin': '금산읍',
  'via_dest': '우체국,양전,원터,만악,부암',
  'time': '13:10',
  'bus_no': '72'},
 {'category': '공공형버스',
  'direction': '진산방면(금산발)',
  'origin': '금산읍',
  'via_dest': '곡남,수영,복수중,백암,구례,신대',
  'time': '14:20',
  'bus_no': '70'},
 {'category': '공공형버스',
  'direction': '진산방면(금산발)',
  'origin': '금산읍',
  'via_dest': '곡남,수영,복수중,백암,구례,신대',
  'time': '15:30',
  'bus_no': '70'},
 {'category': '공공형버스',
  'direction': '진산방면(금산발)',
  'origin': '금산읍',
  'via_dest': '곡남,수영,복수중,백암,구례,신대',
  'time': '16:40',
  'bus_no': '70'}]

PUB_INBOUND = [{'category': '공공형(종점발)',
  'direction': '서남부터미널➡진산',
  'time': '08:45',
  'via_dest': '서남부터미널 발, 안영,지량,신대,지방,행정,묵산'},
 {'category': '공공형(종점발)',
  'direction': '서남부터미널➡진산',
  'time': '12:30',
  'via_dest': '서남부터미널 발, 안영,지량,신대,지방,행정,묵산'},
 {'category': '공공형(종점발)',
  'direction': '서남부터미널➡진산',
  'time': '15:20',
  'via_dest': '서남부터미널 발, 안영,지량,신대,지방,행정,묵산'},
 {'category': '공공형(종점발)',
  'direction': '서남부터미널➡진산',
  'time': '18:40',
  'via_dest': '서남부터미널 발, 안영,지량,신대,지방,행정,묵산'},
 {'category': '공공형(종점발)', 'direction': '진산방면➡금산', 'time': '08:05', 'via_dest': '진산 발 초미동,파초,읍내경유'},
 {'category': '공공형(종점발)', 'direction': '진산방면➡금산', 'time': '18:45', 'via_dest': '진산 발 초미동,파초,읍내경유'},
 {'category': '공공형(종점발)', 'direction': '진산방면➡금산', 'time': '19:50', 'via_dest': '진산 발 원터,금성면'},
 {'category': '공공형(종점발)', 'direction': '남이방면➡금산', 'time': '10:50', 'via_dest': '남이자연휴양림 발 건천,석동,읍내경유'},
 {'category': '공공형(종점발)', 'direction': '남이방면➡금산', 'time': '16:10', 'via_dest': '남이자연휴양림 발 건천,석동,읍내경유'},
 {'category': '공공형(종점발)', 'direction': '오룡방면➡금산', 'time': '13:35', 'via_dest': '오룡 발 알미,상지말,읍내경유'},
 {'category': '공공형(종점발)',
  'direction': '복수면사무소➡금산읍',
  'time': '08:50',
  'via_dest': '중두문,목소리,용지,만악,둑실,못안,알미,상지말,우체국'},
 {'category': '공공형(종점발)',
  'direction': '복수면사무소➡금산읍',
  'time': '19:20',
  'via_dest': '서남부터미널 발, 안영,지량,신대,지방,행정,묵산'},
 {'category': '공공형(종점발)', 'direction': '진산➡복수면사무소', 'time': '08:25', 'via_dest': '읍내,곡남'},
 {'category': '공공형(종점발)', 'direction': '진산➡금산읍', 'time': '11:10', 'via_dest': '부암,만악,원터,양전,우체국'},
 {'category': '공공형(종점발)', 'direction': '진산➡금산읍', 'time': '17:30', 'via_dest': '부암,만악,원터,양전,우체국'},
 {'category': '공공형(종점발)', 'direction': '복수(신대)➡진산면', 'time': '14:50', 'via_dest': '신대,구례,백암,복수중,수영,곡남'},
 {'category': '공공형(종점발)', 'direction': '복수(신대)➡진산면', 'time': '16:00', 'via_dest': '신대,구례,백암,복수중,수영,곡남'},
 {'category': '공공형(종점발)', 'direction': '복수(신대)➡진산면', 'time': '17:00', 'via_dest': '신대,구례,백암,복수중,수영,곡남'}]

DAEJEON_34_META = {
    "bus_no": "34",
    "title": "대전광역시 외곽버스 34번",
    "operator": "대전버스 (인가대수 4대)",
    "interval": "40~55분 간격 (일 22회 운행)",
    "first_last": "첫차 06:00 · 막차 22:00 (양방향 동일)",
    "basis_date": "2026년 2월 26일 기준",
    "start_desc": "[출발] 대전 중구 유천동(서남부터미널기점) / [도착] 산성동(서남부터미널종점)",
    "end_desc": "충남 금산군 진산면 묵산리 (대둔산휴게소 · 배티재)",
}

# 첨부 4.2 시간표 (총 22회: 서남부터미널 출발 / 대둔산휴게소 출발)
DAEJEON_34_TIMETABLE = [
    {"seq": 1,  "seonambu": "06:00", "daedunsan": "06:00"},
    {"seq": 2,  "seonambu": "06:45", "daedunsan": "06:35"},
    {"seq": 3,  "seonambu": "07:30", "daedunsan": "07:15"},
    {"seq": 4,  "seonambu": "08:10", "daedunsan": "07:50"},
    {"seq": 5,  "seonambu": "09:00", "daedunsan": "08:40"},
    {"seq": 6,  "seonambu": "09:45", "daedunsan": "09:20"},
    {"seq": 7,  "seonambu": "10:40", "daedunsan": "10:05"},
    {"seq": 8,  "seonambu": "11:20", "daedunsan": "10:50"},
    {"seq": 9,  "seonambu": "12:10", "daedunsan": "11:45"},
    {"seq": 10, "seonambu": "12:55", "daedunsan": "12:30"},
    {"seq": 11, "seonambu": "13:40", "daedunsan": "13:20"},
    {"seq": 12, "seonambu": "14:30", "daedunsan": "14:10"},
    {"seq": 13, "seonambu": "15:15", "daedunsan": "14:55"},
    {"seq": 14, "seonambu": "16:00", "daedunsan": "15:45"},
    {"seq": 15, "seonambu": "16:55", "daedunsan": "16:35"},
    {"seq": 16, "seonambu": "17:45", "daedunsan": "17:20"},
    {"seq": 17, "seonambu": "18:35", "daedunsan": "18:10"},
    {"seq": 18, "seonambu": "19:20", "daedunsan": "19:05"},
    {"seq": 19, "seonambu": "20:00", "daedunsan": "19:50"},
    {"seq": 20, "seonambu": "20:40", "daedunsan": "20:35"},
    {"seq": 21, "seonambu": "21:20", "daedunsan": "21:20"},
    {"seq": 22, "seonambu": "22:00", "daedunsan": "22:00"},
]

# 첨부 정류장 표 전체 반영 (서남부터미널기점 ➔ 대둔산휴게소 / 대둔산휴게소 ➔ 서남부터미널종점)
# offset_min: 기점 출발 후 평균 통과 소요분(약 52분 코스), zone: 구역 표시
DAEJEON_34_STOPS_TO_DAEDUN = [
    {"name": "서남부터미널기점", "id": "21660", "zone": "대전 중구", "hub": True,  "min": 0},
    {"name": "버드내아파트",     "id": "21680", "zone": "대전 중구", "hub": False, "min": 2},
    {"name": "서부종합시장",     "id": "21690", "zone": "대전 중구", "hub": False, "min": 3},
    {"name": "대전서남부터미널", "id": "22370", "zone": "대전 중구", "hub": True,  "min": 5},
    {"name": "머티네거리",       "id": "22320", "zone": "대전 중구", "hub": False, "min": 6},
    {"name": "산성동행정복지센터", "id": "22300", "zone": "대전 중구", "hub": False, "min": 8},
    {"name": "산성네거리",       "id": "22280", "zone": "대전 중구", "hub": False, "min": 9},
    {"name": "산성초등학교",     "id": "22570", "zone": "대전 중구", "hub": False, "min": 11},
    {"name": "사정동",           "id": "22550", "zone": "대전 중구", "hub": False, "min": 12},
    {"name": "우남스타원아파트", "id": "22500", "zone": "대전 중구", "hub": False, "min": 14},
    {"name": "농산물유통센터",   "id": "22460", "zone": "대전 중구", "hub": False, "min": 15},
    {"name": "안영생활체육단지", "id": "22680", "zone": "대전 중구", "hub": False, "min": 17},
    {"name": "한빛고교",         "id": "22670", "zone": "대전 중구", "hub": True,  "min": 18},
    {"name": "안영동검바위마을", "id": "22700", "zone": "대전 중구", "hub": False, "min": 20},
    {"name": "샛고개",           "id": "23520", "zone": "대전·금산 경계", "hub": False, "min": 21},
    {"name": "한마음아파트",     "id": "74170", "zone": "금산 복수면", "hub": False, "min": 23},
    {"name": "구만리",           "id": "74230", "zone": "금산 복수면", "hub": True,  "min": 24},
    {"name": "부대앞",           "id": "74110", "zone": "금산 복수면", "hub": False, "min": 26},
    {"name": "지량리",           "id": "74070", "zone": "금산 복수면", "hub": False, "min": 27},
    {"name": "둥구나무집",       "id": "74090", "zone": "금산 복수면", "hub": False, "min": 28},
    {"name": "지량1리",          "id": "74010", "zone": "금산 복수면", "hub": False, "min": 29},
    {"name": "압재",             "id": "74030", "zone": "금산 복수면", "hub": False, "min": 31},
    {"name": "신대2리",          "id": "74130", "zone": "금산 복수면", "hub": False, "min": 32},
    {"name": "신대3리",          "id": "74140", "zone": "금산 복수면", "hub": False, "min": 33},
    {"name": "신대1리",          "id": "74190", "zone": "금산 복수면", "hub": False, "min": 35},
    {"name": "신대초등학교",     "id": "74240", "zone": "금산 복수면", "hub": True,  "min": 36},
    {"name": "구례2리",          "id": "74300", "zone": "금산 복수면", "hub": False, "min": 37},
    {"name": "구례1리",          "id": "74270", "zone": "금산 복수면", "hub": False, "min": 38},
    {"name": "구례3리",          "id": "74320", "zone": "금산 복수면", "hub": False, "min": 39},
    {"name": "운곡마을",         "id": "74340", "zone": "금산 복수면", "hub": False, "min": 40},
    {"name": "백암리",           "id": "74210", "zone": "금산 복수면", "hub": False, "min": 41},
    {"name": "수영2리",          "id": "74370", "zone": "금산 복수면", "hub": False, "min": 42},
    {"name": "복수중학교",       "id": "74380", "zone": "금산 복수면", "hub": True,  "min": 43},
    {"name": "수영3리",          "id": "74400", "zone": "금산 복수면", "hub": False, "min": 44},
    {"name": "수영1리",          "id": "74420", "zone": "금산 복수면", "hub": False, "min": 45},
    {"name": "복수면사무소",     "id": "74440", "zone": "금산 복수면", "hub": True,  "min": 46},
    {"name": "곡남리종점",       "id": "74460", "zone": "금산 복수면", "hub": False, "min": 47},
    {"name": "곡남삼거리",       "id": "74550", "zone": "금산 복수면", "hub": False, "min": 48},
    {"name": "교촌리모랭이골",   "id": "74590", "zone": "금산 진산면", "hub": False, "min": 49},
    {"name": "교촌1리",          "id": "74570", "zone": "금산 진산면", "hub": False, "min": 50},
    {"name": "방축리",           "id": "74610", "zone": "금산 진산면", "hub": False, "min": 51},
    {"name": "진산면사무소",     "id": "74630", "zone": "금산 진산면", "hub": True,  "min": 53},
    {"name": "진산",             "id": "74650", "zone": "금산 진산면", "hub": True,  "min": 54},
    {"name": "원묵산",           "id": "74680", "zone": "금산 진산면", "hub": False, "min": 56},
    {"name": "대둔산눈썰매장",   "id": "74690", "zone": "금산 진산면", "hub": False, "min": 58},
    {"name": "대둔산휴게소",     "id": "74700", "zone": "금산 진산면", "hub": True,  "min": 60},
]

DAEJEON_34_STOPS_TO_DAEJEON = [
    {"name": "대둔산휴게소",     "id": "74700", "zone": "금산 진산면", "hub": True,  "min": 0},
    {"name": "대둔산눈썰매장",   "id": "3061",  "zone": "금산 진산면", "hub": False, "min": 2},
    {"name": "원묵산",           "id": "3059",  "zone": "금산 진산면", "hub": False, "min": 4},
    {"name": "진산",             "id": "74650", "zone": "금산 진산면", "hub": True,  "min": 6},
    {"name": "진산면사무소",     "id": "74640", "zone": "금산 진산면", "hub": True,  "min": 7},
    {"name": "방축리",           "id": "74620", "zone": "금산 진산면", "hub": False, "min": 9},
    {"name": "교촌1리",          "id": "74580", "zone": "금산 진산면", "hub": False, "min": 10},
    {"name": "교촌리모랭이골",   "id": "74600", "zone": "금산 진산면", "hub": False, "min": 11},
    {"name": "곡남삼거리",       "id": "74560", "zone": "금산 복수면", "hub": False, "min": 12},
    {"name": "곡남리종점",       "id": "74470", "zone": "금산 복수면", "hub": False, "min": 13},
    {"name": "복수면사무소",     "id": "74450", "zone": "금산 복수면", "hub": True,  "min": 14},
    {"name": "수영1리",          "id": "74430", "zone": "금산 복수면", "hub": False, "min": 15},
    {"name": "수영3리",          "id": "74410", "zone": "금산 복수면", "hub": False, "min": 16},
    {"name": "복수중학교",       "id": "74390", "zone": "금산 복수면", "hub": True,  "min": 17},
    {"name": "수영2리",          "id": "74360", "zone": "금산 복수면", "hub": False, "min": 18},
    {"name": "백암리",           "id": "74220", "zone": "금산 복수면", "hub": False, "min": 19},
    {"name": "운곡마을",         "id": "74350", "zone": "금산 복수면", "hub": False, "min": 20},
    {"name": "구례3리",          "id": "74330", "zone": "금산 복수면", "hub": False, "min": 21},
    {"name": "구례1리",          "id": "74280", "zone": "금산 복수면", "hub": False, "min": 22},
    {"name": "구례2리",          "id": "74310", "zone": "금산 복수면", "hub": False, "min": 23},
    {"name": "신대초등학교",     "id": "74260", "zone": "금산 복수면", "hub": True,  "min": 24},
    {"name": "신대1리",          "id": "74200", "zone": "금산 복수면", "hub": False, "min": 25},
    {"name": "신대3리",          "id": "74160", "zone": "금산 복수면", "hub": False, "min": 27},
    {"name": "신대2리",          "id": "74150", "zone": "금산 복수면", "hub": False, "min": 28},
    {"name": "신대",             "id": "74060", "zone": "금산 복수면", "hub": False, "min": 29},
    {"name": "압재",             "id": "74040", "zone": "금산 복수면", "hub": False, "min": 30},
    {"name": "지량1리",          "id": "74020", "zone": "금산 복수면", "hub": False, "min": 31},
    {"name": "둥구나무집",       "id": "74100", "zone": "금산 복수면", "hub": False, "min": 32},
    {"name": "지량리",           "id": "74080", "zone": "금산 복수면", "hub": False, "min": 33},
    {"name": "부대앞",           "id": "74120", "zone": "금산 복수면", "hub": False, "min": 34},
    {"name": "구만리",           "id": "74250", "zone": "금산 복수면", "hub": True,  "min": 36},
    {"name": "한마음아파트",     "id": "74180", "zone": "금산 복수면", "hub": False, "min": 37},
    {"name": "샛고개",           "id": "22730", "zone": "대전·금산 경계", "hub": False, "min": 39},
    {"name": "안영동검바위마을", "id": "22710", "zone": "대전 중구", "hub": False, "min": 40},
    {"name": "한빛고교",         "id": "22660", "zone": "대전 중구", "hub": True,  "min": 42},
    {"name": "안영생활체육단지", "id": "22690", "zone": "대전 중구", "hub": False, "min": 43},
    {"name": "농산물유통센터",   "id": "22470", "zone": "대전 중구", "hub": False, "min": 45},
    {"name": "우남스타원아파트", "id": "22520", "zone": "대전 중구", "hub": False, "min": 46},
    {"name": "사정동",           "id": "22560", "zone": "대전 중구", "hub": False, "min": 48},
    {"name": "산성초등학교",     "id": "22580", "zone": "대전 중구", "hub": False, "min": 49},
    {"name": "산성네거리",       "id": "22290", "zone": "대전 중구", "hub": False, "min": 51},
    {"name": "산성시장",         "id": "22310", "zone": "대전 중구", "hub": True,  "min": 53},
    {"name": "서남부터미널종점", "id": "21670", "zone": "대전 중구", "hub": True,  "min": 57},
]


# =============================================================================
# 정직한 공식 시간표 기반 계산 함수 (가짜 GPS · 가짜 도로정체 제거)
# =============================================================================

MAJOR_HUBS = ["금산읍", "진산", "마전", "복수", "금성", "군북", "제원", "부리", "하금", "남일(초현)"]

QUICK_GEUMSAN_PRESETS = [
    {"label": "🏡 진산 ➔ 금산읍", "origin": "진산", "dest": "금산읍"},
    {"label": "🏡 금산읍 ➔ 진산", "origin": "금산읍", "dest": "진산"},
    {"label": "🏥 마전 ➔ 금산읍", "origin": "마전", "dest": "금산읍"},
    {"label": "🌿 금산읍 ➔ 수통리", "origin": "금산읍", "dest": "수통리"},
]

QUICK_DJ34_PRESETS = [
    {"label": "⬆️ 진산 ➔ 대전 서남부터미널", "dir": "to_daejeon", "origin": "진산", "dest": "서남부터미널종점"},
    {"label": "⬆️ 복수면사무소 ➔ 대전 서남부터미널", "dir": "to_daejeon", "origin": "복수면사무소", "dest": "서남부터미널종점"},
    {"label": "⬇️ 대전서남부터미널 ➔ 복수면사무소", "dir": "to_daedun", "origin": "대전서남부터미널", "dest": "복수면사무소"},
    {"label": "⬇️ 대전서남부터미널 ➔ 진산", "dir": "to_daedun", "origin": "대전서남부터미널", "dest": "진산"},
]


def get_kst_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul"))


def parse_hhmm_to_min(hhmm: str) -> int:
    h, m = hhmm.strip().split(":")
    return int(h) * 60 + int(m)


def min_to_hhmm(total_min: int) -> str:
    m = total_min % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def format_remain_str(diff_min: int) -> str:
    if diff_min <= 0:
        return "곧 출발"
    if diff_min < 60:
        return f"{diff_min}분 남음"
    h, m = divmod(diff_min, 60)
    return f"{h}시간 {m}분 남음" if m else f"{h}시간 남음"


def estimate_segment_min(u: str, v: str) -> int:
    """노선도 거리 기반 정류장 간 평균 이동시간(분) 단순 추정"""
    if u == v:
        return 0
    nu, nv = NODES.get(u), NODES.get(v)
    if not nu or not nv:
        return 4
    dist = math.hypot(nu["x"] - nv["x"], nu["y"] - nv["y"])
    return int(max(2, min(7, round(dist * 0.38))))


def get_sorted_stops() -> list[str]:
    hubs = [h for h in MAJOR_HUBS if h in NODES]
    others = sorted(s for s in NODES if s not in hubs)
    return hubs + others


def get_reachable_stops(origin: str) -> set[str]:
    reach = set()
    for info in BUS_ROUTES.values():
        stops = info["stops"]
        if origin in stops:
            for s in stops:
                if s != origin:
                    reach.add(s)
    return reach


def format_stop_option(stop_name: str, direct_set: set[str] | None = None) -> str:
    reg = NODES[stop_name]["region"]
    prefix = "⭐ " if NODES[stop_name]["hub"] else ""
    if direct_set is not None:
        tag = " · 직통" if stop_name in direct_set else " · 환승"
        return f"{prefix}{stop_name} ({reg}{tag})"
    return f"{prefix}{stop_name} ({reg})"


def evaluate_geumsan_route(bus_no: str, origin: str, dest: str, now_min: int) -> dict | None:
    """출발지->도착지를 잇는 직통 노선의 공식 기점 출발 시각 및 예상 소요시간 계산"""
    info = BUS_ROUTES[bus_no]
    stops = info["stops"]
    if origin not in stops or dest not in stops or origin == dest:
        return None

    idx_o = stops.index(origin)
    idx_d = stops.index(dest)

    if idx_o < idx_d:
        active_stops = stops
        raw_times = info["out_times"]
    else:
        active_stops = list(reversed(stops))
        raw_times = info["in_times"] if info["in_times"] else info["out_times"]

    o_pos = active_stops.index(origin)
    d_pos = active_stops.index(dest)
    start_terminal = active_stops[0]
    end_terminal = active_stops[-1]

    # 기점->승차 정류장 평균 소요시간, 승차->하차 평균 이동시간
    offset_to_origin = sum(
        estimate_segment_min(active_stops[i], active_stops[i + 1]) for i in range(o_pos)
    )
    ride_min = sum(
        estimate_segment_min(active_stops[i], active_stops[i + 1]) for i in range(o_pos, d_pos)
    )

    sched_entries = sorted(
        [(parse_hhmm_to_min(t), t) for t in raw_times],
        key=lambda x: x[0],
    )
    if not sched_entries:
        return None

    # 내 정류장 예상 통과 시각(기점 출발 + offset_to_origin) 기준으로 아직 안 지나간 다음 차 탐색
    upcoming = []
    for dep_m, dep_str in sched_entries:
        est_board_m = dep_m + offset_to_origin
        if est_board_m >= now_min:
            upcoming.append((dep_m, dep_str, est_board_m))

    first_dep_m, first_dep_str = sched_entries[0]
    if upcoming:
        next_dep_m, next_dep_str, next_board_m = upcoming[0]
        wait_from_now = next_board_m - now_min
        dep_diff_from_now = next_dep_m - now_min
        rem_count = len(upcoming)
        is_ended = False
        if rem_count == 1:
            lb_level, lb_badge = "last", "🚨 오늘 마지막 차(막차)"
        elif rem_count == 2:
            lb_level, lb_badge = "warn", "⏰ 막차 1대 전"
        else:
            lb_level, lb_badge = "ok", f"오늘 {rem_count}회 남음"
    else:
        next_dep_m = first_dep_m
        next_dep_str = first_dep_str
        next_board_m = first_dep_m + offset_to_origin
        wait_from_now = (24 * 60 - now_min) + next_board_m
        dep_diff_from_now = (24 * 60 - now_min) + first_dep_m
        rem_count = 0
        is_ended = True
        lb_level, lb_badge = "ended", f"🌙 오늘 운행 종료 (첫차 {first_dep_str})"

    return {
        "bus_no": bus_no,
        "name": info["name"],
        "category": info["category"],
        "region": info["region"],
        "desc": info["desc"],
        "start_terminal": start_terminal,
        "end_terminal": end_terminal,
        "active_stops": active_stops,
        "offset_to_origin": offset_to_origin,
        "ride_min": ride_min,
        "all_dep_times": [s for _, s in sched_entries],
        "next_dep_m": next_dep_m,
        "next_dep_str": next_dep_str,
        "next_board_m": next_board_m,
        "next_board_str": min_to_hhmm(next_board_m),
        "est_alight_str": min_to_hhmm(next_board_m + ride_min),
        "wait_from_now": wait_from_now,
        "dep_diff_from_now": dep_diff_from_now,
        "rem_count": rem_count,
        "is_ended": is_ended,
        "lb_level": lb_level,
        "lb_badge": lb_badge,
    }


def find_all_geumsan_options(origin: str, dest: str, now_min: int) -> list[dict]:
    results = []
    for bno in BUS_ROUTES:
        ev = evaluate_geumsan_route(bno, origin, dest, now_min)
        if ev is not None:
            results.append(ev)
    # 오늘 운행 중인 버스 우선 -> 내 정류장 예상 도착이 빠른 순
    results.sort(key=lambda x: (1 if x["is_ended"] else 0, x["wait_from_now"], x["ride_min"]))
    return results


def find_simple_transfer(origin: str, dest: str, now_min: int) -> dict | None:
    """직통이 없을 때 주요 거점(금산읍·진산·마전·복수 등) 1회 환승 탐색"""
    best = None
    for hub in MAJOR_HUBS:
        if hub in (origin, dest) or hub not in NODES:
            continue
        leg1_list = find_all_geumsan_options(origin, hub, now_min)
        leg2_list = find_all_geumsan_options(hub, dest, now_min)
        if leg1_list and leg2_list:
            l1, l2 = leg1_list[0], leg2_list[0]
            score = l1["wait_from_now"] + l1["ride_min"] + l2["ride_min"]
            if best is None or score < best["score"]:
                best = {"hub": hub, "leg1": l1, "leg2": l2, "score": score}
    return best


def evaluate_daejeon_34(direction_key: str, origin_name: str, dest_name: str, now_min: int) -> dict:
    """대전 외곽버스 34번 공식 기점 시간표 기반 계산"""
    to_daedun = direction_key == "to_daedun"
    stops = DAEJEON_34_STOPS_TO_DAEDUN if to_daedun else DAEJEON_34_STOPS_TO_DAEJEON
    col_key = "seonambu" if to_daedun else "daedunsan"
    start_terminal = "서남부터미널기점" if to_daedun else "대둔산휴게소"
    dir_title = "대전 서남부터미널 ➔ 복수 · 진산 · 대둔산" if to_daedun else "대둔산 · 진산 · 복수 ➔ 대전 서남부터미널"

    names = [s["name"] for s in stops]
    idx_o = names.index(origin_name) if origin_name in names else 0
    idx_d = names.index(dest_name) if dest_name in names else len(stops) - 1
    if idx_d <= idx_o:
        idx_d = min(len(stops) - 1, idx_o + 1)

    o_item = stops[idx_o]
    d_item = stops[idx_d]
    offset_o = o_item["min"]
    ride_min = max(2, d_item["min"] - o_item["min"])

    dep_times = [row[col_key] for row in DAEJEON_34_TIMETABLE]
    sched_entries = [(parse_hhmm_to_min(t), t) for t in dep_times]

    upcoming = []
    for dep_m, dep_str in sched_entries:
        est_board_m = dep_m + offset_o
        if est_board_m >= now_min:
            upcoming.append((dep_m, dep_str, est_board_m))

    first_dep_m, first_dep_str = sched_entries[0]
    if upcoming:
        next_dep_m, next_dep_str, next_board_m = upcoming[0]
        wait_from_now = next_board_m - now_min
        rem_count = len(upcoming)
        is_ended = False
        if rem_count == 1:
            lb_level, lb_badge = "last", "🚨 오늘 마지막 34번(막차)"
        elif rem_count == 2:
            lb_level, lb_badge = "warn", "⏰ 막차 1대 전"
        else:
            lb_level, lb_badge = "ok", f"오늘 {rem_count}회 남음"
    else:
        next_dep_m = first_dep_m
        next_dep_str = first_dep_str
        next_board_m = first_dep_m + offset_o
        wait_from_now = (24 * 60 - now_min) + next_board_m
        rem_count = 0
        is_ended = True
        lb_level, lb_badge = "ended", f"🌙 오늘 운행 종료 (첫차 {first_dep_str})"

    return {
        "dir_title": dir_title,
        "start_terminal": start_terminal,
        "stops": stops,
        "origin_item": o_item,
        "dest_item": d_item,
        "offset_o": offset_o,
        "ride_min": ride_min,
        "dep_times": dep_times,
        "next_dep_str": next_dep_str,
        "next_board_str": min_to_hhmm(next_board_m),
        "est_alight_str": min_to_hhmm(next_board_m + ride_min),
        "wait_from_now": wait_from_now,
        "rem_count": rem_count,
        "is_ended": is_ended,
        "lb_level": lb_level,
        "lb_badge": lb_badge,
    }


def _embed_html(html_code: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_code, height=height)
    else:
        components.html(html_code, height=height, scrolling=False)


def render_family_sms(message: str) -> None:
    body = quote("[금산 붕붕이] " + message + " (공식 시간표 기준)", safe="")
    _embed_html(f"""
    <a id="family-sms" href="sms:?body={body}" style="display:inline-block;padding:10px 14px;
      border:1px solid #CBD5E1;border-radius:12px;color:#1E293B;background:#fff;
      font:700 15px system-ui;text-decoration:none">💬 엄마한테 문자 보내기</a>
    <script>
      if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {{
        document.getElementById('family-sms').setAttribute('href', 'sms:&body={body}');
      }}
    </script>
    """, height=54)


def render_tts_button(tts_text: str) -> None:
    """어르신용 깔끔한 한국어 음성 안내 버튼"""
    safe_json = json.dumps(tts_text, ensure_ascii=False)
    code = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; font-family: 'Pretendard', 'Malgun Gothic', sans-serif; }}
  body {{ margin: 0; padding: 0; background: transparent; }}
  .wrap {{ display: flex; gap: 8px; align-items: center; }}
  .btn-play {{
    flex: 1; background: #1D4ED8; color: #fff; border: none; border-radius: 12px;
    padding: 12px 16px; font-size: 1rem; font-weight: 800; cursor: pointer;
  }}
  .btn-stop {{
    background: #F1F5F9; color: #334155; border: 1.5px solid #CBD5E1; border-radius: 12px;
    padding: 12px 14px; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  }}
</style></head>
<body>
  <div class="wrap">
    <button class="btn-play" id="playBtn" onclick="speakBus()">🔊 소리로 안내 듣기</button>
    <button class="btn-stop" onclick="stopBus()">⏹️ 멈춤</button>
  </div>
  <script>
    const msgText = {safe_json};
    function speakBus() {{
      if (!('speechSynthesis' in window)) {{
        alert('이 브라우저에서는 음성 안내를 지원하지 않습니다.');
        return;
      }}
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(msgText);
      u.lang = 'ko-KR';
      u.rate = 0.92;
      const btn = document.getElementById('playBtn');
      u.onstart = () => {{ btn.innerText = '🔊 안내 읽는 중...'; }};
      u.onend = () => {{ btn.innerText = '🔊 소리로 안내 듣기'; }};
      u.onerror = () => {{ btn.innerText = '🔊 소리로 안내 듣기'; }};
      window.speechSynthesis.speak(u);
    }}
    function stopBus() {{
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      document.getElementById('playBtn').innerText = '🔊 소리로 안내 듣기';
    }}
  </script>
</body></html>"""
    _embed_html(code, height=54)


def render_time_badges(times: list[str], offset_min: int, now_min: int, accent_green: bool = False) -> str:
    """오늘 출발 시간표를 지난 차 / 다음 차 / 이후 차 / 막차 배지로 깔끔하게 표시"""
    chips = []
    marked_next = False
    for idx, t_str in enumerate(times):
        dep_m = parse_hhmm_to_min(t_str)
        board_m = dep_m + offset_min
        is_last = idx == len(times) - 1
        if board_m >= now_min and not marked_next:
            marked_next = True
            cls = "t-next-green" if accent_green else "t-next-blue"
            suffix = " · 막차" if is_last else " · 다음차"
            chips.append(f"<span class='t-chip {cls}'>🚌 {t_str}{suffix}</span>")
        elif board_m < now_min:
            chips.append(f"<span class='t-chip t-past'>{t_str}</span>")
        elif is_last:
            chips.append(f"<span class='t-chip t-last'>{t_str} (막차)</span>")
        else:
            chips.append(f"<span class='t-chip t-future'>{t_str}</span>")
    return "".join(chips)


# =============================================================================
# 세션 상태 초기화 (단순 · 명확)
# =============================================================================

if "tab" not in st.session_state:
    st.session_state.tab = "geumsan"
if "g_origin" not in st.session_state:
    st.session_state.g_origin = "금산읍"
if "g_dest" not in st.session_state:
    st.session_state.g_dest = "진산"
if "dj_dir" not in st.session_state:
    st.session_state.dj_dir = "to_daejeon"
if "dj_origin" not in st.session_state:
    st.session_state.dj_origin = "진산"
if "dj_dest" not in st.session_state:
    st.session_state.dj_dest = "서남부터미널종점"
if "large_text" not in st.session_state:
    st.session_state.large_text = False
if "show_dj_stops" not in st.session_state:
    st.session_state.show_dj_stops = False


def set_tab(tab_name: str) -> None:
    st.session_state.tab = tab_name


def set_geumsan_pair(o: str, d: str) -> None:
    st.session_state.tab = "geumsan"
    st.session_state.g_origin = o
    st.session_state.g_dest = d


def swap_geumsan_pair() -> None:
    st.session_state.g_origin, st.session_state.g_dest = (
        st.session_state.g_dest,
        st.session_state.g_origin,
    )


def set_dj34_dir(d_key: str) -> None:
    st.session_state.dj_dir = d_key
    if d_key == "to_daejeon":
        st.session_state.dj_origin = "진산"
        st.session_state.dj_dest = "서남부터미널종점"
    else:
        st.session_state.dj_origin = "대전서남부터미널"
        st.session_state.dj_dest = "진산"


def set_dj34_preset(d_key: str, o: str, d: str) -> None:
    st.session_state.tab = "dj34"
    st.session_state.dj_dir = d_key
    st.session_state.dj_origin = o
    st.session_state.dj_dest = d


# =============================================================================
# 심플 & 모바일 고가독성 스타일 (사이드바 숨김 · 큰 터치 버튼)
# =============================================================================

base_zoom = "1.12rem" if st.session_state.large_text else "1.0rem"

st.markdown(
    f"""
<style>
  /* 불필요한 좌측 사이드바 버튼 숨김 -> 완벽한 단일 화면 */
  [data-testid="stSidebar"], [data-testid="collapsedControl"] {{
      display: none !important;
  }}
  html, body, [class*="css"] {{
      font-size: {base_zoom};
      font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
  }}
  .block-container {{
      padding-top: 1.4rem !important;
      padding-bottom: 3rem !important;
      max-width: 760px !important;
  }}
  /* 모든 버튼을 휴대폰 엄지로 누르기 편한 사이트 버튼으로 통일 */
  div.stButton > button {{
      min-height: 50px !important;
      border-radius: 14px !important;
      font-weight: 800 !important;
      font-size: 0.98rem !important;
      padding: 0.55rem 0.9rem !important;
      transition: all 0.12s ease !important;
  }}
  div.stButton > button[kind="secondary"] {{
      background: #FFFFFF !important;
      border: 1.5px solid #CBD5E1 !important;
      color: #1E293B !important;
  }}
  div.stButton > button[kind="secondary"]:hover {{
      border-color: #2563EB !important;
      color: #2563EB !important;
      background: #EFF6FF !important;
  }}
  div.stButton > button[kind="primary"] {{
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22) !important;
  }}
  :is(.st-key-nav_geumsan,.st-key-nav_dj34,.st-key-nav_taxi) div.stButton > button {{
      min-height: 94px !important;
      border-radius: 21px !important;
      padding: 0.6rem 0.45rem !important;
  }}
  :is(.st-key-nav_geumsan,.st-key-nav_dj34,.st-key-nav_taxi) div.stButton p {{
      line-height: 1.23 !important;
      font-weight: 800 !important;
      text-align: center;
  }}
  :is(.st-key-nav_geumsan,.st-key-nav_dj34,.st-key-nav_taxi) div.stButton p::first-line {{
      font-size: 2rem;
  }}
  :is(.st-key-nav_geumsan,.st-key-nav_dj34,.st-key-nav_taxi) button[kind="primary"] {{
      background: #1D4ED8 !important;
      color: white !important;
      border-color: #1D4ED8 !important;
  }}
  :is(.st-key-gps_34310,.st-key-gps_25) div.stButton > button[kind="secondary"] {{
      background: #ECFDF5 !important;
      color: #065F46 !important;
      border-color: #6EE7B7 !important;
  }}
  div.stButton > button:focus-visible {{ outline: 3px solid #2563EB; outline-offset: 2px; }}
  div.stButton > button:active {{ transform: scale(0.98); }}
  /* 모바일에서도 상단 2열 버튼이 세로로 깨지지 않게 유지 */
  @media (max-width: 640px) {{
      div[data-testid="stHorizontalBlock"] {{
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: wrap !important;
          gap: 8px !important;
      }}
      div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
          flex: 1 1 calc(50% - 8px) !important;
          min-width: 140px !important;
      }}
  }}
  .app-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
  }}
  .app-title {{
      font-size: 1.35rem;
      font-weight: 900;
      color: #0F172A;
      letter-spacing: -0.02em;
  }}
  .clock-pill {{
      background: #F1F5F9;
      color: #334155;
      border-radius: 999px;
      padding: 5px 12px;
      font-size: 0.85rem;
      font-weight: 800;
  }}
  .main-card {{
      background: #FFFFFF;
      border: 2px solid #2563EB;
      border-radius: 20px;
      padding: 20px 22px;
      box-shadow: 0 6px 20px rgba(37, 99, 235, 0.08);
      margin: 10px 0 12px 0;
  }}
  .main-card-green {{
      background: #FFFFFF;
      border: 2px solid #16A34A;
      border-radius: 20px;
      padding: 20px 22px;
      box-shadow: 0 6px 20px rgba(22, 163, 74, 0.09);
      margin: 10px 0 12px 0;
  }}
  .sub-card {{
      background: #FFFFFF;
      border: 1.5px solid #E2E8F0;
      border-radius: 16px;
      padding: 16px 18px;
      margin-bottom: 12px;
  }}
  .big-time {{
      font-size: 2.1rem;
      font-weight: 900;
      color: #1D4ED8;
      line-height: 1.15;
  }}
  .big-time-green {{
      font-size: 2.1rem;
      font-weight: 900;
      color: #15803D;
      line-height: 1.15;
  }}
  .badge-ok {{ background:#DCFCE7; color:#166534; padding:5px 11px; border-radius:999px; font-size:0.84rem; font-weight:800; }}
  .badge-warn {{ background:#FEF3C7; color:#92400E; padding:5px 11px; border-radius:999px; font-size:0.84rem; font-weight:800; }}
  .badge-last {{ background:#FEE2E2; color:#B91C1C; padding:5px 11px; border-radius:999px; font-size:0.84rem; font-weight:900; }}
  .badge-ended {{ background:#E2E8F0; color:#475569; padding:5px 11px; border-radius:999px; font-size:0.84rem; font-weight:800; }}
  .t-chip {{
      display: inline-block;
      padding: 7px 12px;
      border-radius: 10px;
      font-weight: 800;
      font-size: 0.94rem;
      margin: 4px 4px 4px 0;
  }}
  .t-past {{ background: #F1F5F9; color: #94A3B8; text-decoration: line-through; font-weight: 600; }}
  .t-next-blue {{ background: #2563EB; color: #FFFFFF; }}
  .t-next-green {{ background: #16A34A; color: #FFFFFF; }}
  .t-future {{ background: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; }}
  .t-last {{ background: #FEF2F2; color: #DC2626; border: 1.5px solid #FCA5A5; }}
  .honest-note {{
      font-size: 0.82rem;
      color: #64748B;
      margin-top: 8px;
  }}
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# 상단 제목 + 큰 글씨 스위치 + 사이트 메뉴 버튼 2개
# =============================================================================

now_dt = get_kst_now()
now_min = now_dt.hour * 60 + now_dt.minute

h_col1, h_col2 = st.columns([3.4, 1.3])
with h_col1:
    st.markdown(
        f"""
<div class="app-header">
  <style>
.bb-brand-row{{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap}}
.bb-brand-icon{{display:grid;place-items:center;width:44px;height:44px;background:#1d4ed8;border-radius:13px;flex:none}}
.bb-brand-icon svg{{width:30px;height:30px}}
.bb-bus-track{{margin:6px auto 0;width:104px;border-bottom:2px dashed #93b4da;text-align:left}}
.bb-moving-bus{{display:inline-block;font-size:23px;animation:bb-drive 2.1s ease-in-out infinite alternate}}
@keyframes bb-drive{{from{{transform:translateX(70px)}}to{{transform:translateX(0)}}}}
@media(prefers-reduced-motion:reduce){{.bb-moving-bus{{animation:none}}}}
</style>
  <div class="app-title bb-brand-row"><span class="bb-brand-icon" aria-hidden="true"><svg width="56" height="56" viewBox="0 0 56 56" fill="none">
    <rect x="9" y="6" width="38" height="42" rx="10" fill="#fff"/>
    <rect x="14" y="13" width="28" height="16" rx="4" fill="#bfdbfe"/>
    <path d="M28 13v16" stroke="#fff" stroke-width="2"/>
    <circle cx="18" cy="37" r="3" fill="#1d4ed8"/><circle cx="38" cy="37" r="3" fill="#1d4ed8"/>
    <path d="M16 46v5m24-5v5" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
  </svg></span><span>금산 붕붕이</span></div>
  <div class="bb-bus-track" aria-hidden="true"><span class="bb-moving-bus">🚌</span></div>
  <span class="clock-pill">현재 {now_dt.strftime('%H:%M')}</span>
</div>
""",
        unsafe_allow_html=True,
    )
with h_col2:
    st.session_state.large_text = st.toggle("🔍 큰 글씨", value=st.session_state.large_text)

# 최상단 사이트 메뉴 탭 버튼 딱 2개!
menu_c1, menu_c2, menu_c3 = st.columns(3)
with menu_c1:
    st.button(
        "🚌  \n금산 버스",
        key="nav_geumsan",
        type="primary" if st.session_state.tab == "geumsan" else "secondary",
        on_click=set_tab,
        args=("geumsan",),
        **STRETCH_KW,
    )
with menu_c2:
    st.button(
        "🚍  \n대전 34번",
        key="nav_dj34",
        type="primary" if st.session_state.tab == "dj34" else "secondary",
        on_click=set_tab,
        args=("dj34",),
        **STRETCH_KW,
    )

with menu_c3:
    st.button("🚕  \n택시 비교", key="nav_taxi",
              type="primary" if st.session_state.tab == "taxi" else "secondary",
              on_click=set_tab, args=("taxi",), **STRETCH_KW)


# =============================================================================
# [화면 1] 🔵 금산 군내 · 공공형 버스 (출발·도착만 고르면 끝!)
# =============================================================================
if st.session_state.tab == "taxi":
    show_taxi_comparison()
elif st.session_state.tab == "geumsan":
    st.caption("자주 타는 구간을 누르거나 아래에서 출발지·도착지만 고르세요. 버스 번호를 몰라도 다음 차를 바로 찾아줍니다.")

    # 자주 타는 구간 원터치 버튼 4개
    qp1, qp2, qp3, qp4 = st.columns(4)
    for col_q, item in zip((qp1, qp2, qp3, qp4), QUICK_GEUMSAN_PRESETS):
        with col_q:
            is_active_preset = (
                st.session_state.g_origin == item["origin"]
                and st.session_state.g_dest == item["dest"]
            )
            st.button(
                item["label"],
                key=f"q_g_{item['origin']}_{item['dest']}",
                type="primary" if is_active_preset else "secondary",
                on_click=set_geumsan_pair,
                args=(item["origin"], item["dest"]),
                **STRETCH_KW,
            )

    all_stops = get_sorted_stops()

    # 단순 2칸 선택 + 맞바꾸기 버튼
    sel_c1, sel_c2, sel_c3 = st.columns([2.2, 2.2, 1.0])
    with sel_c1:
        o_idx = all_stops.index(st.session_state.g_origin) if st.session_state.g_origin in all_stops else 0
        picked_o = st.selectbox(
            "출발 정류장",
            options=all_stops,
            index=o_idx,
            format_func=lambda s: format_stop_option(s),
        )
        if picked_o != st.session_state.g_origin:
            st.session_state.g_origin = picked_o
            if st.session_state.g_dest == picked_o:
                st.session_state.g_dest = "진산" if picked_o != "진산" else "금산읍"
            st.rerun()

    with sel_c2:
        reach_set = get_reachable_stops(st.session_state.g_origin)
        dest_candidates = (
            [s for s in all_stops if s != st.session_state.g_origin and s in reach_set]
            + [s for s in all_stops if s != st.session_state.g_origin and s not in reach_set]
        )
        d_idx = (
            dest_candidates.index(st.session_state.g_dest)
            if st.session_state.g_dest in dest_candidates
            else 0
        )
        picked_d = st.selectbox(
            "도착 정류장",
            options=dest_candidates,
            index=d_idx,
            format_func=lambda s: format_stop_option(s, reach_set),
        )
        if picked_d != st.session_state.g_dest:
            st.session_state.g_dest = picked_d
            st.rerun()

    with sel_c3:
        st.write("")
        st.button("🔄 바꾸기", key="btn_swap_g", on_click=swap_geumsan_pair, **STRETCH_KW)

    g_origin = st.session_state.g_origin
    g_dest = st.session_state.g_dest

    # 진산·복수 등 34번 정차 지역이면 대전 34번 바로가기 한 줄 안내
    if g_origin in ("진산", "복수", "구만리", "신대", "백암리", "배티재(대둔산)") or g_dest in (
        "진산", "복수", "구만리", "신대", "백암리", "배티재(대둔산)"
    ):
        b_c1, b_c2 = st.columns([3.2, 1.3])
        b_c1.info("💡 **복수 · 진산 · 대둔산 ↔ 대전 서남부터미널**은 **대전 34번 버스(일 22회)**가 가장 자주 다닙니다.")
        b_c2.button("🟢 34번 보기", key="jump_34_tip", on_click=set_tab, args=("dj34",), **STRETCH_KW)

    options = find_all_geumsan_options(g_origin, g_dest, now_min)

    if options:
        best = options[0]
        show_gps(34310, GEUMSAN_TAGO_ROUTES.get(best["bus_no"], []), best["bus_no"])
        b_cls = (
            "badge-last"
            if best["lb_level"] == "last"
            else ("badge-ended" if best["lb_level"] == "ended" else ("badge-warn" if best["lb_level"] == "warn" else "badge-ok"))
        )

        if best["is_ended"]:
            headline_time = f"내일 첫차 {best['next_board_str']}경"
            remain_line = f"오늘 버스가 모두 끝났습니다 · 기점({best['start_terminal']}) 첫차 {best['next_dep_str']} 출발"
        elif best["offset_to_origin"] == 0:
            headline_time = f"{best['next_dep_str']} 출발 ({format_remain_str(best['wait_from_now'])})"
            remain_line = f"{g_origin} 기점 정각 출발 · {g_dest}까지 약 {best['ride_min']}분 소요"
        else:
            headline_time = f"약 {best['next_board_str']} 도착 예정 ({format_remain_str(best['wait_from_now'])})"
            remain_line = (
                f"기점({best['start_terminal']}) {best['next_dep_str']} 공식 출발 "
                f"(+{best['offset_to_origin']}분 후 통과 예상) · 이동 약 {best['ride_min']}분"
            )

        st.markdown(
            f"""
<div class="main-card">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
    <div style="font-size:1.15rem; font-weight:900; color:#0F172A;">
      🚌 가장 빠른 차: <span style="color:#2563EB;">{html.escape(best['name'])}</span>
      <span style="font-size:0.9rem; font-weight:700; color:#64748B;">({html.escape(g_origin)} ➔ {html.escape(g_dest)})</span>
    </div>
    <span class="{b_cls}">{html.escape(best['lb_badge'])}</span>
  </div>
  <div class="big-time">{headline_time}</div>
  <div style="font-size:0.95rem; font-weight:700; color:#334155; margin-top:6px;">
    {html.escape(remain_line)}
  </div>
  <div class="honest-note">
    ※ 실시간 GPS가 아닌 <b>2026. 7. 1 시행 금산군 공식 기점 시간표</b> 기준 안내입니다. 중간 정류장은 도로 사정에 따라 5분가량 차이가 날 수 있으니 조금 일찍 나와 주세요.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # 음성 안내 버튼
        if best["is_ended"]:
            tts_msg = (
                f"{g_origin}에서 {g_dest} 가는 오늘 버스는 운행이 종료되었습니다. "
                f"내일 첫차는 {best['bus_no']}번이며 기점에서 {best['next_dep_str']}에 출발합니다."
            )
        else:
            tts_msg = (
                f"{g_origin}에서 {g_dest} 가는 가장 빠른 버스는 {best['bus_no']}번입니다. "
                f"기점인 {best['start_terminal']}에서 {best['next_dep_str']}에 출발하며, "
                f"{g_origin} 정류장에는 약 {best['wait_from_now']}분 뒤인 {best['next_board_str']} 무렵 도착할 예정입니다. "
                f"{best['lb_badge']}."
            )
        render_tts_button(tts_msg)
        render_family_sms(tts_msg)

        # 해당 구간을 운행하는 전체 직통 노선별 오늘 시간표 한눈에 표시
        st.markdown(f"#### 📅 `{g_origin} ➔ {g_dest}` 운행 버스 시간표 ({len(options)}개 노선)")
        for opt in options:
            chips_html = render_time_badges(opt["all_dep_times"], opt["offset_to_origin"], now_min, accent_green=False)
            note_offset = (
                f"{opt['start_terminal']} 기점 출발 시각"
                if opt["offset_to_origin"] == 0
                else f"{opt['start_terminal']} 기점 출발 시각 (`{g_origin}`까지 평균 +{opt['offset_to_origin']}분)"
            )
            st.markdown(
                f"""
<div class="sub-card">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
    <div>
      <b style="font-size:1.05rem; color:#0F172A;">🚌 {html.escape(opt['name'])}</b>
      <span style="font-size:0.86rem; color:#64748B;"> · {html.escape(opt['desc'])}</span>
    </div>
    <span style="font-size:0.84rem; font-weight:800; color:#1D4ED8;">{html.escape(opt['lb_badge'])}</span>
  </div>
  <div style="font-size:0.83rem; color:#64748B; margin-bottom:6px;">📍 {html.escape(note_offset)}</div>
  <div>{chips_html}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            with st.expander(f"🚏 {opt['bus_no']}번 경유 정류장 보기 ({len(opt['active_stops'])}곳)"):
                stop_labels = []
                for s_nm in opt["active_stops"]:
                    if s_nm == g_origin:
                        stop_labels.append(f"**🙋 {s_nm}(타는 곳)**")
                    elif s_nm == g_dest:
                        stop_labels.append(f"**🏁 {s_nm}(내리는 곳)**")
                    else:
                        stop_labels.append(s_nm)
                st.markdown(" ➔ ".join(stop_labels))

    else:
        tr = find_simple_transfer(g_origin, g_dest, now_min)
        if tr:
            st.warning(
                f"**`{g_origin} ➔ {g_dest}`** 한 번에 가는 직통 버스가 없습니다. "
                f"**`{tr['hub']}`**에서 갈아타시면 이동할 수 있습니다."
            )
            tc1, tc2 = st.columns(2)
            with tc1:
                st.button(
                    f"1구간: {g_origin} ➔ {tr['hub']} ({tr['leg1']['bus_no']}번)",
                    key="btn_tr_1",
                    on_click=set_geumsan_pair,
                    args=(g_origin, tr["hub"]),
                    **STRETCH_KW,
                )
            with tc2:
                st.button(
                    f"2구간: {tr['hub']} ➔ {g_dest} ({tr['leg2']['bus_no']}번)",
                    key="btn_tr_2",
                    on_click=set_geumsan_pair,
                    args=(tr["hub"], g_dest),
                    **STRETCH_KW,
                )
        else:
            st.warning("선택하신 구간을 연결하는 버스 노선이 없습니다.")


# =============================================================================
# [화면 2] 🟢 대전 외곽버스 34번 전용 안내 (서남부터미널 ↔ 복수 ↔ 진산 ↔ 대둔산)
# =============================================================================
else:
    st.caption(f"{DAEJEON_34_META['basis_date']} 공식 시간표 · 첫차 06:00 / 막차 22:00 · 일 22회 (40~55분 간격)")

    # 자주 타는 구간 원터치 버튼 4개
    dp1, dp2 = st.columns(2)
    with dp1:
        st.button(
            QUICK_DJ34_PRESETS[0]["label"],
            key="q_dj_0",
            type="primary"
            if (st.session_state.dj_dir == "to_daejeon" and st.session_state.dj_origin == "진산")
            else "secondary",
            on_click=set_dj34_preset,
            args=("to_daejeon", "진산", "서남부터미널종점"),
            **STRETCH_KW,
        )
    with dp2:
        st.button(
            QUICK_DJ34_PRESETS[1]["label"],
            key="q_dj_1",
            type="primary"
            if (st.session_state.dj_dir == "to_daejeon" and st.session_state.dj_origin == "복수면사무소")
            else "secondary",
            on_click=set_dj34_preset,
            args=("to_daejeon", "복수면사무소", "서남부터미널종점"),
            **STRETCH_KW,
        )

    dp3, dp4 = st.columns(2)
    with dp3:
        st.button(
            QUICK_DJ34_PRESETS[2]["label"],
            key="q_dj_2",
            type="primary"
            if (st.session_state.dj_dir == "to_daedun" and st.session_state.dj_dest == "복수면사무소")
            else "secondary",
            on_click=set_dj34_preset,
            args=("to_daedun", "대전서남부터미널", "복수면사무소"),
            **STRETCH_KW,
        )
    with dp4:
        st.button(
            QUICK_DJ34_PRESETS[3]["label"],
            key="q_dj_3",
            type="primary"
            if (st.session_state.dj_dir == "to_daedun" and st.session_state.dj_dest == "진산")
            else "secondary",
            on_click=set_dj34_preset,
            args=("to_daedun", "대전서남부터미널", "진산"),
            **STRETCH_KW,
        )

    # 방향 선택 큰 버튼 2개
    dir_b1, dir_b2 = st.columns(2)
    with dir_b1:
        st.button(
            "⬆️ 대전 방면",
            key="dj_dir_up",
            type="primary" if st.session_state.dj_dir == "to_daejeon" else "secondary",
            on_click=set_dj34_dir,
            args=("to_daejeon",),
            **STRETCH_KW,
        )
    with dir_b2:
        st.button(
            "⬇️ 대둔산 방면",
            key="dj_dir_down",
            type="primary" if st.session_state.dj_dir == "to_daedun" else "secondary",
            on_click=set_dj34_dir,
            args=("to_daedun",),
            **STRETCH_KW,
        )

    cur_stops_34 = (
        DAEJEON_34_STOPS_TO_DAEDUN
        if st.session_state.dj_dir == "to_daedun"
        else DAEJEON_34_STOPS_TO_DAEJEON
    )
    names_34 = [s["name"] for s in cur_stops_34]
    map_34 = {s["name"]: s for s in cur_stops_34}

    sc1, sc2 = st.columns(2)
    with sc1:
        b_opts = names_34[:-1]
        o_i = b_opts.index(st.session_state.dj_origin) if st.session_state.dj_origin in b_opts else 0
        sel_o = st.selectbox(
            "타는 정류장",
            options=b_opts,
            index=o_i,
            key=f"dj_o_{st.session_state.dj_dir}_{st.session_state.dj_origin}",
            format_func=lambda nm: f"{'⭐ ' if map_34[nm]['hub'] else ''}{nm} ({map_34[nm]['zone']})",
        )
        if sel_o != st.session_state.dj_origin:
            st.session_state.dj_origin = sel_o
            st.rerun()

    with sc2:
        after_i = names_34.index(st.session_state.dj_origin) + 1
        a_opts = names_34[after_i:]
        d_i = a_opts.index(st.session_state.dj_dest) if st.session_state.dj_dest in a_opts else len(a_opts) - 1
        sel_d = st.selectbox(
            "내리는 정류장",
            options=a_opts,
            index=d_i,
            key=f"dj_d_{st.session_state.dj_dir}_{st.session_state.dj_dest}",
            format_func=lambda nm: f"{'🏁 ' if map_34[nm]['hub'] else ''}{nm} ({map_34[nm]['zone']})",
        )
        if sel_d != st.session_state.dj_dest:
            st.session_state.dj_dest = sel_d
            st.rerun()

    dj_res = evaluate_daejeon_34(
        st.session_state.dj_dir,
        st.session_state.dj_origin,
        st.session_state.dj_dest,
        now_min,
    )

    show_gps(25, ["DJB30300016"], "34")
    b34_cls = (
        "badge-last"
        if dj_res["lb_level"] == "last"
        else ("badge-ended" if dj_res["lb_level"] == "ended" else ("badge-warn" if dj_res["lb_level"] == "warn" else "badge-ok"))
    )

    if dj_res["is_ended"]:
        head_34 = f"내일 첫차 {dj_res['next_board_str']}경"
        sub_34 = f"오늘 34번 운행이 끝났습니다 · 기점({dj_res['start_terminal']}) 첫차 06:00 출발"
    elif dj_res["offset_o"] == 0:
        head_34 = f"{dj_res['next_dep_str']} 출발 ({format_remain_str(dj_res['wait_from_now'])})"
        sub_34 = f"{dj_res['start_terminal']} 정각 출발 · {st.session_state.dj_dest}까지 약 {dj_res['ride_min']}분 소요"
    else:
        head_34 = f"약 {dj_res['next_board_str']} 도착 예정 ({format_remain_str(dj_res['wait_from_now'])})"
        sub_34 = (
            f"기점({dj_res['start_terminal']}) {dj_res['next_dep_str']} 공식 출발 "
            f"(+{dj_res['offset_o']}분 후 통과 예상) · 이동 약 {dj_res['ride_min']}분"
        )

    st.markdown(
        f"""
<div class="main-card-green">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
    <div style="font-size:1.15rem; font-weight:900; color:#14532D;">
      🟢 대전 34번 다음 버스
      <span style="font-size:0.9rem; font-weight:700; color:#475569;">({html.escape(st.session_state.dj_origin)} ➔ {html.escape(st.session_state.dj_dest)})</span>
    </div>
    <span class="{b34_cls}">{html.escape(dj_res['lb_badge'])}</span>
  </div>
  <div class="big-time-green">{head_34}</div>
  <div style="font-size:0.95rem; font-weight:700; color:#334155; margin-top:6px;">
    {html.escape(sub_34)}
  </div>
  <div class="honest-note">
    ※ 실시간 GPS가 아닌 <b>대전 34번 공식 기점 시간표({DAEJEON_34_META['basis_date']})</b> 기준 추정 시각입니다. 정류장 번호 <b>{dj_res['origin_item']['id']}</b>에서 조금 여유 있게 대기해 주세요.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    tts_34 = (
        f"대전 34번 버스 안내입니다. {dj_res['start_terminal']}에서 {dj_res['next_dep_str']}에 출발하는 차량이 "
        f"{st.session_state.dj_origin} 정류장에 약 {dj_res['wait_from_now']}분 뒤인 {dj_res['next_board_str']} 무렵 도착할 예정입니다. "
        f"{st.session_state.dj_dest}까지는 약 {dj_res['ride_min']}분 걸립니다. {dj_res['lb_badge']}."
    )
    render_tts_button(tts_34)
    render_family_sms(tts_34)

    # 양방향 공식 시간표 한 장에 깔끔하게 표시
    chips_to_dd = render_time_badges(
        [r["seonambu"] for r in DAEJEON_34_TIMETABLE],
        dj_res["offset_o"] if st.session_state.dj_dir == "to_daedun" else 0,
        now_min,
        accent_green=True,
    )
    chips_to_dj = render_time_badges(
        [r["daedunsan"] for r in DAEJEON_34_TIMETABLE],
        dj_res["offset_o"] if st.session_state.dj_dir == "to_daejeon" else 0,
        now_min,
        accent_green=True,
    )

    st.markdown(
        f"""
<div class="sub-card" style="margin-top:10px;">
  <div style="font-size:1.05rem; font-weight:900; color:#14532D; margin-bottom:10px;">
    📅 대전 34번 오늘 전체 시간표 (일 22회 · 기점 출발 시각)
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:0.9rem; font-weight:800; color:#166534; margin-bottom:4px;">
      ⬆️ 대둔산휴게소 출발 (진산 · 복수 ➔ 대전 서남부터미널 방면)
    </div>
    <div>{chips_to_dj}</div>
  </div>
  <div>
    <div style="font-size:0.9rem; font-weight:800; color:#166534; margin-bottom:4px;">
      ⬇️ 대전 서남부터미널 출발 (복수 · 진산 ➔ 대둔산휴게소 방면)
    </div>
    <div>{chips_to_dd}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # 전체 정류장 목록은 필요할 때만 펼쳐보기
    with st.expander(f"🚏 34번 전체 경유 정류장 · 정류장번호 보기 ({len(dj_res['stops'])}곳)"):
        rows_34 = []
        for idx_s, s_obj in enumerate(dj_res["stops"], start=1):
            mark = ""
            if s_obj["name"] == st.session_state.dj_origin:
                mark = "🙋 타는 곳"
            elif s_obj["name"] == st.session_state.dj_dest:
                mark = "🏁 내리는 곳"
            rows_34.append(
                {
                    "순서": idx_s,
                    "정류장명": s_obj["name"],
                    "정류장번호": s_obj["id"],
                    "지역": s_obj["zone"],
                    "기점 대비": f"+{s_obj['min']}분",
                    "표시": mark,
                }
            )
        st.dataframe(pd.DataFrame(rows_34), hide_index=True, **STRETCH_KW)
