# Android 8.5.4: erişim koşulları ve doğrulama kayıtları

## Gerçek testler — 19 Ekim 2026

- GitHub Actions /api/matches ve /soccer/api/search: **HTTP 403**, `text/html`, **Access Denied**.
- Türkiye'deki kullanıcıya ait PHP hosting: aynı iki endpoint **HTTP 403**, **Access Denied**.
- PHP sunucusunda dosya gerçekten yürütüldü, FTP ayrı test klasörüne başarıyla dağıtıldı.
- Dolayısıyla **API'den canlı futbol JSON'u dönmedi**; 403'ün yalnızca GitHub kaynaklı olduğunu söyleyemeyiz.

## APK içinde kanıtlanan parçalar

- Android uygulaması: `com.kokteyl.mackolik`, sürüm `8.5.4`.
- Retrofit arayüzü `com/perform/livescores/data/api/football/TokenApi`:
  `GET register/device/{applicationUuid}/{deviceUuid}`; metod adı `getApiToken`.
- `com/perform/livescores/data/service/SportFeedsApiToken` sınıfı mevcut.
- `com/perform/livescores/network/akamai/AkamaiService`,
  `AssetsAkamaiKeyProvider` ve `provideAkamaiInterceptor` referansları mevcut.
- APK assets altında `akamai_key.txt` var; içeriği hassas olduğundan **rapora veya repoya çıkarılmadı**.
- APK'nin DEX dize tablosunda `https://api.mackolikfeeds.com`,
  `https://auth-api.mackolikfeeds.com`, `http://origin-web.mackolikfeeds.io` var.
  Bu hostların her birine hangi Retrofit arayüzünün bağlı olduğu kesin eşleştirilmedi.
- `X-Authorization` dizesi SportFeedsRetrofitAdapter kodunda görünüyor.
  Bunun Maçkolik futbol API'si için gerekli başlık olduğunu henüz doğrulamadık.

## Açık teknik sorular

1. 403, Akamai/CDN erişim politikası mı, uygulama cihaz oturumu eksikliği mi, yoksa yanlış host/yol eşlemesi mi?
2. Android uygulamasının resmî/normal oturum edinme sürecinde `TokenApi` hangi host ve header düzeniyle çağrılıyor?
3. `/api/matches/` ve `/soccer/api/search/` hangi Retrofit base URL örneğini kullanıyor?
4. Meşru erişim elde edildiğinde isabetli şut yerine **toplam şut** için hangi JSON alanı kullanılmalı?

## Uygulama kuralları

- Sahte JSON, uydurma başarı veya varsayımsal token kaydetme.
- APK'nin paketlenmiş anahtarını, HMAC materyalini, kullanıcı oturumunu ve cihaz tokenını loglarda / repoda yayımlama.
- Yetkisiz API erişim kontrolünü kırma, kullanıcı/cihaz kimliği taklidi veya WAF atlatma denemesi yapma.
- Yetkili erişim gerekiyorsa sağlayıcıdan resmi erişim ya da kullanıcının kendi izinli oturum akışını kullan.
- 403 aynı kalıyorsa sınırsız istek/yeniden deneme döngüsü yerine düşük hacimli tanılama ve rapor.
- GitHub testleri UTC :07 :22 :37 :52'de planlanır; GitHub iş kuyruğu gecikmeleri olabilir.
- Dağıtım klasörü `https://duvar.applerehberi.com/mackolik-api-lab/` sadece izolasyonlu test dosyalarını barındırır.

## Canlı loglar ve sonuçlar

- [GitHub test işleri](https://github.com/utkubrs/mackolik-api-lab/actions)
- [Son kontrol](../reports/SON_DURUM.md)
- [JSON durum](../data/latest.json)
- [Özel klasöre FTP dağıtım logları](https://github.com/utkubrs/duvar-arena/actions)


## Yeni statik doğrulama — Retrofit base URL'leri (19 Ekim 2026)

`base.apk` içindeki **classes7.dex**, `Lcom/perform/livescores/di/ApiModule;` sınıfının gerçek yöntem gövdelerinde şu sabit adresleri Retrofit.Builder.baseUrl çağrısından önce kullanıyor:

| DEX metodu | Doğrudan görülen sabit base URL |
|---|---|
| `provideAtmosphereRetrofit` | `https://api.mackolikfeeds.com` |
| `provideContactUsRetrofit` | `https://api.mackolikfeeds.com` |
| `provideFavOddRetrofit` | `https://api.mackolikfeeds.com` |
| `provideOnboardRetrofit` | `https://api.mackolikfeeds.com` |
| `provideAdRetrofit` | `https://ad.mackolikfeeds.com/` |
| `provideLanguageRetrofit` | `https://www.mackolik.com/static-files/` |
| `provideKokteylRetrofit` | `http://sportsapi.cdn.md` |
| `providePerformFeedsConfig` | `https://api.mackolikfeeds.com` |

`classes4.dex` içindeki `ThirdPartyModule.provideFootballMatchesApi`, `provideFootballSearchPlayerApi`, `provideFootballPlayerApi` ve `provideTokenApi` metodlarında `Retrofit.create` çağrısı doğrulandı. Bu yöntemlerin aldığı Retrofit örneklerine hangi `@Named` sağlayıcının bağlandığı burada henüz kesinleştirilmedi. **Özellikle ana futbol arayüzünün yukarıdaki hangi base URL'yi kullandığı ayrıca doğrulanmadan farklı hostlarda deneme bombardımanı yapılmamalı.**

### API dışındaki alternatif: herkesin görebildiği futbolcu profili

- Maçkolik web profilinde Harry Winks: `https://www.mackolik.com/futbolcu/h-winks/5qfa3h4gut5jlnfkexq5m1djp` (arama yoluyla gerçek sayfa doğrulandı).
- Genel lig istatistik sayfalarında `Maç Başı Toplam Şut` başlığı bulunuyor.
- **Bu web verileri oyuncunun son 5 maçının şut sayılarını göstermiyor.** Bu nedenle son beş maç dizisi üretmeyiz.
- `.github/workflows/public_site.yml` erişilebilirliği günlük / manuel, bağımsız şekilde kontrol eder; sonuç `data/public_site_latest.json` olarak yayımlanır.



## Canlı kamuya açık sayfa testi (19 Ekim 2026, 16:32 UTC)

- `https://www.mackolik.com/futbolcu/h-winks/5qfa3h4gut5jlnfkexq5m1djp` web araması ile gerçek profil olarak doğrulandı.
- GitHub Actions'in standart, yönlendirmesiz olmayan urllib HTTPS sayfa isteği **HTTP 403**, sıfır yanıt gövdesi döndürdü.
- `data/public_site_latest.json` içinde bu HTTP 403 sonuç kaydedildi. Bu, sitenin insanlar tarafından hiç açılamadığı anlamına gelmez; otomasyon ortamının isteği reddedildiğini gösterir.
- `scripts/public_site.py` son beş maç şut verisini **kasıtlı olarak doğrulanmadı** gösterir; sayfa başlığının bulunmasını veri başarısı saymaz.
- Bu aşamada otomatik erişim denemelerini yoğunlaştırmak yerine resmi veri erişim yetkisi veya otomasyon için açık kaynak/izinli çözüm gerekir.


## Bağımlılık enjeksiyonu (DEX yöntem imzaları)

`classes4.dex` içinde şu dört sağlayıcının her biri tam olarak bir `retrofit2.Retrofit` parametresi alıyor:

- `ThirdPartyModule.provideFootballMatchesApi(Retrofit) -> FootballMatchesApi`
- `ThirdPartyModule.provideFootballPlayerApi(Retrofit) -> FootballPlayerApi`
- `ThirdPartyModule.provideFootballSearchPlayerApi(Retrofit) -> FootballSearchPlayerApi`
- `ThirdPartyModule.provideTokenApi(Retrofit) -> TokenApi`

`classes20.dex` içinde otomatik üretilmiş `ThirdPartyModule_ProvideTokenApi...Factory` sınıfının `retrofitProvider` bağımlılığı da görülüyor. Bu, token servisinin bir Retrofit örneğine bağlı olduğunu **kesinleştirir**, fakat onun URL'sini/kimlik doğrulamasını **kesinleştirmez**. Dagger component sağlayıcı eşlemesi veya uygulamanın izinli ağ isteği kayıtları olmadan host tahmini yapmak hatalıdır.
