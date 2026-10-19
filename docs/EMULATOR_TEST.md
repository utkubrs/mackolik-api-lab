# Maçkolik 8.5.4 — gerçek Android emülatörü

## Gerçek kanıt (19 Ekim 2026)

`Android Emülatör — APK Uyumluluğu` çalışması başarılı:
https://github.com/utkubrs/mackolik-api-lab/actions/runs/39288863251

- Ubuntu GitHub runner üzerinde Android 15 (API 35), `google_apis` + `x86_64` sistem imajı açıldı.
- `adb shell getprop ro.product.cpu.abilist` çıktısında `x86_64` ve `arm64-v8a` bulunuyor.
- Kullanıcıdan gelen ZIP'deki dört APK incelendi; yalnız `split_config.arm64_v8a.apk` yerel ARM64 kitaplıkları içeriyor.
- Bu, emülatörün **ARM64 desteklediğini bildirdiği** anlamına gelir; orijinal Maçkolik APK kurulumu henüz çalıştırılmadı. Erişim tokenı üretildiği veya API 403 sorununun çözüldüğü anlamına gelmez.

## Özel APK kaynağıyla normal uygulama testi

`.github/workflows/emulator_app.yml` sadece manuel `workflow_dispatch` ile başlatılır.

İşi çalıştırabilmek için GitHub Actions Secrets içinde şu iki veri olmalıdır:

- `MACKOLIK_APK_URL`: kullanıcının kontrol ettiği, orijinal ZIP arşivine ait süreli/geçici HTTPS indirme adresi.
- `MACKOLIK_APK_SHA256`: indirilecek ZIP dosyasının SHA-256 özeti.

Betik `scripts/emulator_app_smoke.sh`, bu dosyayı özel runner alanına indirip SHA-256 doğrular, `adb install-multiple` ile dört orijinal APK'yi kurar, **gerçek uygulamayı** Android package manager aracılığıyla açar ve `out/launch.png` görüntüsü + kurulum durumunu saklar. ZIP ya da gizli URL loglara/depo dosyalarına yazılmaz.

Bu yöntem, Maçkolik uygulamasının normal kullanıcı akışını doğrulamak içindir. Güvenlik kontrolü aşımı, cihaz kimliği taklidi, uygulamanın gizli anahtarını kopyalama, paket sahteciliği veya çalınmış token kullanımı yoktur. Yanıt şifreliyse tokenları yakalama/ifşa etme yapılmaz.

### Mevcut engel

Sohbete yüklenmiş 106 MB ZIP, GitHub Actions runner tarafından otomatik erişilebilir bir depolama URL'si değildir. GitHub reposu public olduğu için binary'yi buraya koymadık. FTP dağıtım yetkisi/hosting şifresi de bu oturumda doğrudan erişilebilir değil; bu yüzden Actions Secrets henüz ayarlanmadı ve `emulator_app.yml` gerçek uygulama açılışı denemesine başlamadı.

## 10 dakikalık izleme

`.github/workflows/probe.yml` schedule: `:07, :17, :27, :37, :47, :57` (UTC).
Önceki bütün kamuya açık API kontrolleri `403/Access Denied` olduğu sürece `scripts/retry_guard.py` yeni istekleri 60 dakika aralıkla sınırlar. GitHub schedule gecikebilir.

Bu ayrıntılar, "10 dakikada bir 403'ü zorlamadan izle; yeni erişim koşulu kanıtı varsa meşru uygulama testini bir kez çalıştır" yaklaşımını uygulanabilir kılar.

## Bu oturumda yüklenen APK paketinin bütünlük özeti

`Mackolik-8.5.4-split-apks.zip` SHA-256:

```
9d49ecb65c07bbf840d348c06e17e482a3865350b388432d6452713b4e400d9d
```

Bu özet yüklenen orijinal arşivden hesaplandı; ZIP dosyasının kendisi kamuya açık GitHub deposuna konmadı. Hazırlanan emülatör eylemi, bir HTTPS kaynak tanımlandığında aynı SHA ile arşivin değişmemiş olduğunu doğrulayabilir.
