import json, glob, os, re, unicodedata, math, shutil
from pathlib import Path

REPO = Path('/Users/zuzay/sunucu/siteler/laloo')
ROUTES_DATA = Path('/Users/zuzay/sunucu/veri/rota')
OUT = REPO / 'routes'
SITE = 'https://www.laloo.org'

TYPE_EN = {
    'anit': 'monument', 'antik_alan': 'ancient site', 'bazilika': 'basilica',
    'cesme': 'fountain', 'kale': 'castle/fort', 'katedral': 'cathedral',
    'kopru': 'bridge', 'meydan': 'square', 'muze': 'museum', 'park': 'park',
    'saray': 'palace', 'tapinak': 'temple',
}
KIND_EN = {'public': 'Public toilet', 'cafe': 'Cafe/rest stop', 'water': 'Drinking water'}

# stop name translations for known Turkish names
NAME_EN = {
    'Vatikan Müzeleri (giriş)': 'Vatican Museums (entrance)',
    'Aziz Petrus Meydanı': "St. Peter's Square",
    'Aziz Petrus Bazilikası': "St. Peter's Basilica",
    'Castel Sant\'Angelo': "Castel Sant'Angelo",
    'Ponte Sant\'Angelo': "Ponte Sant'Angelo",
    'Eyfel Kulesi': 'Eiffel Tower',
    'Zafer Takı': 'Arc de Triomphe',
    'Louvre Müzesi': 'Louvre Museum',
    'Notre Dame Katedrali': 'Notre-Dame Cathedral',
    'Orsay Müzesi': 'Musée d\'Orsay',
    'Sacre-Coeur Bazilikası': 'Sacré-Cœur Basilica',
    'Panthéon': 'Panthéon',
    'Kolezyum': 'Colosseum',
    'Forum Romanum': 'Roman Forum',
    'Pantheon': 'Pantheon',
    'Trevi Çeşmesi': 'Trevi Fountain',
    'İspanyol Merdivenleri': 'Spanish Steps',
    'Navona Meydanı': 'Piazza Navona',
    'Aziz Angelos Şatosu': "Castel Sant'Angelo",
    'Barselona Katedrali': 'Barcelona Cathedral',
    'Sagrada Familia': 'Sagrada Família',
    'Park Güell': 'Park Güell',
    'Barceloneta Plajı': 'Barceloneta Beach',
    'Brandenburg Kapısı': 'Brandenburg Gate',
    'Reichstag Binası': 'Reichstag Building',
    'Zafer Sütunu': 'Victory Column',
    'Ayasofya': 'Hagia Sophia',
    'Topkapı Sarayı': 'Topkapi Palace',
    'Sultanahmet Camii': 'Blue Mosque',
    'Kapalıçarşı': 'Grand Bazaar',
    'Galata Kulesi': 'Galata Tower',
    'Dolmabahçe Sarayı': 'Dolmabahçe Palace',
}

THEME_SLUG = {
    'Gotik mahalle':'gothic-quarter',
    'Passeig de Gracia':'passeig-de-gracia',
    'Sahil ve Ciutadella':'beach-and-ciutadella',
    'Mitte anıtları':'mitte-landmarks',
    'Müze Adası ve Alexanderplatz':'museum-island-and-alexanderplatz',
    'Parlamento ve bazilika':'parliament-and-basilica',
    'Buda Kalesi ve nehir':'buda-castle-and-river',
    'Westminster ve nehir':'westminster-and-river',
    'Covent Garden ve British Museum':'covent-garden-and-british-museum',
    'Tower ve Southwark':'tower-and-southwark',
    'Downtown merkez':'downtown-center',
    'Hollywood bulvarı':'hollywood-boulevard',
    'Santa Monica merkezi':'santa-monica-center',
    'Sanat üçgeni':'art-triangle',
    'Saray ve Gran Via':'royal-palace-and-gran-via',
    'Federation ve Degraves':'federation-and-degraves',
    'Docklands ve Flagstaff':'docklands-and-flagstaff',
    'Duomo ve Sforza':'duomo-and-sforza',
    'Kale ve park':'castle-and-park',
    'Tarihî merkez ve nehir':'historic-center-and-river',
    'Louvre ve Palais Royal':'louvre-and-palais-royal',
    'Montmartre':'montmartre',
    'Antik Roma':'ancient-rome',
    'Meydanlar ve çeşmeler':'squares-and-fountains',
    'Nehir ve meydan':'river-and-squares',
    'Liman ve Opera':'harbour-and-opera',
    'Darling Harbour':'darling-harbour',
    'Ximending ve anıtlar':'ximending-and-memorials',
    '228 Park ve Taipei Station':'228-park-and-taipei-station',
    'Asakusa ve Ueno':'asakusa-and-ueno',
    'Harajuku ve Yoyogi':'harajuku-and-yoyogi',
    'Vatikan çevresi':'vatican-area',
    'Tarihî merkez':'historic-center',
    'Hofburg ve Rathaus':'hofburg-and-rathaus',
    'Eski şehir ve göl':'old-town-and-lake',
    'Limmat ve Rathaus':'limmat-and-rathaus',
}
CITY_EN = {
    'barcelona':'Barcelona','berlin':'Berlin','budapest':'Budapest','londra':'London',
    'los-angeles':'Los Angeles','madrid':'Madrid','melbourne':'Melbourne','milan':'Milan',
    'paris':'Paris','roma':'Rome','sydney':'Sydney','taipei':'Taipei','tokyo':'Tokyo',
    'vatikan':'Vatican City','vienna':'Vienna','zurich':'Zurich',
}

def slugify(s):
    s = s.lower().strip()
    repl = {'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u','â':'a','î':'i','û':'u','é':'e','è':'e','ê':'e','à':'a','á':'a','í':'i','ó':'o','ô':'o','ú':'u','ñ':'n','ł':'l'}
    for k,v in repl.items(): s=s.replace(k,v)
    s = re.sub(r'[^a-z0-9]+','-', s).strip('-')
    return s or 'route'

def en_name(ad):
    return NAME_EN.get(ad, ad)

def en_type(t):
    return TYPE_EN.get(t, t.replace('_',' ') if t else 'stop')

def en_kind(k):
    return KIND_EN.get(k, 'Toilet/rest stop' if k in ('cafe','public') else (k or 'point'))

def haversine(a,b,c,d):
    R=6371000.0
    import math
    p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(x)))

def point_seg_dist_m(px,py, ax,ay,bx,by):
    # approximate in meters using local projection
    import math
    lat0=math.radians((ay+by)/2)
    def to_m(lon,lat): return ((lon)*111320*math.cos(lat0),(lat)*110540)
    P=to_m(px,py); A=to_m(ax,ay); B=to_m(bx,by)
    ABx, ABy = B[0]-A[0], B[1]-A[1]
    APx, APy = P[0]-A[0], P[1]-A[1]
    ab2 = ABx*ABx + ABy*ABy
    if ab2==0: t=0
    else: t=max(0,min(1,(APx*ABx+APy*ABy)/ab2))
    cx,cy = A[0]+t*ABx, A[1]+t*ABy
    dx,dy = P[0]-cx, P[1]-cy
    return math.sqrt(dx*dx+dy*dy), (cx,cy,t)

def nearest_to_polyline(toilets, geom):
    # geom [[lat,lon],...]
    best=None
    for t in toilets:
        lat=t.get('lat'); lon=t.get('lng')
        if lat is None or lon is None: continue
        bd=None; bseg=0
        for i in range(len(geom)-1):
            ay,ax=geom[i]; by,bx=geom[i+1]
            d,(_cxy)=point_seg_dist_m(lon,lat, ax,ay,bx,by)
            if bd is None or d<bd: bd=d; bseg=i
        if bd is None: continue
        if best is None or bd < best[0]: best=(bd,t,bseg)
    return best

# load toilets per city (best effort)
toilet_cache={}
def load_toilets(city):
    if city in toilet_cache: return toilet_cache[city]
    arr=[]
    # same city file
    for fp in [ROUTES_DATA/city/'tuvaletler.json', ROUTES_DATA/'roma'/'tuvaletler.json' if city in ('roma','vatikan') else None]:
        if fp and fp.exists():
            try:
                d=json.load(open(fp))
                recs=d['kayitlar'] if isinstance(d,dict) and 'kayitlar' in d else (d if isinstance(d,list) else [])
                for r in recs:
                    kind=r.get('kind')
                    if kind=='water': continue
                    if kind not in ('public','cafe', None): continue
                    if r.get('active') is False: continue
                    arr.append(r)
            except: pass
            break
    toilet_cache[city]=arr
    return arr

def route_slug(d, city):
    tema = d.get('tema')
    if tema and tema in THEME_SLUG: return THEME_SLUG[tema]
    bolge = d.get('bolge') or ''
    if bolge in THEME_SLUG: return THEME_SLUG[bolge]
    # fallback from bolge or baslik
    base = d.get('bolge') or d.get('tema') or f"route-{d.get('rota_no',1)}"
    ce = CITY_EN.get(city, city).lower()
    b = base
    for pref in [CITY_EN.get(city,''), city, ce, 'Vatikan', 'Roma']: 
        if pref and b.lower().startswith(pref.lower()): b=b[len(pref):].strip(' -–')
    s=slugify(b)
    return s or f"route-{d.get('rota_no',1)}"

def route_title_en(d, city):
    tema=d.get('tema')
    if tema and tema in THEME_SLUG:
        words=THEME_SLUG[tema].replace('-',' ').title().replace(' And ',' and ')
        return f"{CITY_EN.get(city,city)} walking route: {words}"
    bolge=d.get('bolge')
    if bolge and bolge in THEME_SLUG:
        words=THEME_SLUG[bolge].replace('-',' ').title().replace(' And ',' and ')
        return f"{CITY_EN.get(city,city)} walking route: {words}"
    return f"{CITY_EN.get(city,city)} walking route"

def fmt_dur(sure_sn):
    if not sure_sn and sure_sn!=0: return 'No info'
    m=int(round(sure_sn/60))
    return f"{m} min"

def fmt_dist(km):
    try: return f"{float(km):.2f} km"
    except: return 'No info'

def helper_summary(aralar):
    n=sum(1 for a in aralar if a.get('yardimci_durak'))
    return f"{n} toilet/water point(s)" if n else "0 toilet/water points"

def build_page(d, city, slug, new_slug, no_helper_removed=False):
    stops = d.get('rota',{}).get('ana_duraklar',[])
    aralar = d.get('rota',{}).get('aralar',[])
    geom = d.get('rota',{}).get('geometri',[])
    city_en = CITY_EN.get(city, city.title())
    title = route_title_en(d, city)
    dist = fmt_dist(d.get('rota',{}).get('toplam_mesafe_km'))
    dur = fmt_dur(d.get('rota',{}).get('toplam_sure_sn'))
    helpers_n = sum(1 for a in aralar if a.get('yardimci_durak'))
    desc = f"Walking route in {city_en}: {title.split(': ',1)[-1]}. {dist}, {dur}, {len(stops)} stops, map, toilets and water points."
    canon = f"{SITE}/routes/{city}/{new_slug}/"
    # stops html
    shtml=[]
    for s in stops:
        nm=en_name(s.get('ad','Stop'))
        tur=en_type(s.get('tur'))
        saat=s.get('saat') or 'No info'
        ucret=s.get('ucret') or 'No info'
        er=s.get('erisilebilirlik') or 'No info'
        if saat=='bilgi yok': saat='No info'
        if ucret=='bilgi yok': ucret='No info'
        if er=='bilgi yok': er='No info'
        extra=''
        if s.get('icinde'):
            inside=', '.join(en_name(x) for x in s['icinde'])
            extra=f"<div class=\"note\">Inside: {html_escape(inside)}</div>"
        shtml.append(f"<div class=\"stop\"><b><span class=\"n\">{s.get('sira','')}</span>{html_escape(nm)}</b> <span class=\"t\">{html_escape(tur)}</span><div class=\"note\">Hours: {html_escape(str(saat))} · Fee: {html_escape(str(ucret))} · Accessibility: {html_escape(str(er))}</div>{extra}</div>")
    # segments
    rows=[]
    for a in aralar:
        h=a.get('yardimci_durak')
        if isinstance(h,dict):
            hname=en_name(h.get('ad') or h.get('name') or 'Toilet/water point')
            hkind=en_kind(h.get('kind') or h.get('tur'))
            hdist=h.get('mesafe_m') or h.get('rota_uzaklik_m')
            hdist_s = (f"{float(hdist):.0f} m") if hdist is not None else 'on route'
            hcell=f"{html_escape(hname)} ({html_escape(hkind)}, {hdist_s})"
        elif isinstance(h,str) and h.strip():
            hcell=html_escape(en_name(h.strip()))
        else:
            hcell='—'
        a_nm=en_name(a.get('baslangic',''))
        b_nm=en_name(a.get('bitis',''))
        rows.append(f"<tr><td>{a.get('sira','')}</td><td>{html_escape(a_nm)} → {html_escape(b_nm)}</td><td>{fmt_dist(a.get('mesafe_km'))}</td><td>{fmt_dur(a.get('sure_sn'))}</td><td>{hcell}</td></tr>")
    seg_html = '<table><thead><tr><th>#</th><th>From → To</th><th>Distance</th><th>Time</th><th>Helper stop</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>' if rows else '<p class="note">No segment data.</p>'
    # helper points table
    hrows=[]
    for a in aralar:
        h=a.get('yardimci_durak')
        if not h: continue
        if isinstance(h,str):
            hrows.append(f"<tr><td>{html_escape(en_name(h.strip()))}</td><td><span class=\"t f\">Toilet/rest stop</span></td><td>On/near route</td><td>No info / No info</td></tr>")
            continue
        if not isinstance(h,dict): continue
        hname=en_name(h.get('ad') or h.get('name') or 'Toilet/water point')
        hkind=en_kind(h.get('kind') or h.get('tur'))
        hdist=h.get('mesafe_m') or h.get('rota_uzaklik_m')
        hdist_s = (f"{float(hdist):.0f} m from route") if hdist is not None else 'near route'
        saat=h.get('hours') or h.get('saat') or 'No info'
        ucret=h.get('fee') or h.get('ucret') or 'No info'
        if saat=='bilgi yok': saat='No info'
        if ucret=='bilgi yok': ucret='No info'
        hrows.append(f"<tr><td>{html_escape(hname)}</td><td><span class=\"t f\">{html_escape(hkind)}</span></td><td>{hdist_s}</td><td>{html_escape(str(saat))} / {html_escape(str(ucret))}</td></tr>")
    helper_html = ('<table><thead><tr><th>Place</th><th>Type</th><th>From route</th><th>Hours / fee</th></tr></thead><tbody>'+''.join(hrows)+'</tbody></table>') if hrows else '<p class="note">No helper toilet/water stop listed within route rules for this route.</p>'
    # map data
    pts=[[p[0],p[1]] for p in geom] if geom else []
    ms=[{"lat":s.get('lat'),"lon":s.get('lon'),"ad":en_name(s.get('ad','')),"sira":s.get('sira')} for s in stops]
    hs=[]
    for a in aralar:
        h=a.get('yardimci_durak')
        if isinstance(h,dict) and h.get('lat') is not None and h.get('lon') is not None:
            hs.append({"lat":h['lat'],"lon":h['lon'],"ad":en_name(h.get('ad') or h.get('name') or ''),"tur":en_kind(h.get('kind') or h.get('tur'))})
    import json as _j
    ptsj=_j.dumps(pts); msj=_j.dumps(ms, ensure_ascii=False); hsj=_j.dumps(hs, ensure_ascii=False)
    schema = {
        "@context":"https://schema.org","@type":"TouristTrip",
        "name": title,
        "description": desc,
        "touristType":"Walking",
        "itinerary":{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":s.get('sira',i+1),"item":{"@type":"TouristAttraction","name":en_name(s.get('ad',''))}} for i,s in enumerate(stops)]},
        "provider":{"@type":"Organization","name":"Laloo","url":"https://laloo.org"}
    }
    schema_j=_j.dumps(schema, ensure_ascii=False)
    page=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(title)} · Laloo</title><meta name="description" content="{html_escape(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{html_escape(title)}"><meta property="og:description" content="{html_escape(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/favicon-512.png"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><meta name="theme-color" content="#fefef8">
<script type="application/ld+json">{schema_j}</script>
<style>:root{{--navy:#10223d;--blue:#1c4fa0;--line:#e6e1d4;--bg:#fefef8;--muted:#5f6b7d;--card:#fff;--green:#1b7a3a;--greenbg:#e3f6e8;--tag:#e8f0fb}}
@media (prefers-color-scheme:dark){{:root{{--navy:#e9eef6;--blue:#8fb4ff;--line:#2a3445;--bg:#111722;--muted:#9aa6b8;--card:#172030;--green:#7fd79a;--greenbg:#1d3326;--tag:#1f2e48}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--navy);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}a{{color:var(--blue)}}
header{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 16px;border-bottom:1px solid var(--line)}}
header img{{height:34px;display:block;border-radius:8px}}@media (prefers-color-scheme:dark){{header img{{background:#fefef8;padding:2px 6px;height:38px}}}}
main{{max-width:860px;margin:0 auto;padding:18px 16px 40px}}h1{{font-size:28px;line-height:1.2;margin:8px 0 10px}}h2{{font-size:20px;margin:28px 0 8px}}
.stat{{color:var(--muted);font-size:14px;margin:0 0 16px}}.note{{color:var(--muted);font-size:14px}}
.stop{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:0 0 10px}}
.stop .n{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#1c4fa0;color:#fff;font-weight:700;font-size:13px;margin-right:8px}}
.t{{display:inline-block;font-size:12px;font-weight:700;padding:2px 7px;border-radius:8px;margin:4px 4px 0 0;background:var(--tag);color:var(--blue)}}
.t.f{{background:var(--greenbg);color:var(--green)}}
ul.rl{{list-style:none;padding:0;margin:0}}.rl li{{margin:0 0 10px}}.rl a{{font-weight:700}}.rl span{{display:block;color:var(--muted);font-size:14px}}
#map{{height:360px;border:1px solid var(--line);border-radius:12px;margin:12px 0;background:#eef3f8}}
table{{width:100%;border-collapse:collapse;margin:8px 0}}th,td{{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left;font-size:14px;vertical-align:top}}th{{color:var(--muted);font-weight:700}}
footer{{max-width:860px;margin:0 auto;padding:18px 16px 40px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
svg.route{{width:100%;height:auto;border:1px solid var(--line);border-radius:12px;background:#f5f7fa;margin:12px 0}}
</style></head><body>
<header><a href="/"><img src="/logo-header.png" alt="LALOO" width="120" height="34"></a><nav><a href="/routes/">Routes</a> · <a href="/routes/{city}/">{html_escape(city_en)}</a></nav></header>
<main>
<h1>{html_escape(title)}</h1>
<p class="stat">{dist} · {dur} · {len(stops)} stops · {helpers_n} toilet/water point(s)</p>
{svg_route(geom, ms, hs)}
<div id="map"></div>
<noscript><p class="note">Interactive map requires JavaScript. Route line and stops are shown above.</p></noscript>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" defer></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" media="print" onload="this.media='all'">
<script>(function(){{function init(){{if(!window.L)return;var pts={ptsj};var ms={msj};var hs={hsj};var map=L.map('map');L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}}).addTo(map);var layers=[];if(pts.length){{var line=L.polyline(pts,{{color:'#1c4fa0',weight:4}}).addTo(map);layers.push(line);}}ms.forEach(function(m){{if(m.lat==null)return;var mk=L.marker([m.lat,m.lon]).addTo(map).bindPopup((m.sira?m.sira+'. ':'')+m.ad);layers.push(mk);}});hs.forEach(function(m){{if(m.lat==null)return;var mk=L.circleMarker([m.lat,m.lon],{{radius:6,color:'#1b7a3a'}}).addTo(map).bindPopup((m.ad||'')+' ('+(m.tur||')+')');layers.push(mk);}});if(layers.length){{map.fitBounds(L.featureGroup(layers).getBounds().pad(0.15));}}else{{map.setView([0,0],2);}}}}if(document.readyState==='loading'){{document.addEventListener('DOMContentLoaded',function(){{setTimeout(init,200)}});}}else{{setTimeout(init,200);}}}})();</script>

<h2>Stops</h2>
{''.join(shtml) or '<p class="note">No stops listed.</p>'}
<h2>Segments</h2>
{seg_html}
<h2>Toilets and water on or near route</h2>
{helper_html}
<p class="note">Attribution: © OpenStreetMap contributors. Stop selection informed by Wikivoyage where noted (CC BY-SA 4.0).</p>
</main>
<footer><a href="/">laloo.org</a> · <a href="/routes/">Routes</a> · <a href="/routes/{city}/">{html_escape(city_en)} routes</a> · © OpenStreetMap contributors · Wikivoyage (CC BY-SA) where used</footer>
</body></html>'''
    return page

def svg_route(geom, ms, hs):
    if not geom or len(geom)<2:
        return '<svg class="route" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg"><text x="20" y="100" fill="#5f6b7d">Route map unavailable</text></svg>'
    lats=[p[0] for p in geom]+[m['lat'] for m in ms if m.get('lat') is not None]
    lons=[p[1] for p in geom]+[m['lon'] for m in ms if m.get('lon') is not None]
    minlat,maxlat=min(lats),max(lats); minlon,maxlon=min(lons),max(lons)
    if maxlat-minlat<1e-6: maxlat+=0.001; minlat-=0.001
    if maxlon-minlon<1e-6: maxlon+=0.001; minlon-=0.001
    w,h,pad=800,360,30
    def proj(lat,lon):
        x=pad + (lon-minlon)/(maxlon-minlon)*(w-2*pad)
        y=pad + (maxlat-lat)/(maxlat-minlat)*(h-2*pad)
        return x,y
    pts=' '.join(f"{proj(p[0],p[1])[0]:.1f},{proj(p[0],p[1])[1]:.1f}" for p in geom)
    circles=[]
    for m in ms:
        if m.get('lat') is None: continue
        x,y=proj(m['lat'],m['lon']); n=m.get('sira','')
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#1c4fa0"/><text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="11" font-family="system-ui,sans-serif" fill="#fff" font-weight="700">{n}</text>')
    for hpt in hs:
        if hpt.get('lat') is None: continue
        x,y=proj(hpt['lat'],hpt['lon'])
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#1b7a3a" stroke="#fff" stroke-width="2"/>')
    return f'<svg class="route" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Route diagram"><rect width="100%" height="100%" fill="#f5f7fa"/><polyline points="{pts}" fill="none" stroke="#1c4fa0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>{"".join(circles)}</svg>'

def html_escape(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def make_redirect(target):
    canon=SITE+target
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{canon}"><meta name="robots" content="noindex"><title>Redirecting…</title></head><body><p>Redirecting to <a href="{target}">{html_escape(canon)}</a>.</p></body></html>'

def write_file(p, content):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

def main():
    # collect approved
    routes=[]
    for p in sorted(ROUTES_DATA.glob('*/rota-*.json')):
        d=json.load(open(p))
        if d.get('durum')!='onaylandı': continue
        city=p.parent.name
        routes.append({'city':city,'path':p,'d':d})
    # determine slugs per city
    by_city={}
    for r in routes: by_city.setdefault(r['city'],[]).append(r)
    removed=[]
    kept=[]
    for city, lst in by_city.items():
        for r in lst:
            r['new_slug']=route_slug(r['d'], city)
    # try 300m helper for 0-helper routes
    for r in list(routes):
        d=r['d']; city=r['city']
        aralar=d.get('rota',{}).get('aralar',[])
        helpers=sum(1 for a in aralar if a.get('yardimci_durak'))
        if helpers==0:
            geom=d.get('rota',{}).get('geometri',[])
            toilets=load_toilets(city)
            if toilets and geom:
                best=nearest_to_polyline(toilets, geom)
                if best and best[0] <= 300:
                    dist_m,t,seg_i=best
                    seg = aralar[seg_i] if seg_i < len(aralar) else (aralar[0] if aralar else None)
                    if seg is not None:
                        seg['yardimci_durak'] = {
                            'ad': t.get('name') or 'Public toilet',
                            'kind': t.get('kind') or 'public',
                            'lat': t.get('lat'), 'lon': t.get('lng'),
                            'mesafe_m': round(dist_m,1),
                            'saat': t.get('info') or 'No info',
                            'ucret': t.get('fee') or 'No info',
                            'kaynak': t.get('_kaynak') or t.get('source') or 'local',
                        }
                        d.setdefault('notlar',[]).append('G59: helper toilet added within 300 m (automated).')
            helpers=sum(1 for a in aralar if a.get('yardimci_durak'))
            if helpers==0:
                removed.append({'city':city,'route_no':d.get('rota_no'),'tema':d.get('tema') or d.get('bolge'),'path':str(r['path'])})
                r['drop']=True
    kept=[r for r in routes if not r.get('drop')]
    # regenerate pages: remove old city dirs for approved route pages we manage? safer: remove all routes/* except fixed editorial slugs
    keep_editorial={'eiffel-tower-to-louvre-bathrooms','santa-monica-to-venice-beach-bathrooms','midtown-manhattan-bathrooms-walk','istanbul-old-city-toilets-sultanahmet-grand-bazaar'}
    # remove generated city dirs
    for child in list(OUT.iterdir()):
        if not child.is_dir(): continue
        name=child.name
        if name in keep_editorial: continue
        shutil.rmtree(child)
    # build kept pages and redirects
    by_city2={}
    for r in kept: by_city2.setdefault(r['city'],[]).append(r)
    all_route_urls=[]
    for city, lst in sorted(by_city2.items()):
        lst=sorted(lst, key=lambda x: (x['d'].get('rota_no') or 0))
        city_en=CITY_EN.get(city,city.title())
        city_dir=OUT/city
        route_links=[]
        for r in lst:
            d=r['d']; new_slug=r['new_slug']
            rn=d.get('rota_no')
            old=f"rota-{rn if rn is not None else 1}"
            page=build_page(d, city, old, new_slug)
            target_dir=city_dir/new_slug
            write_file(target_dir/'index.html', page)
            all_route_urls.append(f"/routes/{city}/{new_slug}/")
            if old!=new_slug:
                write_file(city_dir/old/'index.html', make_redirect(f"/routes/{city}/{new_slug}/"))
            title=route_title_en(d,city).split(': ',1)[-1]
            dist=fmt_dist(d.get('rota',{}).get('toplam_mesafe_km'))
            dur=fmt_dur(d.get('rota',{}).get('toplam_sure_sn'))
            route_links.append(f"<li><a href=\"/routes/{city}/{new_slug}/\">{html_escape(title)}</a><span>{dist} · {dur} · {len(d.get('rota',{}).get('ana_duraklar',[]))} stops</span></li>")
        # city index
        canon=f"{SITE}/routes/{city}/"
        cpage=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(city_en)} walking routes · Laloo</title><meta name="description" content="Walking routes in {html_escape(city_en)} with maps, stops, distances, times, and nearby toilets/water points.">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{html_escape(city_en)} walking routes · Laloo"><meta property="og:description" content="Walking routes in {html_escape(city_en)} with maps, stops, distances, times, and nearby toilets/water points."><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/favicon-512.png"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><meta name="theme-color" content="#fefef8">
<style>body{{margin:0;background:#fefef8;color:#10223d;font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}a{{color:#1c4fa0}}header{{padding:10px 16px;border-bottom:1px solid #e6e1d4}}main{{max-width:760px;margin:0 auto;padding:18px 16px 40px}}ul{{list-style:none;padding:0}}li{{margin:0 0 12px}}li span{{display:block;color:#5f6b7d;font-size:14px}}footer{{max-width:760px;margin:0 auto;padding:18px 16px 40px;border-top:1px solid #e6e1d4;color:#5f6b7d;font-size:13px}}</style></head><body>
<header><a href="/"><img src="/logo-header.png" alt="LALOO" width="120" height="34"></a> <a href="/routes/">Routes</a></header>
<main><h1>{html_escape(city_en)} walking routes</h1><ul class="rl">{''.join(route_links)}</ul></main>
<footer><a href="/">laloo.org</a> · <a href="/routes/">Routes</a> · © OpenStreetMap contributors · Wikivoyage (CC BY-SA) where used</footer></body></html>'''
        write_file(city_dir/'index.html', cpage)
    # routes index
    editorial_items = [
        ("/routes/santa-monica-to-venice-beach-bathrooms/","Santa Monica to Venice Beach: every bathroom on the way"),
        ("/routes/midtown-manhattan-bathrooms-walk/","Midtown Manhattan on foot: bathroom stops from Bryant Park to Rockefeller Center"),
        ("/routes/eiffel-tower-to-louvre-bathrooms/","Eiffel Tower to the Louvre: a Paris walk with bathroom stops"),
        ("/routes/istanbul-old-city-toilets-sultanahmet-grand-bazaar/","Istanbul's old city on foot: toilet stops from Sultanahmet to the Spice Bazaar"),
    ]
    ehtml=''.join(f'<li><a href="{u}">{html_escape(t)}</a></li>' for u,t in editorial_items)
    city_items=[]
    for city, lst in sorted(by_city2.items()):
        city_en=CITY_EN.get(city,city.title())
        city_items.append(f'<li><a href="/routes/{city}/">{html_escape(city_en)} routes</a><span>{len(lst)} route(s)</span></li>')
    canon=f"{SITE}/routes/"
    ipage=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bathroom routes & walking guides · Laloo</title><meta name="description" content="Walking routes and guides with bathroom stops, maps, distances and times.">
<link rel="canonical" href="{canon}"><meta property="og:title" content="Bathroom routes & walking guides · Laloo"><meta property="og:url" content="{canon}"><meta property="og:image" content="{SITE}/favicon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><meta name="theme-color" content="#fefef8">
<style>body{{margin:0;background:#fefef8;color:#10223d;font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}a{{color:#1c4fa0}}header{{padding:10px 16px;border-bottom:1px solid #e6e1d4}}main{{max-width:760px;margin:0 auto;padding:18px 16px 40px}}h1{{font-size:28px}}h2{{font-size:20px;margin-top:26px}}ul{{list-style:none;padding:0}}li{{margin:0 0 10px}}li span{{display:block;color:#5f6b7d;font-size:14px}}footer{{max-width:760px;margin:0 auto;padding:18px 16px 40px;border-top:1px solid #e6e1d4;color:#5f6b7d;font-size:13px}}</style></head><body>
<header><a href="/"><img src="/logo-header.png" alt="LALOO" width="120" height="34"></a></header>
<main><h1>Bathroom routes &amp; walking guides</h1>
<h2>Guides</h2><ul class="rl">{ehtml}</ul>
<h2>City route lists</h2><ul class="rl">{''.join(city_items) if city_items else '<li>No approved routes yet.</li>'}</ul></main>
<footer><a href="/">laloo.org</a> · <a href="/cities/">All cities</a> · © OpenStreetMap contributors · Wikivoyage (CC BY-SA) where used</footer></body></html>'''
    write_file(OUT/'index.html', ipage)
    # sitemap: keep non-routes entries, replace routes block to only kept routes + city lists + editorial
    sm_path=REPO/'sitemap.xml'
    sm=sm_path.read_text(encoding='utf-8') if sm_path.exists() else ''
    # remove existing route-generated url blocks we manage? easier rebuild routes section by filtering
    # keep all <url>..</url> not starting with https://www.laloo.org/routes/ except editorial? we'll preserve editorial and rebuild others
    urls = re.findall(r'<url>.*?</url>', sm, flags=re.S)
    kept_urls=[]
    for u in urls:
        locm=re.search(r'<loc>(.*?)</loc>', u)
        loc=locm.group(1) if locm else ''
        if loc.startswith(f'{SITE}/routes/'):
            # keep editorial
            if any(loc.rstrip('/').endswith(e.rstrip('/')) for e,_ in editorial_items):
                kept_urls.append(u)
            # drop all other route urls (city lists and generated)
            continue
        # also convert old laloo.org canonicals? leave as-is
        if loc.startswith('https://laloo.org/routes/'):
            # normalize editorial if somehow
            newloc=loc.replace('https://laloo.org', SITE)
            if any(newloc.rstrip('/').endswith(e.rstrip('/')) for e,_ in editorial_items):
                kept_urls.append(u.replace(loc,newloc))
            continue
        kept_urls.append(u)
    # append new routes
    for city in sorted(by_city2.keys()):
        kept_urls.append(f'<url><loc>{SITE}/routes/{city}/</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>')
    for u in sorted(all_route_urls):
        kept_urls.append(f'<url><loc>{SITE}{u}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    new_sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(kept_urls)+'\n</urlset>\n'
    sm_path.write_text(new_sm, encoding='utf-8')

    # report
    print('KEPT',len(kept))
    print('REMOVED',len(removed))
    for r in removed:
        print('REMOVED_ITEM', json.dumps(r, ensure_ascii=False))
    return removed

if __name__=='__main__':
    main()
