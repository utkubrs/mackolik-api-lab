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
