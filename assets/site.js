// 다리 건너 낚시 · 공통 스크립트
// 1) 모든 페이지에서 쓰는 SVG 조각(거친 띠 필터, 다리 그림, 찌 아이콘)을 넣는다
// 2) 포인트 자료와 지도 그리기
// 3) 물때(지금은 예시 숫자) 그리기
{
  const defs = `
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <filter id="rough" x="-5%" y="-30%" width="110%" height="160%">
    <feTurbulence type="fractalNoise" baseFrequency="0.04 0.9" numOctaves="2" seed="3"/>
    <feDisplacementMap in="SourceGraphic" scale="14"/>
  </filter>
  <symbol id="bridge" viewBox="0 0 420 300"><g fill="none" stroke-linecap="round">
    <g stroke="#8EC5FF" stroke-width="3.5"><line x1="0" y1="200" x2="420" y2="200"/><line x1="130" y1="60" x2="130" y2="222"/><line x1="320" y1="60" x2="320" y2="222"/></g>
    <g stroke="#8EC5FF" stroke-width="1.2" opacity=".6">
      <line x1="130" y1="70" x2="40" y2="200"/><line x1="130" y1="80" x2="70" y2="200"/><line x1="130" y1="90" x2="100" y2="200"/>
      <line x1="130" y1="70" x2="220" y2="200"/><line x1="130" y1="80" x2="190" y2="200"/><line x1="130" y1="90" x2="160" y2="200"/>
      <line x1="320" y1="70" x2="230" y2="200"/><line x1="320" y1="80" x2="260" y2="200"/><line x1="320" y1="90" x2="290" y2="200"/>
      <line x1="320" y1="70" x2="410" y2="200"/><line x1="320" y1="80" x2="380" y2="200"/><line x1="320" y1="90" x2="350" y2="200"/>
    </g>
    <g fill="#CFE5FF" stroke="none"><circle cx="130" cy="60" r="3"/><circle cx="320" cy="60" r="3"/>
      <circle cx="40" cy="200" r="2"/><circle cx="100" cy="200" r="2"/><circle cx="160" cy="200" r="2"/><circle cx="220" cy="200" r="2"/>
      <circle cx="260" cy="200" r="2"/><circle cx="320" cy="200" r="2"/><circle cx="380" cy="200" r="2"/></g>
    <g stroke="#4DA3FF" stroke-width="1.5" opacity=".35">
      <path d="M0 240 Q 30 234 60 240 T 120 240 T 180 240 T 240 240 T 300 240 T 360 240 T 420 240"/>
      <path d="M20 262 Q 50 256 80 262 T 140 262 T 200 262 T 260 262 T 320 262 T 380 262" opacity=".6"/>
    </g></g></symbol>
  <symbol id="float" viewBox="0 0 20 70">
    <line x1="10" y1="0" x2="10" y2="22" stroke="#F6D89A" stroke-width="2.5"/>
    <ellipse cx="10" cy="40" rx="8" ry="20" fill="#FF8A3D"/><ellipse cx="10" cy="54" rx="8" ry="8" fill="#FFFFFF"/>
  </symbol>
</defs></svg>`;
  document.body.insertAdjacentHTML('afterbegin', defs);

  // 휴대폰 아래 메뉴 막대 (엄지로 누르기 쉽게)
  const inPoints = /\/points\/[^/]+$/.test(location.pathname.replace(/\\/g, '/'));
  const base = inPoints ? '../' : '';
  const file = location.pathname.split(/[\\/]/).pop() || 'index.html';
  const here = inPoints || file === 'points.html' ? 'points' : file === 'about.html' ? 'about' : file === 'index.html' || file === '' ? 'tide' : '';
  const ico = {
    tide: '<path d="M2 15c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M2 20c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M12 3v7m-3-3 3 3 3-3"/>',
    points: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    about: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    blog: '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
  };
  const tab = (key, href, text) => `<a href="${href}"${here === key ? ' class="on" aria-current="page"' : ''}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ico[key]}</svg>${text}</a>`;
  document.body.insertAdjacentHTML('beforeend', `<nav class="tabbar" aria-label="메뉴">${tab('tide', base || './', '물때')}${tab('points', base + 'points.html', '포인트')}${tab('blog', 'https://blog.naver.com/manic31', '블로그')}${tab('about', base + 'about.html', '소개')}</nav>`);
}

// ── 포인트 자료 ─────────────────────────────────────────
// 블로그에 이미 공개한 내용만 넣는다. 위치를 아끼는 곳은 kind:'secret'(핀 대신 넓은 동그라미).
// lon/lat은 실제 좌표. 지금은 지명 기준 대략값이고, 네이버 지도 공유 링크를 받으면 그 좌표로 바꾼다.
// naver: 핀을 눌렀을 때 열 네이버 지도 링크(공유 링크 naver.me/... 를 받으면 교체). 비공개 포인트는 비워 둔다.
window.POINTS = [
  // 쪽실: 사용자가 좋아하는 자리(네이버 공유 링크). 양도면 길정리 977, '망실지'라고도 부름.
  { id: 'jjoksil', name: '쪽실수로', alias: '망실지', region: '강화 양도면 길정리', fish: '붕어', season: '가을', kind: 'open',
    tip: '수심 60~70cm · 가을엔 동물성 미끼 · 주차 자리 적어 새벽 일찍', lon: 126.4634, lat: 37.6375, dx: -9,  // 선두포와 400m 거리라 화면에서만 살짝 벌림
    naver: 'https://naver.me/5nhwwEgf' },
  // 선두포: 사용자가 준 네이버 공유 링크(앉던 자리)
  { id: 'seondupo', name: '선두포 수로', region: '강화 화도면', fish: '붕어', kind: 'closed',
    tip: '앉을 자리에 흙을 쌓아 막음 · 길 건너 쪽실수로로', lon: 126.4659, lat: 37.6344, dx: 9,
    naver: 'https://naver.me/GWWcc4Ap' },
  { id: 'seokmo-healing', name: '석모도 힐링 포인트', region: '석모도 어딘가', fish: '바다 · 붕어 · 배스', kind: 'secret',
    tip: '한자리에서 원투도, 수로 붕어도, 배스도', lon: 126.33, lat: 37.69 },
];
const toXY = (lon, lat) => {
  const m = window.MAPDATA;
  return [(lon - m.lon0) * m.cos * m.k, (m.lat1 - lat) * m.k];
};

window.drawMap = function (svgId, listId, opts = {}) {
  const map = document.getElementById(svgId);
  const list = listId && document.getElementById(listId);
  if (!map) return;
  const base = opts.base || '';
  const M = window.MAPDATA;
  map.setAttribute('viewBox', `0 0 ${M.W} ${M.H}`);
  const label = (lon, lat, text, cls = 'isl') => { const [x, y] = toXY(lon, lat); return `<text class="${cls}" x="${x.toFixed(1)}" y="${y.toFixed(1)}">${text}</text>`; };
  const big = M.islands.filter(s => s.name), small = M.islands.filter(s => !s.name);
  map.innerHTML = `
    <defs>
      <pattern id="waves" width="40" height="14" patternUnits="userSpaceOnUse">
        <path d="M0 7 Q10 3 20 7 T40 7" fill="none" stroke="rgba(77,163,255,.12)" stroke-width="1"/></pattern>
      <filter id="wobble"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="2.2"/></filter>
    </defs>
    <style>
      .isl { font: 700 13px Pretendard, sans-serif; fill: #DCE8FA; text-anchor: middle; paint-order: stroke; stroke: rgba(5,13,36,.7); stroke-width: 3px; }
      .brg { font: 600 9.5px Pretendard, sans-serif; fill: #F6D89A; paint-order: stroke; stroke: rgba(5,13,36,.8); stroke-width: 3px; }
      .land { font: 600 11px Pretendard, sans-serif; fill: #8EA0BE; text-anchor: middle; }
    </style>
    <rect width="${M.W}" height="${M.H}" fill="url(#waves)"/>
    <g filter="url(#wobble)" stroke-linejoin="round">
      ${M.coasts.map(d => `<path d="${d}" fill="none" stroke="rgba(142,197,255,.45)" stroke-width="1.3" stroke-dasharray="4 3"/>`).join('')}
      ${small.map(s => `<path d="${s.d}" fill="rgba(77,163,255,.1)" stroke="rgba(142,197,255,.35)" stroke-width="1"/>`).join('')}
      ${big.map(s => `<path d="${s.d}" fill="rgba(77,163,255,.2)" stroke="#8EC5FF" stroke-width="1.6"/>`).join('')}
      ${Object.values(M.bridges).map(d => `<path d="${d}" fill="none" stroke="#F6D89A" stroke-width="3.2" stroke-linecap="round"/>`).join('')}
    </g>
    ${label(126.445, 37.725, '강화도')}${label(126.318, 37.668, '석모도')}${label(126.265, 37.79, '교동도')}
    ${label(126.6, 37.68, '김포', 'land')}
    ${label(126.528, 37.738, '강화대교', 'brg')}${label(126.527, 37.645, '초지대교', 'brg')}
    ${label(126.355, 37.708, '석모대교', 'brg')}${label(126.29, 37.762, '교동대교', 'brg')}`;

  POINTS.forEach((p, i) => {
    const n = i + 1;
    let [x, y] = toXY(p.lon, p.lat);
    x += p.dx || 0;
    if (p.kind === 'secret') {
      map.insertAdjacentHTML('beforeend', `<g class="area" data-i="${i}"><ellipse cx="${x}" cy="${y}" rx="30" ry="20"/>
        <text x="${x}" y="${y + 4}" fill="#F6D89A" font-size="11" font-weight="800" text-anchor="middle">${n} 어딘가</text></g>`);
    } else {
      // 핀 끝이 실제 위치를 가리키도록 물방울 모양
      map.insertAdjacentHTML('beforeend', `<g class="pin${p.kind === 'closed' ? ' closed' : ''}" data-i="${i}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})">
        <circle class="halo" cx="0" cy="-15" r="14"/>
        <path class="dot" d="M0 0 C-3 -6 -10 -9 -10 -16 A10 10 0 1 1 10 -16 C10 -9 3 -6 0 0Z" fill="#2F7BFF" stroke="#fff" stroke-width="1.5"/>
        <text x="0" y="-12" fill="#fff" font-size="11" font-weight="800" text-anchor="middle">${n}</text></g>`);
    }
    if (list) {
      const chip = p.kind === 'closed' ? '<span class="chip closed">지금 못 앉음</span>' : p.kind === 'secret' ? '<span class="chip secret">위치 비공개</span>' : '';
      list.insertAdjacentHTML('beforeend', `<div class="p" data-i="${i}"><div class="no ${p.kind}">${n}</div><div>
        <div class="name">${p.name}${p.alias ? ` <small style="color:var(--dim);font-weight:600">(${p.alias})</small>` : ''}${chip}</div><div class="meta">${p.region} · ${p.fish}</div><div class="meta">${p.tip}</div>
        <a class="go" href="${base}points/${p.id}.html">자세히 보기 →</a>${p.naver ? ` <a class="go nv-link" href="${p.naver}" target="_blank" rel="noopener">네이버 지도</a>` : ''}</div></div>`);
    }
  });
  // 핀을 누르면 지도 위에 말풍선: 네이버 지도 열기 / 자세히
  const card = map.closest('.map');
  let bubble = card.querySelector('.bubble');
  if (!bubble) { bubble = document.createElement('div'); bubble.className = 'bubble'; card.appendChild(bubble); }
  const showBubble = i => {
    const p = POINTS[i];
    let [x, y] = toXY(p.lon, p.lat); x += p.dx || 0;
    const nav = p.naver ? `<a class="nv" href="${p.naver}" target="_blank" rel="noopener">네이버 지도 열기</a>` : '<span class="nv off">위치는 비공개</span>';
    bubble.innerHTML = `<b>${POINTS.indexOf(p) + 1}. ${p.name}</b>${nav}<a class="dt" href="${base}points/${p.id}.html">자세히 →</a>`;
    bubble.style.left = `${(x / M.W) * 100}%`;
    bubble.style.top = `${((y - (p.kind === 'secret' ? 22 : 32)) / M.H) * 100}%`;
    bubble.classList.add('show');
  };
  const els = () => document.querySelectorAll(`#${svgId} [data-i]` + (list ? `, #${listId} [data-i]` : ''));
  const pick = i => els().forEach(el => el.classList.toggle('on', el.dataset.i == i));
  els().forEach(el => el.addEventListener('click', (ev) => {
    if (ev.target.closest('a')) return;
    pick(el.dataset.i);
    if (el.closest('svg')) showBubble(el.dataset.i); else bubble.classList.remove('show');
  }));
  map.addEventListener('click', (ev) => { if (!ev.target.closest('[data-i]')) { bubble.classList.remove('show'); } });
  if (list) pick(0);
};

// ── 물때 ──────────────────────────────────────────────────
// data/tide.json 을 읽는다. 이 파일은 GitHub Actions가 매일 새벽
// 국립해양조사원 조석예보에서 받아 갱신한다(tools/fetch_tide.py).
window.drawTide = async function () {
  const $ = id => document.getElementById(id);
  const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
  let data;
  try {
    const r = await fetch('data/tide.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error(r.status);
    data = await r.json();
  } catch (e) {
    set('tideSrc', '물때 자료를 불러오지 못했어요. 잠시 뒤 다시 열어 주세요.');
    return;
  }
  if (data.sample && $('mockNote')) $('mockNote').hidden = false;

  // 한국 시간 기준 오늘
  const kst = new Date(Date.now() + (9 * 60 + new Date().getTimezoneOffset()) * 60000);
  const key = d => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
  const addDay = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
  const today = key(kst);
  const WD = '일월화수목금토';

  let code = data.stations[0].code;
  try { const s = localStorage.getItem('tideStation'); if (data.stations.some(x => x.code === s)) code = s; } catch (e) {}

  const tabs = $('stabs');
  const render = () => {
    const st = data.stations.find(x => x.code === code);
    if (tabs) tabs.innerHTML = data.stations.map(x =>
      `<button type="button" role="tab" aria-selected="${x.code === code}" data-code="${x.code}">${x.name}</button>`).join('');
    const updated = data.generated ? data.generated.slice(5, 10).replace('-', '/') + ' 갱신' : '';
    // 탭 이름과 실제 관측소가 다르면(시화방조제 → 인천송도) 둘 다 보여 준다
    const obs = st.obs && st.obs !== st.name ? `${st.name} · ${st.obs} 관측소 기준` : `${st.name} 관측소 기준`;
    set('tideSrc', `${obs} · ${updated}`);
    const day = data.days[today];
    const todayExt = st.ext[today];
    if (!day || !todayExt) { set('tideDate', '오늘 물때 자료가 아직 없어요.'); return; }
    set('mul', day.mul);
    set('tideDate', `${kst.getMonth() + 1}월 ${kst.getDate()}일 (${WD[kst.getDay()]}) · 음력 ${day.lunar}일`);
    set('sunrise', day.sunrise); set('sunset', day.sunset);
    const tag = $('tideTag');
    const big = ['6물', '7물', '8물'].includes(day.mul), small = ['조금', '무시'].includes(day.mul);
    if (tag) { tag.hidden = !(big || small); tag.textContent = big ? '사리 무렵 · 물살 빠름' : '조금 무렵 · 물살 약함'; }

    // 어제 마지막 ~ 내일 처음까지 이어 붙여 0~24시 곡선을 그린다
    const hr = t => +t.slice(0, 2) + +t.slice(3, 5) / 60;
    const yest = st.ext[key(addDay(kst, -1))] || [], tomo = st.ext[key(addDay(kst, 1))] || [];
    const ext = [
      ...yest.slice(-1).map(e => [hr(e.time) - 24, e.level, e.t]),
      ...todayExt.map(e => [hr(e.time), e.level, e.t]),
      ...tomo.slice(0, 2).map(e => [hr(e.time) + 24, e.level, e.t]),
    ].filter(e => e[1] != null);
    // 물때가 자정을 넘어가 오늘이 3번뿐인 날은 내일 첫 물때를 흐리게 덧붙인다
    const shown = [...todayExt.map(e => ({ ...e, h: hr(e.time) })),
      ...(todayExt.length < 4 ? tomo.slice(0, 4 - todayExt.length).map(e => ({ ...e, h: hr(e.time) + 24, tomo: true })) : [])];
    const times = $('times');
    if (times) times.innerHTML = shown.map(e =>
      `<div class="t${e.tomo ? ' tomo' : ''}" data-h="${e.h.toFixed(3)}"><div class="k${e.t === 'L' ? ' low' : ''}">${e.tomo ? '내일 ' : ''}${e.t === 'H' ? '만조' : '간조'}</div><div class="v">${e.time}</div><div class="h">${e.level ?? '–'}cm</div></div>`).join('');
    drawCurve(ext);
    drawWeek();
  };
  const drawWeek = () => {
    const week = $('week');
    if (!week) return;
    const st = data.stations.find(x => x.code === code);
    let html = '';
    for (let i = 0; i < 7; i++) {
      const d = addDay(kst, i), k = key(d), day = data.days[k], ex = st.ext[k];
      if (!day || !ex) continue;
      const hi = ex.find(e => e.t === 'H'), lo = ex.find(e => e.t === 'L');
      const big = ['6물', '7물', '8물'].includes(day.mul), small = ['조금', '무시'].includes(day.mul);
      html += `<div class="day${i === 0 ? ' on' : ''}"><div class="d">${d.getMonth() + 1}/${d.getDate()} ${WD[d.getDay()]}</div><div class="m">${day.mul}</div>
        <div class="hi">만조 ${hi ? hi.time : '–'}</div><div class="lo">간조 ${lo ? lo.time : '–'}</div>${big ? '<div class="tg big">사리</div>' : small ? '<div class="tg">조금</div>' : ''}</div>`;
    }
    week.innerHTML = html;
  };
  if (tabs) tabs.addEventListener('click', ev => {
    const b = ev.target.closest('button[data-code]');
    if (!b) return;
    code = b.dataset.code;
    try { localStorage.setItem('tideStation', code); } catch (e) {}
    render();
  });
  render();
};

function drawCurve(ext) {
  const curve = document.getElementById('curve');
  if (curve && ext.length > 1) {
    const W = 600, top = 14, bot = 126;
    const max = Math.max(...ext.map(e => e[1])) * 1.08;
    const x = h => h / 24 * W, y = v => bot - v / max * (bot - top);
    const level = h => {
      for (let i = 0; i < ext.length - 1; i++) {
        const [h0, v0] = ext[i], [h1, v1] = ext[i + 1];
        if (h >= h0 && h <= h1) return v0 + (v1 - v0) * (1 - Math.cos(Math.PI * (h - h0) / (h1 - h0))) / 2;
      }
      return h < ext[0][0] ? ext[0][1] : ext[ext.length - 1][1];
    };
    let d = '';
    for (let h = 0; h <= 24; h += .25) d += (h ? 'L' : 'M') + x(h).toFixed(1) + ' ' + y(level(h)).toFixed(1);
    const clock = new Date();
    const now = clock.getHours() + clock.getMinutes() / 60;
    const rising = level(now + .1) > level(now);
    // 다음 간조/만조까지 남은 시간
    const nxt = ext.find(([h]) => h > now);
    if (nxt) {
      const isHigh = nxt[2] === 'H';
      const hh = ((nxt[0] % 24) + 24) % 24, hm = Math.round((hh % 1) * 60);
      const left = Math.round((nxt[0] - now) * 60);
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      set('nextKind', isHigh ? '다음 만조' : '다음 간조');
      set('nextTime', `${nxt[0] >= 24 ? '내일 ' : ''}${String(Math.floor(hh)).padStart(2, '0')}:${String(hm).padStart(2, '0')}`);
      set('nextLeft', left >= 60 ? `${Math.floor(left / 60)}시간 ${left % 60}분 뒤` : `${left}분 뒤`);
      document.querySelectorAll('.t[data-h]').forEach(el => el.classList.toggle('next', Math.abs(+el.dataset.h - nxt[0]) < .01));
    }
    let s = `<defs><linearGradient id="fillg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4DA3FF" stop-opacity=".45"/><stop offset="1" stop-color="#4DA3FF" stop-opacity="0"/></linearGradient></defs>`;
    [0, 6, 12, 18, 24].forEach(h => s += `<line x1="${x(h)}" y1="${top}" x2="${x(h)}" y2="${bot}" stroke="rgba(142,197,255,.12)"/><text x="${Math.min(Math.max(x(h), 10), W - 14)}" y="144" fill="#8EA0BE" font-size="11" text-anchor="middle">${h}시</text>`);
    s += `<path d="${d}L${W} ${bot}L0 ${bot}z" fill="url(#fillg)"/><path d="${d}" fill="none" stroke="#8EC5FF" stroke-width="2.5"/>`;
    s += `<line x1="${x(now)}" y1="${top}" x2="${x(now)}" y2="${bot}" stroke="#F6D89A" stroke-dasharray="3 3"/><circle cx="${x(now)}" cy="${y(level(now))}" r="5" fill="#F6D89A"/><text x="${x(now) + 8}" y="${top + 10}" fill="#F6D89A" font-size="11"${now > 18 ? ' text-anchor="end" dx="-16"' : ''}>지금 · ${rising ? '들물' : '날물'}</text>`;
    curve.innerHTML = s;
  }
}

// ── 홈 화면 앱 · 오프라인 대비 (sw.js) ─────────────────────────
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
  const swBase = /\/points\/[^/]+$/.test(location.pathname) ? '../' : '';
  window.addEventListener('load', () => navigator.serviceWorker.register(swBase + 'sw.js').catch(() => {}));
}