# ⚽ Maçkolik API Lab

**GitHub Actions üstünde çalışan, telefondan takip edilebilen veri kaynağı teşhis laboratuvarı.** Maçkolik Android 8.5.4 statik analiziyle bulunan maç, oyuncu, kadro ve şut istatistiği endpointlerinin ağ ve JSON erişimini küçük hacimli, **yetkisiz kimlik doğrulama taklidi yapmayan** denemelerle kontrol eder.

> **Durum: Keşif / canlı API verisi doğrulanmadı.** İstek yolları APK'den elde edilmiştir fakat gerçek veri döndürdükleri veya serbest kullanıma açık oldukları kanıtlanmamıştır. Maçkolik'in kullanım koşullarını / veri lisansını ayrıca kontrol et.

## Telefonda nasıl çalıştırılır?

GitHub deposunda **Actions → ⚽ Maçkolik API - Ağ ve JSON Testi → Run workflow**. Varsayılan `smoke` iki ayrı GET isteği yapar: bugünün maçları ve `Harry Winks` araması. Ayrıntılı adımlar için [Mobil kılavuz](docs/MOBILE.md).

**Sonuçları görüntüle:** Her çalışma GitHub **Summary** panelinde HTTP durum/süre/JSON şema özetini verir. Çalışmanın **Artifacts** bölümündeki `mackolik-diagnostics-...` arşivinden `diagnostics.json` indirip [web/index.html](web/index.html) dosyasıyla yerel mobil panelde açabilirsin.

**Loglama:** `--verbose` ile DEBUG, UTC zaman damgası, URL ve GET parametreleri (id ve arama terimi), HTTP durum kodu, milisaniye, gelen bayt, güvenli HTTP başlıkları, JSON alan yolları ve toplam şut adayı. Tam sunucu HTTP başlıkları, cookies, tokens ve yetkilendirme bilgileri **asla basılmaz**; JSON örneklerinde hassas anahtarlar ayıklanır. Yanıt gövdesinin tamamı loglara basılmaz, saklanan örnekler limitlidir.

**Otomatik test:** 6 saatte bir 2 istek; yalnızca erişim teşhisi, yüksek frekanslı scraping yok. Planlanan çalıştırmalar GitHub'ın tarifesine ve erişim koşullarına bağlıdır. Log ve JSON artefaktları 30 gün saklanır.

## PHP ile kullanmak

`php/mackolik_client.php`, aynı allowlist endpointlerini PHP cURL ile test edebilir. Kullanım örnekleri:

```bash
php php/mackolik_client.php matches
php php/mackolik_client.php search 'Harry Winks'
php php/mackolik_client.php player_stats <gercek_match_mid> <gercek_player_mid>
```

**Bu henüz doğrulanmış bir üretim veri sağlayıcısı değildir.** Erişim izni ve JSON alanları kanıtlandıktan sonra PHP cron sistemine entegre edilir.

## Bilgisayar gerektirmeyen test altyapısı

- `.github/workflows/probe.yml`: manuel mobil seçim + 6 saatlik teşhis
- `.github/workflows/ci.yml`: kod testleri (API'ye istek atmaz)
- `scripts/probe.py`: hiçbir harici Python paketi gerektirmeyen GET/JSON istemcisi
- `tests/test_probe.py`: mock verilerle toplam şutun isabetli şuttan ayrılması ve veri gizliliği testleri
- `web/index.html`: offline, mobil uyumlu JSON teşhis paneli
- `php/mackolik_client.php`: ilerideki PHP cron için kontrol adapteri
- [docs/API_MAP.md](docs/API_MAP.md): APK'den doğrulanmış yol/parametre envanteri

## Şut / son 5 maç hedefi

Hedef `1-0-2-5-1` gibi **toplam şut** dizisi. Şu an `player_stats` yanıtındaki `name`/`value` üzerinden yalnızca şut adayı çıkartılır; canlı JSON alanları kanıtlanmadan son 5 maç otomasyonu yapılmaz. **0 şut ile bulunamayan veri null farklıdır.** Resmî ve muhtemel ilk 11 alanları APK'de tespit edildi fakat canlı yanıt doğrulaması gerekiyor.

## Sınırlar ve güvenlik

- APK/uygulama dosyası, gizli anahtar, cookie veya token bu depoya konmaz.
- 401, 403 veya 429 alınırsa erişim mekanizmasını aşmayı denemez; sonucu teşhis olarak kaydeder.
- Kaydedilmiş örnek veriler redakte/limitlidir, testler yalnızca GET kullanır, takip eden yönlendirmeler kapalıdır.
- Örnek `tests/fixtures/player_stats.json` gerçek Maçkolik yanıtı değil, **temsili unit test verisidir**.
- Bu proje hiçbir bahis oynamaz, kupon göndermez, bahis otomasyonu yapmaz.

> **Gizlilik:** Depo şu anda herkese açık görünüyor. Özel veriler, anahtarlar ve erişim tokenları burada paylaşılmaz.
