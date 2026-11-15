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

    dpath = grab(r'<path d="([^"]+)"', svg)
    deco = (f'<svg class="deco" viewBox="0 0 800 360" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><path d="{dpath}"/></svg>' if dpath else "")
    for i, m in enumerate(ms):
        if i < len(stops):
            m["typ"], m["nt"] = stops[i][1], stops[i][2]
            m["em"] = em(stops[i][1])
    data = json.dumps({"pts": pts, "ms": ms, "hs": hs, "city": city}, separators=(",", ":"), ensure_ascii=False)

    out = head + "<style>" + CSS + "</style></head><body>\n" + f"""<header class="top"><a href="/"><img src="/logo-header.png" alt="LALOO" width="120" height="34"></a><nav><a href="/routes/">Routes</a> <span>›</span> <a href="{e(city_href)}">{e(city)}</a></nav></header>
<section class="hero">{deco}<div class="hin"><p class="kick">{e(city)} · walking route</p><h1>{e(rname)}</h1><div class="chips">{chips}</div></div></section>
<main>
<div class="mapwrap"><div id="map" aria-label="3D route map"></div><div id="hud"><div class="bar"><i></i></div><span id="hudt"></span></div><div class="btns"><button id="play" type="button">▶ Walk the route in 3D</button></div>
<noscript>{svg}<p class="nt">Interactive map needs JavaScript.</p></noscript></div>
<div class="cols"><section><h2>The route</h2><ol class="tl">{"".join(tl)}</ol></section>
<aside><h2>Toilets &amp; water</h2>{tcards or '<p class="nt">No helper points found near this route.</p>'}
<a class="cta" href="{e(city_href)}">More {e(city)} routes →</a></aside></div>
<p class="attr">{attrib}</p>
</main>
<footer><a href="/">laloo.org</a> · <a href="/routes/">Routes</a> · <a href="{e(city_href)}">{e(city)} routes</a> · © OpenStreetMap contributors · OpenFreeMap</footer>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js" defer></script>
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
.deco{position:absolute;inset:0;width:100%;height:100%;opacity:.28}.deco path{fill:none;stroke:#fff;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:4000;stroke-dashoffset:4000;animation:dd 4s .3s ease forwards}@keyframes dd{to{stroke-dashoffset:0}}
.btns{position:absolute;z-index:5;right:14px;bottom:30px;display:flex;gap:8px}
.btns button{border:0;border-radius:999px;padding:12px 18px;font:700 15px system-ui,sans-serif;background:#1c4fa0;color:#fff;box-shadow:0 6px 18px rgba(28,79,160,.45);cursor:pointer;transition:transform .15s}.btns button:hover{transform:translateY(-2px)}
#hud{position:absolute;z-index:5;left:14px;right:14px;top:14px;display:none;background:rgba(16,34,61,.82);color:#fff;border-radius:14px;padding:10px 14px;backdrop-filter:blur(6px);font-size:14px}
#hud.on{display:block;animation:up .4s ease both}#hud .bar{height:5px;border-radius:5px;background:rgba(255,255,255,.2);margin-bottom:8px;overflow:hidden}#hud .bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#f2a516,#7fd79a)}
#hudt b{font-size:16px}
.pin{width:34px;height:34px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#1c4fa0;border:3px solid #fff;box-shadow:0 4px 12px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;cursor:pointer;animation:drop .6s cubic-bezier(.3,1.6,.5,1) both}.pin b{transform:rotate(45deg);color:#fff;font:800 14px system-ui,sans-serif}.pin.on{background:#f2a516}
@keyframes drop{from{opacity:0;transform:translateY(-40px) rotate(-45deg)}}
.hm{width:24px;height:24px;border-radius:50%;background:#1b7a3a;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,.3)}
.walker{width:22px;height:22px;border-radius:50%;background:#f2a516;border:4px solid #fff;box-shadow:0 0 0 0 rgba(242,165,22,.6);animation:pu 1.1s infinite}@keyframes pu{70%{box-shadow:0 0 0 16px rgba(242,165,22,0)}100%{box-shadow:0 0 0 0 rgba(242,165,22,0)}}
.maplibregl-popup-content{border-radius:14px;font:14px/1.4 system-ui,sans-serif;color:#10223d;padding:12px 14px;box-shadow:0 10px 30px rgba(16,34,61,.25);animation:up .35s ease both}
.bb .bh{display:flex;gap:10px;align-items:center}.bb .be{font-size:26px}.bb b{display:block;font-size:15px}.bb .bt{font-size:12px;font-weight:700;color:#1c4fa0;text-transform:capitalize}.bb p{margin:8px 0 0;color:#5f6b7d;font-size:13px}
.bb .bl{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.bb .bl a{font-size:12px;font-weight:700;text-decoration:none;background:#e8f0fb;color:#1c4fa0;padding:5px 9px;border-radius:999px}
.brk .maplibregl-popup-content{background:#1b7a3a;color:#fff}.brk .maplibregl-popup-tip{border-top-color:#1b7a3a!important;border-bottom-color:#1b7a3a!important}.brk .bb span{display:block;font-size:13px;opacity:.9}
#map .fb svg{width:100%;height:100%}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.rv{opacity:1;transform:none}.deco path{stroke-dashoffset:0}}"""

JS = r"""(function(){
var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.15}):null;
document.querySelectorAll('.rv').forEach(function(el,i){el.style.transitionDelay=(i%6)*60+'ms';io?io.observe(el):el.classList.add('in')});
var D=window.LR,cards=document.querySelectorAll('.st'),btn=document.getElementById('play'),hud=document.getElementById('hud'),bar=hud.querySelector('i'),hudt=document.getElementById('hudt');
function fallback(){var n=document.querySelector('noscript');var m=document.getElementById('map');if(n){m.innerHTML='<div class="fb">'+n.textContent+'</div>'}btn.style.display='none'}
function hl(i){cards.forEach(function(c,j){c.classList.toggle('on',j===i)});pins.forEach(function(p,j){p.el.firstChild.classList.toggle('on',j===i)})}
var pins=[],hms=[],map,L=D.pts.map(function(p){return[p[1],p[0]]});
function hv(a,b){var R=6371000,t=Math.PI/180,x=(b[1]-a[1])*t,y=(b[0]-a[0])*t*Math.cos((a[1]+b[1])/2*t);return Math.sqrt(x*x+y*y)*R}
function brg(a,b){var t=Math.PI/180,y=Math.sin((b[0]-a[0])*t)*Math.cos(b[1]*t),x=Math.cos(a[1]*t)*Math.sin(b[1]*t)-Math.sin(a[1]*t)*Math.cos(b[1]*t)*Math.cos((b[0]-a[0])*t);return Math.atan2(y,x)/t}
var cum=[0];for(var j=1;j<L.length;j++)cum.push(cum[j-1]+hv(L[j-1],L[j]));var TOT=cum[cum.length-1]||1;
function at(d){d=Math.max(0,Math.min(TOT,d));var k=1;while(k<cum.length-1&&cum[k]<d)k++;var s=cum[k]-cum[k-1]||1,r=(d-cum[k-1])/s,p=L[k-1],q=L[k]||p;return[p[0]+(q[0]-p[0])*r,p[1]+(q[1]-p[1])*r]}
var hd=D.hs.map(function(h){if(h.lat==null)return -1;var bi=0,bd=1e18;L.forEach(function(p,j){var d=hv(p,[h.lon,h.lat]);if(d<bd){bd=d;bi=j}});return cum[bi]||0});
var sd=D.ms.map(function(m){var bi=0,bd=1e18;L.forEach(function(p,j){var d=hv(p,[m.lon,m.lat]);if(d<bd){bd=d;bi=j}});return cum[bi]||0});
function grad(p,c1,c2){if(p<=0)return['interpolate',['linear'],['line-progress'],0,c2,1,c2];if(p>=0.9998)return['interpolate',['linear'],['line-progress'],0,c1,1,c1];return['interpolate',['linear'],['line-progress'],0,c1,p,c1,Math.min(1,p+1e-4),c2,1,c2]}
function bounds(){var b=new maplibregl.LngLatBounds();L.forEach(function(p){b.extend(p)});D.ms.forEach(function(m){b.extend([m.lon,m.lat])});return b}
function init(){if(!window.maplibregl)return setTimeout(init,150);if(!L.length&&!D.ms.length)return fallback();
try{map=new maplibregl.Map({container:'map',style:'https://tiles.openfreemap.org/styles/liberty',bounds:bounds(),fitBoundsOptions:{padding:60},pitch:0,maxPitch:75,cooperativeGestures:true,attributionControl:{compact:true}})}catch(e){return fallback()}
map.addControl(new maplibregl.NavigationControl({visualizePitch:true}),'top-left');
map.on('load',function(){
map.addSource('r',{type:'geojson',lineMetrics:true,data:{type:'Feature',properties:{},geometry:{type:'LineString',coordinates:L.length?L:[[0,0],[0,0]]}}});
map.addLayer({id:'rc',type:'line',source:'r',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#ffffff','line-width':10,'line-opacity':.9}});
map.addLayer({id:'rl',type:'line',source:'r',layout:{'line-cap':'round','line-join':'round'},paint:{'line-width':6,'line-gradient':grad(0,'#1c4fa0','rgba(28,79,160,0)')}});
var t0=null;function draw(ts){if(!t0)t0=ts;var p=Math.min(1,(ts-t0)/2200);map.setPaintProperty('rl','line-gradient',grad(p,'#1c4fa0','rgba(28,79,160,0)'));if(p<1)requestAnimationFrame(draw);else map.easeTo({pitch:50,bearing:-15,duration:2000})}requestAnimationFrame(draw);
D.ms.forEach(function(m,i){var el=document.createElement('div');el.innerHTML='<div class="pin" style="animation-delay:'+(0.5+i*0.25)+'s"><b>'+(m.sira||i+1)+'</b></div>';
var mk=new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat([m.lon,m.lat]).setPopup(new maplibregl.Popup({offset:34,closeButton:false,maxWidth:'280px'}).setHTML(bub(m,i))).addTo(map);
el.addEventListener('click',function(){hl(i)});pins.push({el:el,mk:mk})});
D.hs.forEach(function(h){if(h.lat==null)return;var wc=/toilet/i.test(h.tur||'');var el=document.createElement('div');el.className='hm';el.textContent=wc?'🚻':'💧';hms.push({h:h,mk:new maplibregl.Marker({element:el}).setLngLat([h.lon,h.lat]).setPopup(new maplibregl.Popup({offset:16,closeButton:false,className:'brk'}).setHTML('<div class="bb"><b>'+(wc?'🚻 WC break':'💧 Water break')+'</b><span>'+esc(h.ad||'')+(wc?'':' · refill your bottle')+'</span></div>')).addTo(map)})});
});
cards.forEach(function(c,i){c.querySelector('.card').addEventListener('click',function(){if(!pins[i]||walking)return;hl(i);map.flyTo({center:pins[i].mk.getLngLat(),zoom:17.3,pitch:60,bearing:map.getBearing(),duration:1600});pins.forEach(function(p){p.mk.getPopup().remove()});pins[i].mk.togglePopup();document.getElementById('map').scrollIntoView({behavior:'smooth',block:'center'})})});
if(!L.length){btn.style.display='none';return}
var walking=false,stop=false;
btn.addEventListener('click',function(){if(walking){stop=true;return}walk()});
function walk(){walking=true;stop=false;btn.textContent='■ Stop';hud.classList.add('on');pins.forEach(function(p){p.mk.getPopup().remove()});
var wel=document.createElement('div');wel.className='walker';var w=new maplibregl.Marker({element:wel}).setLngLat(L[0]).addTo(map);
var speed=Math.max(90,TOT/22),dist=0,last=-1,hl2=-1,pause=0,prev=null,b=brg(L[0],at(40));
map.flyTo({center:L[0],zoom:17.4,pitch:62,bearing:b,duration:2200,essential:true});
setTimeout(function(){requestAnimationFrame(step)},2300);
function step(ts){if(stop)return end();if(prev===null)prev=ts;var dt=Math.min(64,ts-prev);prev=ts;
if(pause>0){pause-=dt}else{dist+=speed*dt/1000}
var pos=at(dist),ah=at(dist+45),nb=brg(pos,ah),db=((nb-b+540)%360)-180;b+=db*Math.min(1,dt/450);
w.setLngLat(pos);map.jumpTo({center:pos,bearing:b,pitch:62,zoom:17.4});
var f=Math.min(1,dist/TOT);map.setPaintProperty('rl','line-gradient',grad(f,'#f2a516','#1c4fa0'));bar.style.width=(f*100)+'%';
sd.forEach(function(d,i){if(dist>=d&&i>last){last=i;hl(i);pause=3200;pins.forEach(function(p){p.mk.getPopup().remove()});pins[i].mk.togglePopup()}});hd.forEach(function(d,i){if(d>=0&&dist>=d&&i>hl2){hl2=i;pause=Math.max(pause,2200);var o=hms.filter(function(x){return x.h===D.hs[i]})[0];if(o){pins.forEach(function(p){p.mk.getPopup().remove()});o.mk.togglePopup();setTimeout(function(){o.mk.getPopup().remove()},2600)}}});
var nx=last+1<D.ms.length?D.ms[last+1].ad:'Finish';hudt.innerHTML=(last>=0?'<b>'+(last+1)+'. '+esc(D.ms[last].ad)+'</b> · ':'')+'next: '+esc(nx)+' · '+(Math.max(0,TOT-dist)/1000).toFixed(2)+' km left';
if(dist<TOT)requestAnimationFrame(step);else setTimeout(end,1200)}
function end(){w.remove();hms.forEach(function(o){o.mk.getPopup().remove()});walking=false;btn.textContent='↻ Walk again';hud.classList.remove('on');map.setPaintProperty('rl','line-gradient',grad(1,'#1c4fa0','#1c4fa0'));map.fitBounds(bounds(),{padding:60,pitch:50,bearing:-15,duration:1800})}}
}
function bub(m,i){var q=encodeURIComponent(m.ad+' '+(D.city||''));return '<div class="bb"><div class="bh"><span class="be">'+(m.em||'📍')+'</span><div><b>'+(m.sira||i+1)+'. '+esc(m.ad)+'</b><span class="bt">'+esc(m.typ||'')+'</span></div></div>'+(m.nt?'<p>'+esc(m.nt)+'</p>':'')+'<div class="bl"><a target="_blank" rel="noopener" href="https://en.wikipedia.org/w/index.php?search='+q+'">About</a><a target="_blank" rel="noopener" href="https://www.google.com/search?q='+q+'+opening+hours">Hours &amp; tickets</a><a target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query='+m.lat+','+m.lon+'">Directions</a></div></div>'}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();"""

if __name__ == "__main__":
    n = sum(1 for p in sys.argv[1:] if render(p))
    print(f"{n} sayfa yenilendi")
