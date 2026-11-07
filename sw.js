// 다리 건너 낚시 · 오프라인 대비
// 인터넷이 되면 항상 새로 받고(받은 것은 저장), 안 되면 마지막으로 저장한 것을 보여 준다.
// 화면 파일을 바꿔도 이 방식이라 따로 버전을 올릴 필요가 없다.
const CACHE = 'darigeonneo-v3';
const CORE = ['./', 'index.html', 'points.html', 'about.html', 'privacy.html',
  'assets/style.css', 'assets/site.js', 'assets/mapdata.js', 'data/tide.json',
  'points/jjoksil.html', 'points/seondupo.html', 'points/seokmo-healing.html',
  'assets/icons/icon-192-v2.png', 'manifest.webmanifest'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // 글꼴 등 다른 곳 파일은 브라우저에 맡김
  e.respondWith(
    // 브라우저 캐시(최대 10분)를 건너뛰고 서버에 바뀌었는지 물어본 뒤 받는다
    fetch(new Request(req.url, { cache: 'no-cache', credentials: 'same-origin' })).then(res => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true })
      .then(hit => hit || (req.mode === 'navigate' ? caches.match('index.html') : Response.error())))
  );
});
