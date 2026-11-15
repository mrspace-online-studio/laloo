"""Build search metadata; notify IndexNow only after a successful deployment."""
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'

class Head(HTMLParser):
    def __init__(self):
        super().__init__(); self.noindex = False; self.redirect = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta':
            if a.get('name', '').lower() in ('robots', 'googlebot', 'bingbot') and 'noindex' in a.get('content', '').lower(): self.noindex = True
            if a.get('http-equiv', '').lower() == 'refresh': self.redirect = True

def request_json(url, data=None, allow_html=False):
    req = Request(url, data=None if data is None else json.dumps(data).encode(),
                  headers={'Content-Type': 'application/json', 'User-Agent': 'SiteIndexing/1.0'})
    with urlopen(req, timeout=45) as response:
        raw = response.read()
        # Cloudflare's SPA fallback serves index.html with 200 for missing paths.
        if allow_html and 'text/html' in response.headers.get('Content-Type', '').lower() and raw.lstrip().lower().startswith((b'<!doctype html', b'<html')):
            return None
        return json.loads(raw)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def collect(root, config, catalog=None):
    site = config['site'].rstrip('/'); pages = {}
    excluded = set(config.get('exclude', []))
    # Changes to shared JS/CSS can change the content of every public page.
    shared = b''.join(p.read_bytes() for p in sorted(root.rglob('*'))
                      if p.is_file() and p.suffix in ('.css', '.js') and not any(x.startswith(('.', '_')) or x in ('tools', 'tests', 'node_modules') for x in p.relative_to(root).parts))
    for p in sorted(root.rglob('*.html')):
        rel = p.relative_to(root).as_posix()
        if rel in excluded or any(x.startswith(('.', '_')) or x in ('tools', 'tests', 'node_modules') for x in p.relative_to(root).parts): continue
        content = p.read_bytes(); head = Head(); head.feed(content.decode('utf-8'))
        if head.noindex or head.redirect: continue
        path = rel[:-10] if rel.endswith('index.html') else rel
        pages[site + '/' + quote(path, safe='/')] = digest(content + shared)
    if config.get('catalog_api'):
        if catalog is None: catalog = request_json(config['catalog_api'], {'action': 'list'})
        if not isinstance(catalog, dict) or not isinstance(catalog.get('items'), list): raise ValueError('Invalid public catalog; sitemap was not replaced')
        template = (root / 'item.html').read_bytes()
        for item in catalog['items']:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']: raise ValueError('Invalid public item ID')
            url = site + '/item.html?id=' + quote(item['id'], safe='')
            pages[url] = digest(template + shared + json.dumps(item, sort_keys=True, ensure_ascii=False).encode())
    return dict(sorted(pages.items()))

def build(root, compare_live=False, catalog=None):
    config = json.loads((root / 'indexing.json').read_text()); site = config['site'].rstrip('/')
    pages = collect(root, config, catalog)
    if not pages: raise ValueError('No public pages; refusing empty sitemap')
    previous = {}
    if compare_live:
        try:
            previous = request_json(site + '/indexing-manifest.json', allow_html=True)
            if previous is None: previous = {}
            if not isinstance(previous, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in previous.items()): raise ValueError('Invalid published manifest')
        except HTTPError as error:
            if error.code != 404: raise
            # First deployment: notify all current public URLs.
    changes = sorted(u for u in pages.keys() | previous.keys() if pages.get(u) != previous.get(u))
    ET.register_namespace('', NS); tree = ET.Element('{%s}urlset' % NS)
    for url in pages:
        node = ET.SubElement(tree, '{%s}url' % NS); ET.SubElement(node, '{%s}loc' % NS).text = url
    ET.indent(tree)
    (root / 'sitemap.xml').write_bytes(ET.tostring(tree, encoding='utf-8', xml_declaration=True) + b'\n')
    robots = root / 'robots.txt'
    lines = [line for line in robots.read_text().splitlines() if not line.lower().startswith('sitemap:')]
    robots.write_text('\n'.join(lines).rstrip() + '\n\nSitemap: ' + site + '/sitemap.xml\n')
    (root / 'indexing-manifest.json').write_text(json.dumps(pages, indent=2) + '\n')
    (root / '_indexnow-changes.json').write_text(json.dumps(changes) + '\n')
    print(f'{len(pages)} public URLs; {len(changes)} changed URLs')
    return pages

def submit(root):
    config = json.loads((root / 'indexing.json').read_text()); site = config['site'].rstrip('/')
    key = config['indexnow_key']; host = urlparse(site).netloc
    if len(key) != 32 or any(c not in '0123456789abcdef' for c in key): raise ValueError('Invalid IndexNow key')
    key_url = site + '/' + key + '.txt'
    with urlopen(Request(key_url, headers={'User-Agent': 'SiteIndexing/1.0'}), timeout=30) as response:
        if response.read().decode().strip() != key: raise ValueError('Published IndexNow key does not match')
    # Never submit URLs before the exact built manifest has reached production.
    expected = json.loads((root / 'indexing-manifest.json').read_text())
    if request_json(site + '/indexing-manifest.json') != expected: raise ValueError('Production manifest differs from this build; no URLs submitted')
    urls = json.loads((root / '_indexnow-changes.json').read_text())
    if not isinstance(urls, list): raise ValueError('Invalid URL list')
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != host or parsed.fragment: raise ValueError('URL is outside the site')
    for start in range(0, len(urls), 10000):
        batch = urls[start:start + 10000]
        req = Request('https://api.indexnow.org/indexnow', data=json.dumps({'host': host, 'key': key, 'keyLocation': key_url, 'urlList': batch}).encode(), headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'SiteIndexing/1.0'}, method='POST')
        try:
            with urlopen(req, timeout=45) as response:
                if response.status not in (200, 202): print(f'::warning::IndexNow status {response.status}; sitemap remains the source of truth'); continue
        except HTTPError as e:
            print(f'::warning::IndexNow rejected the submission (HTTP {e.code}); sitemap remains the source of truth'); continue
        print(f'IndexNow accepted {len(batch)} URLs (indexing is not guaranteed)')
    if not urls: print('No changed URLs to submit')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'submit'])
    parser.add_argument('--compare-live', action='store_true')
    parser.add_argument('--catalog-file', type=Path, help='Saved public catalog for offline validation')
    args = parser.parse_args()
    if args.action == 'build': build(ROOT, args.compare_live, json.loads(args.catalog_file.read_text()) if args.catalog_file else None)
    else: submit(ROOT)
