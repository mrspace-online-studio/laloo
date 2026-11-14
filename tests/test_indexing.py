import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('indexing',Path(__file__).resolve().parents[1]/'tools/indexing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class IndexingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.config={'site':'https://example.com','indexnow_key':'a'*32,'exclude':['admin.html','item.html']}
  (self.root/'indexing.json').write_text(json.dumps(self.config));(self.root/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /admin.html\n')
  (self.root/'index.html').write_text('<head><title>Home</title></head>')
 def test_public_pages_and_noindex(self):
  for name,text in [('admin.html','private'),('rate.html','<meta content="noindex" name="robots">'),('old.html','<meta http-equiv="refresh" content="0;url=/">'),('terms.html','public')]: (self.root/name).write_text(text)
  self.assertEqual(set(m.build(self.root)),{'https://example.com/','https://example.com/terms.html'})
  self.assertIn('Disallow: /admin.html',(self.root/'robots.txt').read_text())
  m.build(self.root);self.assertEqual((self.root/'robots.txt').read_text().count('Sitemap:'),1)
 def test_catalog_addresses_escape_xml_and_ids(self):
  self.config['catalog_api']='https://catalog.example';(self.root/'indexing.json').write_text(json.dumps(self.config));(self.root/'item.html').write_text('template')
  pages=m.build(self.root,catalog={'items':[{'id':'a&b','title':'shirt'}]})
  self.assertIn('https://example.com/item.html?id=a%26b',pages)
 def test_catalog_failure_preserves_old_sitemap(self):
  (self.root/'sitemap.xml').write_text('old');self.config['catalog_api']='https://catalog.example';(self.root/'indexing.json').write_text(json.dumps(self.config))
  with self.assertRaises(ValueError): m.build(self.root,catalog={'error':'unavailable'})
  self.assertEqual((self.root/'sitemap.xml').read_text(),'old')
 def test_changed_and_deleted_urls(self):
  current=m.build(self.root);previous={**current,'https://example.com/deleted.html':'old'}
  (self.root/'index.html').write_text('new content')
  with patch.object(m,'request_json',return_value=previous): m.build(self.root,True)
  self.assertEqual(json.loads((self.root/'_indexnow-changes.json').read_text()),['https://example.com/','https://example.com/deleted.html'])
 def test_first_deployment_and_network_failure(self):
  with patch.object(m,'request_json',side_effect=HTTPError('x',404,'missing',{},None)): m.build(self.root,True)
  with patch.object(m,'request_json',side_effect=HTTPError('x',503,'down',{},None)):
   with self.assertRaises(HTTPError): m.build(self.root,True)
 def test_spa_fallback_without_prior_manifest(self):
  with patch.object(m,'request_json',return_value=None):
   m.build(self.root,True)
  self.assertEqual(json.loads((self.root/'_indexnow-changes.json').read_text()),['https://example.com/'])
 def test_shared_asset_change_affects_pages(self):
  (self.root/'app.js').write_text('version1');before=m.collect(self.root,self.config)
  (self.root/'app.js').write_text('version2');self.assertNotEqual(before,m.collect(self.root,self.config))
 def test_submit_refuses_unpublished_manifest(self):
  m.build(self.root)
  class Key:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return b'a'*32
  with patch.object(m,'urlopen',return_value=Key()) as net,patch.object(m,'request_json',return_value={}):
   with self.assertRaises(ValueError):m.submit(self.root)
   self.assertEqual(net.call_count,1)
 def test_submit_validated_post(self):
  expected=m.build(self.root)
  class Response:
   status=202
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return b'a'*32
  with patch.object(m,'urlopen',return_value=Response()) as net,patch.object(m,'request_json',return_value=expected):
   m.submit(self.root);request=net.call_args_list[-1].args[0]
   self.assertEqual(request.full_url,'https://api.indexnow.org/indexnow');self.assertEqual(request.method,'POST')
   self.assertEqual(json.loads(request.data)['urlList'],['https://example.com/'])

if __name__=='__main__':unittest.main()
