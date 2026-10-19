> **Canlı test alanı:** [FTP üzerinden çalışan mobil panel](https://duvar.applerehberi.com/mackolik-api-lab/) · [Sunucudan gerçek zamanlı JSON HTTP durumları](https://duvar.applerehberi.com/mackolik-api-lab/remote_probe.php) · [Erişim analizi](docs/AUTH_DISCOVERY.md). Türkiye hostingine FTP aktarımı ve PHP çalışması GitHub loglarında doğrulandı. Mevcut cevap **HTTP 403 Access Denied**; bu, futbol istatistiği verisi değildir.

# ⚽ Maçkolik API Lab

**GitHub Actions üstünde çalışan, telefondan takip edilebilen veri kaynağı teşhis laboratuvarı.** Maçkolik Android 8.5.4 statik analiziyle bulunan maç, oyuncu, kadro ve şut istatistiği endpointlerinin ağ ve JSON erişimini küçük hacimli, **yetkisiz kimlik doğrulama taklidi yapmayan** denemelerle kontrol eder.

> **Durum: İlk gerçek GitHub Actions testlerinde `HTTP 403 / Access Denied` ve `text/html` alındı; maç ve oyuncu JSON verisi henüz gelmedi.** İstek yolları APK'den elde edilmiştir fakat gerçek veri döndürdükleri veya serbest kullanıma açık oldukları kanıtlanmamıştır. Maçkolik'in kullanım koşullarını / veri lisansını ayrıca kontrol et.

## Telefonda nasıl çalıştırılır?

GitHub deposunda **Actions → ⚽ Maçkolik API - Ağ ve JSON Testi → Run workflow**. Varsayılan `smoke` iki ayrı GET isteği yapar: bugünün maçları ve `Harry Winks` araması. Ayrıntılı adımlar için [Mobil kılavuz](docs/MOBILE.md).

**Sonuçları görüntüle:** Her çalışma GitHub **Summary** panelinde HTTP durum/süre/JSON şema özetini verir. [Son durum](reports/SON_DURUM.md) ve [JSON](data/latest.json) her başarılı çalışmanın ardından depoda güncellenir. [Geçmiş](data/history.jsonl) son 384 turla sınırlandırılır. Çalışmanın **Artifacts** bölümündeki `mackolik-diagnostics-...` arşivinden `diagnostics.json` indirip [web/index.html](web/index.html) dosyasıyla yerel mobil panelde açabilirsin.

**Loglama:** `--verbose` ile DEBUG, UTC zaman damgası, URL ve GET parametreleri (id ve arama terimi), HTTP durum kodu, milisaniye, gelen bayt, güvenli HTTP başlıkları, JSON alan yolları ve toplam şut adayı. Tam sunucu HTTP başlıkları, cookies, tokens ve yetkilendirme bilgileri **asla basılmaz**; JSON örneklerinde hassas anahtarlar ayıklanır. Yanıt gövdesinin tamamı loglara basılmaz, saklanan örnekler limitlidir.

**Otomatik test:** 10 dakikada bir (UTC :07, :17, :27, :37, :47, :57) 2 istek; yalnızca erişim teşhisi, yüksek frekanslı scraping yok. Planlanan çalıştırmalar GitHub'ın tarifesine ve erişim koşullarına bağlıdır. Log ve JSON artefaktları 30 gün saklanır.

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
- `web/index.html`: barındırıldığında GitHub'daki son JSON raporunu otomatik okuyan mobil durum paneli
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

## İlk doğrulanan sonuç (19 Ekim 2026)

GitHub Actions sunucusu **2 GET** isteği yaptı: `/api/matches/` ve `/soccer/api/search/`. Her ikisi de **HTTP 403**, `Content-Type: text/html`, HTML hata açıklaması `Access Denied`. İsteklere JSON dönmedi. Bu, APK'den bulunan yolların serbest erişilebilir olduğu anlamına gelmez. Erişim gereklilikleri yetkisiz aşılmayacak. Testler 15 dakikalık schedule'a ayarlı, GitHub çalıştırma gecikmeleri olabilir.

**FTP dağıtımı:** Doğru hosting için kullanılabilir FTP kimlik bilgileri bulunmadığından yapılmadı. Test amaçlı `php/public_probe.php` hazır; depo sonucunun otomatik yayımlanması FTP gerektirmiyor.

## Android emülatörü (yeni)

Gerçek Android 15 emülatörü başarıyla başlatıldı; ABI listesinde Maçkolik split APK'nin `arm64-v8a` mimarisi yer alıyor. Orijinal APK'nin çalıştırılması için, büyük yükleme dosyasını herkese açık repoya koymadan erişilebilecek özel bir APK kaynağı gerekiyor. [Emülatör kanıtı ve normal APK testi](docs/EMULATOR_TEST.md).

**İstek aralığı:** 10 dakikalık kontrol planı devam eder; erişim reddi sürüyorsa üçüncü taraf API'ye gereksiz denemeleri 60 dakikada bire düşüren koruma etkindir. Gerçek maç istatistiği JSON'u henüz alınmadı.


## Google Play üzerinden APK yükleme testi (19 Ekim 2026)

[Android 15 Google Play sistem imajı testi](docs/PLAY_STORE_TEST.md) başarıyla koştu; mağaza kurulu, fakat **Google hesabı oturum açma ekranı** görüldü. **Maçkolik uygulaması kurulu değil; API verisi gelmedi.** İlk gerçek uygulama testine orijinal imzalı ZIP kaynağı sağlandığında devam edilebilir.
