#!/usr/bin/env python3
"""Laloo rota sayfalarini yeni tasarimla yeniden uretir.
Kullanim: python3 render.py <sayfa.html> ...  (yerinde yazar)
Veriyi mevcut sayfanin icinden okur: baslik, istatistik, duraklar, ara yollar, tuvaletler, harita noktalari."""
import html, json, re, sys

EMOJI = {"temple": "⛩️", "shrine": "⛩️", "museum": "🏛️", "park": "🌳", "garden": "🌷", "square": "⛲",
         "beach": "🏖️", "church": "⛪", "cathedral": "⛪", "basilica": "⛪", "viewpoint": "🔭", "market": "🛍️",
         "monument": "🗿", "memorial": "🗿", "castle": "🏰", "palace": "🏰", "bridge": "🌉", "street": "🚶",
         "harbour": "⚓", "harbor": "⚓", "trail": "🥾", "gallery": "🖼️", "station": "🚉", "attraction": "📍"}


def em(t):
    t = (t or "").lower()
    for k, v in EMOJI.items():
        if k in t:
            return v
    return "📍"


def grab(pat, s, flags=re.S):
    m = re.search(pat, s, flags)
    return m.group(1) if m else ""


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def rows(table_html):
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", table_html, re.S):
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if tds:
            out.append([strip(x) for x in tds])
    return out


def render(path):
    src = open(path, encoding="utf-8").read()
    if 'http-equiv="refresh"' in src:
        return False
    head = src.split("<style>")[0]
    h1 = strip(grab(r"<h1>(.*?)</h1>", src))
    city, _, rname = h1.partition(" walking route: ")
    stat = strip(grab(r'<p class="stat">(.*?)</p>', src))
    km = grab(r"([\d.]+) km", stat)
    mins = grab(r"(\d+) min", stat)
    nst = grab(r"(\d+) stops", stat)
    ntoi = grab(r"(\d+) toilet", stat)
    city_href = grab(r'<nav>.*?·\s*<a href="([^"]+)"', src)
    svg = grab(r'(<svg class="route".*?</svg>)', src)
    js = grab(r"<script>\(function\(\)\{function init\(\)\{if\(!window\.L\)return;(.*?)var map=L\.map", src)
    pts = json.loads(grab(r"var pts=(\[.*?\]);", js) or "[]")
    ms = json.loads(grab(r"var ms=(\[.*?\]);", js) or "[]")
    hs = json.loads(grab(r"var hs=(\[.*?\]);", js) or "[]")

    stops = []
    for b in re.findall(r'<div class="stop">(.*?)</div></div>', src, re.S):
        name = strip(re.sub(r'<span class="n">\d+</span>', "", grab(r"<b>(.*?)</b>", b)))
        typ = strip(grab(r'<span class="t">(.*?)</span>', b))
        note = strip(grab(r'<div class="note">(.*)', b))
        if all("No info" in p for p in note.split("·")):
            note = ""
        stops.append((name, typ, note))
    tabs = re.findall(r"<tbody>(.*?)</tbody>", src, re.S)
    segs = rows(tabs[0]) if tabs else []
    toil = rows(tabs[1]) if len(tabs) > 1 else []
    attrib = grab(r'<p class="note">(Attribution:.*?)</p>', src)

    e = html.escape
    chips = (f'<span class="chip"><b>{km}</b> km</span><span class="chip"><b>{mins}</b> min walk</span>'
             f'<span class="chip"><b>{nst}</b> stops</span><span class="chip g"><b>{ntoi}</b> toilet / water</span>')

    tl = []
    for i, (name, typ, note) in enumerate(stops):
        tl.append(f'<li class="st rv" data-i="{i}"><span class="dot">{i+1}</span><div class="card">'
                  f'<div class="ic">{em(typ)}</div><div><h3>{e(name)}</h3><span class="tag">{e(typ)}</span>'
                  + (f'<p class="nt">{e(note)}</p>' if note else "") + "</div></div></li>")
        if i < len(segs):
            s = segs[i]
            helper = s[4] if len(s) > 4 and s[4] not in ("—", "-", "") else ""
            tl.append(f'<li class="sg rv"><span>🚶 {e(s[2])} · {e(s[3])}</span>'
                      + (f'<span class="hp">💧 {e(helper)} on the way</span>' if helper else "") + "</li>")

    tcards = "".join(
        f'<div class="tc rv"><div class="ic g">{"🚻" if "toilet" in (r[1] or "").lower() else "💧"}</div>'
        f'<div><b>{e(r[0])}</b><span>{e(r[1])} · {e(r[2])} from route</span>'
        + (f'<span>{e(r[3])}</span>' if r[3] and r[3] != "No info / No info" else "") + "</div></div>"
        for r in toil)

    data = json.dumps({"pts": pts, "ms": ms, "hs": hs}, separators=(",", ":"), ensure_ascii=False)

    out = head + "<style>" + CSS + "</style></head><body>\n" + f"""<header class="top"><a href="/"><img src="/logo-header.png" alt="LALOO" width="120" height="34"></a><nav><a href="/routes/">Routes</a> <span>›</span> <a href="{e(city_href)}">{e(city)}</a></nav></header>
<section class="hero"><div class="hin"><p class="kick">{e(city)} · walking route</p><h1>{e(rname)}</h1><div class="chips">{chips}</div></div></section>
<main>
<div class="mapwrap"><div id="map" aria-label="Route map"></div><button id="play" type="button">▶ Walk the route</button>
<noscript>{svg}<p class="nt">Interactive map needs JavaScript.</p></noscript></div>
<div class="cols"><section><h2>The route</h2><ol class="tl">{"".join(tl)}</ol></section>
<aside><h2>Toilets &amp; water</h2>{tcards or '<p class="nt">No helper points found near this route.</p>'}
<a class="cta" href="{e(city_href)}">More {e(city)} routes →</a></aside></div>
<p class="attr">{attrib}</p>
</main>
<footer><a href="/">laloo.org</a> · <a href="/routes/">Routes</a> · <a href="{e(city_href)}">{e(city)} routes</a> · © OpenStreetMap contributors · © CARTO</footer>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" defer></script>
<script>var LR={data};</script>
<script>{JS}</script>
</body></html>
"""
    open(path, "w", encoding="utf-8").write(out)
    return True


CSS = r""":root{--navy:#10223d;--blue:#1c4fa0;--line:#e6e1d4;--bg:#fefef8;--muted:#5f6b7d;--card:#fff;--green:#1b7a3a;--greenbg:#e3f6e8;--tag:#e8f0fb;--sh:0 6px 24px rgba(16,34,61,.08)}
@media (prefers-color-scheme:dark){:root{--navy:#e9eef6;--blue:#8fb4ff;--line:#2a3445;--bg:#111722;--muted:#9aa6b8;--card:#172030;--green:#7fd79a;--greenbg:#1d3326;--tag:#1f2e48;--sh:0 6px 24px rgba(0,0,0,.3)}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--navy);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}a{color:var(--blue)}
.top{position:sticky;top:0;z-index:1000;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 16px;background:color-mix(in srgb,var(--bg) 85%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.top img{height:34px;display:block;border-radius:8px}.top nav{font-size:14px}.top nav span{color:var(--muted);margin:0 4px}.top nav a{text-decoration:none;font-weight:600}
@media (prefers-color-scheme:dark){.top img{background:#fefef8;padding:2px 6px}}
.hero{background:linear-gradient(135deg,#1c4fa0 0%,#10223d 70%);color:#fff;padding:42px 16px 70px;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;inset:auto -10% -60% auto;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(127,215,154,.35),transparent 65%);animation:fl 9s ease-in-out infinite alternate}
@keyframes fl{to{transform:translate(-60px,-40px)}}
.hin{max-width:1080px;margin:0 auto;position:relative;z-index:1}.kick{margin:0;opacity:.75;font-size:14px;letter-spacing:.06em;text-transform:uppercase}
.hero h1{font-size:clamp(30px,5vw,48px);line-height:1.1;margin:6px 0 16px;animation:up .7s ease both}
.chips{display:flex;flex-wrap:wrap;gap:8px;animation:up .7s .15s ease both}.chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);padding:6px 12px;border-radius:999px;font-size:14px}.chip b{font-size:16px}.chip.g{background:rgba(127,215,154,.22)}
@keyframes up{from{opacity:0;transform:translateY(14px)}}
main{max-width:1080px;margin:0 auto;padding:0 16px 40px}
.mapwrap{position:relative;margin-top:-44px;z-index:2;border-radius:18px;overflow:hidden;box-shadow:var(--sh);border:1px solid var(--line);background:var(--card)}
#map{height:min(62vh,520px);background:#e9eef3}
#play{position:absolute;z-index:500;right:14px;bottom:14px;border:0;border-radius:999px;padding:12px 18px;font:700 15px system-ui,sans-serif;background:#1c4fa0;color:#fff;box-shadow:0 6px 18px rgba(28,79,160,.45);cursor:pointer;transition:transform .15s}#play:hover{transform:translateY(-2px)}#play:disabled{opacity:.6;cursor:default}
.mapwrap noscript svg{width:100%;height:auto;display:block}
.cols{display:grid;grid-template-columns:1fr;gap:28px;margin-top:28px}@media(min-width:860px){.cols{grid-template-columns:1.6fr 1fr}aside{position:sticky;top:76px;align-self:start}}
h2{font-size:22px;margin:0 0 14px}
.tl{list-style:none;margin:0;padding:0 0 0 22px;position:relative}.tl:before{content:"";position:absolute;left:21px;top:20px;bottom:20px;width:3px;border-radius:3px;background:linear-gradient(var(--blue),var(--green))}
.st{position:relative;padding-left:26px}.dot{position:absolute;left:-14px;top:14px;width:30px;height:30px;border-radius:50%;background:var(--blue);color:#fff;font-weight:800;font-size:14px;display:flex;align-items:center;justify-content:center;border:3px solid var(--bg);transition:transform .3s,background .3s}
.card{display:flex;gap:14px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:var(--sh);cursor:pointer;transition:transform .2s,border-color .2s}
.card:hover{transform:translateX(4px);border-color:var(--blue)}.st.on .card{border-color:var(--blue);transform:translateX(6px)}.st.on .dot{transform:scale(1.25);background:#f2a516}
.ic{flex:none;width:46px;height:46px;border-radius:12px;background:var(--tag);display:flex;align-items:center;justify-content:center;font-size:24px}.ic.g{background:var(--greenbg)}
.card h3{margin:0;font-size:18px}.tag{display:inline-block;margin-top:4px;font-size:12px;font-weight:700;text-transform:capitalize;padding:2px 8px;border-radius:8px;background:var(--tag);color:var(--blue)}
.nt{color:var(--muted);font-size:14px;margin:6px 0 0}
.sg{padding:12px 0 12px 26px;color:var(--muted);font-size:14px;display:flex;flex-wrap:wrap;gap:4px 14px}.sg .hp{color:var(--green);font-weight:600}
.tc{display:flex;gap:12px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 10px}.tc span{display:block;color:var(--muted);font-size:13px}
.cta{display:block;text-align:center;margin-top:14px;padding:12px;border-radius:12px;background:var(--tag);font-weight:700;text-decoration:none}
.rv{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}.rv.in{opacity:1;transform:none}
.attr{color:var(--muted);font-size:12px;margin-top:30px}
footer{max-width:1080px;margin:0 auto;padding:18px 16px 40px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
.lr-pin{width:30px;height:30px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#1c4fa0;border:3px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;animation:drop .5s cubic-bezier(.3,1.6,.5,1) both}.lr-pin b{transform:rotate(45deg);color:#fff;font:800 13px system-ui,sans-serif}
@keyframes drop{from{opacity:0;transform:translateY(-30px) rotate(-45deg)}}
.lr-h{width:22px;height:22px;border-radius:50%;background:#1b7a3a;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:11px;box-shadow:0 2px 6px rgba(0,0,0,.3)}
.lr-w{width:18px;height:18px;border-radius:50%;background:#f2a516;border:3px solid #fff;box-shadow:0 0 0 6px rgba(242,165,22,.35);animation:pu 1.2s infinite}@keyframes pu{50%{box-shadow:0 0 0 12px rgba(242,165,22,0)}}
.lr-line{stroke-dasharray:var(--len);stroke-dashoffset:var(--len);animation:dr 2.4s ease forwards}@keyframes dr{to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.rv{opacity:1;transform:none}.lr-line{stroke-dasharray:none}}"""

JS = r"""(function(){
var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.15}):null;
document.querySelectorAll('.rv').forEach(function(el,i){el.style.transitionDelay=(i%6)*60+'ms';io?io.observe(el):el.classList.add('in')});
function init(){if(!window.L){return setTimeout(init,150)}
var D=window.LR,dark=matchMedia('(prefers-color-scheme:dark)').matches;
var map=L.map('map',{scrollWheelZoom:false,zoomControl:true});
L.tileLayer('https://{s}.basemaps.cartocdn.com/'+'rastertiles/'+(dark?'dark_all':'voyager')+'/{z}/{x}/{y}{r}.png',{maxZoom:19,subdomains:'abcd',attribution:'&copy; OpenStreetMap contributors &copy; CARTO'}).addTo(map);
var b=[];D.pts.forEach(function(p){b.push(p)});D.ms.forEach(function(m){b.push([m.lat,m.lon])});
if(b.length)map.fitBounds(L.latLngBounds(b).pad(.12));else map.setView([0,0],2);
var line=null;if(D.pts.length){L.polyline(D.pts,{color:'#fff',weight:9,opacity:.9}).addTo(map);line=L.polyline(D.pts,{color:'#1c4fa0',weight:5,className:'lr-line'}).addTo(map);
var el=line.getElement();if(el&&el.getTotalLength){var len=el.getTotalLength();el.style.setProperty('--len',len);el.style.strokeDasharray=len}}
var cards=document.querySelectorAll('.st'),mk=[];
D.ms.forEach(function(m,i){var k=L.marker([m.lat,m.lon],{icon:L.divIcon({className:'',html:'<div class="lr-pin" style="animation-delay:'+(0.6+i*0.25)+'s"><b>'+(m.sira||i+1)+'</b></div>',iconSize:[30,30],iconAnchor:[15,30]})}).addTo(map).bindPopup('<b>'+(m.sira||i+1)+'. '+m.ad+'</b>');mk.push(k);
k.on('click',function(){hl(i)})});
D.hs.forEach(function(h){if(h.lat==null)return;L.marker([h.lat,h.lon],{icon:L.divIcon({className:'',html:'<div class="lr-h">'+(/toilet/i.test(h.tur||'')?'🚻':'💧')+'</div>',iconSize:[22,22],iconAnchor:[11,11]})}).addTo(map).bindPopup((h.ad||'')+(h.tur?' ('+h.tur+')':''))});
function hl(i){cards.forEach(function(c,j){c.classList.toggle('on',j===i)})}
cards.forEach(function(c,i){c.querySelector('.card').addEventListener('click',function(){if(!mk[i])return;hl(i);map.flyTo(mk[i].getLatLng(),17,{duration:.8});mk[i].openPopup();document.getElementById('map').scrollIntoView({behavior:'smooth',block:'center'})})});
var near=D.ms.map(function(m){var bi=0,bd=1e9;D.pts.forEach(function(p,j){var d=(p[0]-m.lat)*(p[0]-m.lat)+(p[1]-m.lon)*(p[1]-m.lon);if(d<bd){bd=d;bi=j}});return bi});
var btn=document.getElementById('play');if(!D.pts.length){btn.style.display='none';return}
btn.addEventListener('click',function(){btn.disabled=true;btn.textContent='Walking…';map.closePopup();map.fitBounds(L.latLngBounds(b).pad(.12));
var w=L.marker(D.pts[0],{icon:L.divIcon({className:'',html:'<div class="lr-w"></div>',iconSize:[18,18],iconAnchor:[9,9]}),zIndexOffset:1000}).addTo(map);
var d=[0];for(var j=1;j<D.pts.length;j++){var a=map.latLngToLayerPoint(D.pts[j-1]),c=map.latLngToLayerPoint(D.pts[j]);d.push(d[j-1]+a.distanceTo(c))}
var tot=d[d.length-1]||1,dur=Math.min(14000,Math.max(6000,D.pts.length*20)),t0=null,last=-1;
function step(ts){if(!t0)t0=ts;var f=Math.min(1,(ts-t0)/dur),tg=f*tot,k=1;while(k<d.length-1&&d[k]<tg)k++;
var s=d[k]-d[k-1]||1,r=(tg-d[k-1])/s,p=D.pts[k-1],q=D.pts[k];w.setLatLng([p[0]+(q[0]-p[0])*r,p[1]+(q[1]-p[1])*r]);
near.forEach(function(n,i){if(k>=n&&i>last){last=i;hl(i);mk[i]&&mk[i].openPopup()}});
if(f<1)requestAnimationFrame(step);else setTimeout(function(){map.removeLayer(w);btn.disabled=false;btn.textContent='↻ Walk again'},900)}
requestAnimationFrame(step)})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();"""

if __name__ == "__main__":
    n = sum(1 for p in sys.argv[1:] if render(p))
    print(f"{n} sayfa yenilendi")
