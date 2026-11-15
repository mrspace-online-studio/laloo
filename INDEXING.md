# İndeksleme

- Google etiketi ana sayfanın head bölümünde. Search Console doğrulaması ve Bing GSC içe aktarması yayın sonrası elle tamamlanacak.
- `python3 tools/indexing.py build` herkese açık HTML sayfalarından sitemap üretir; özel, noindex ve yönlendirme sayfaları hariçtir. Heron ürün adresleri açık katalogdan gelir; katalog okunamazsa derleme durur.
- `robots.txt` içindeki özel sayfa ve AI eğitim botu kuralları korunur.
- Pages kullanılıyorsa birleştirdikten sonra Settings → Pages → Build and deployment → Source: GitHub Actions seç. Yeni iş akışı PR'da yalnız derler; main üzerinde başarılı dağıtımdan sonra IndexNow bildirir. Laloo için mevcut sağlayıcı GitHub Pages olarak doğrulandı.
- Günlük derleme katalog değişikliklerini de alır. Laloo gece veri üreticisi başarılı tamamlandığında workflow_run tetikleyicisi yeni sayfaları yayınlar.
- `--compare-live` önceki yayındaki `indexing-manifest.json` ile karşılaştırır. İlk yayında (404 veya manifest yerine HTML geri dönüşü) tüm açık adresler; sonraki yayınlarda eklenen, değişen ve kaldırılan adresler bildirilir. Başka ağ hatası dağıtımı durdurur.
- `python3 tools/indexing.py submit` yalnız canlı anahtar dosyası ve manifest bu derlemeyle eşleşirse POST yapar. Bildirim kabulü indekslenme garantisi değildir.
- `_indexnow-changes.json` yalnız dağıtım artefaktıdır; repoya veya siteye konmaz.
