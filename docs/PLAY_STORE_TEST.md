# Android 15 Google Play normal kurulum testi

**Tarih:** 19 Ekim 2026, 17:21 UTC.

[GitHub Actions kanıtı](https://github.com/utkubrs/mackolik-api-lab/actions/runs/39293115895)  
[Ekran görüntüsü ve JSON artefaktı](https://github.com/utkubrs/mackolik-api-lab/actions/runs/39293115895/artifacts/12206497080)

## Gerçek sonuç

- Android 15, Google Play içeren resmî `google_apis_playstore` emülatör imajında başarılı açıldı.
- `com.android.vending` Android paket yöneticisinde bulundu.
- Normal `market://details?id=com.kokteyl.mackolik` intent'i Android tarafından başlatıldı.
- Görüntüde **Google Play “Sign in”** ekranı ve mavi “Sign in” düğmesi bulundu. Giriş yapılmadı.
- `adb shell pm path com.kokteyl.mackolik` sonucu boş: **Maçkolik kurulu değil**.
- `out/play_store_evidence.json` sonuçları: `google_play_package_available=true`, `mackolik_installed=false`, `screenshot_present=true`.
- Google Play'in açılması, uygulama kurulumu ya da futbol API'si erişimi anlamına gelmez.

## Teknik çıkarım

Google Play üzerinden uygulama yükleme senaryosu bu headless ve giriş yapılmamış emülatörde tamamlanamıyor. Google hesap kimliğini/logini otomatikleştirme; kaydedilmiş bir oturum yok. En temiz alternatif, kullanıcının **kendi orijinal imzalı dört split APK dosyasını** `emulator_app.yml` iş akışına özel HTTPS kaynak üzerinden sağlamaktır.

İlk gerçek API testleri hâlâ `HTTP 403 Access Denied`. Uygulamanın gerçek başlangıç oturumu başarıyla test edilmeden ham API isteğini uygulama oturumu gibi göstermeyin.

## Saklanan dosyalar

- `play_store_evidence.json`: HTTP olmayan cihaz ve Google Play durumu
- `play_store.png`: oturum açma ekranının gerçek emülatör görüntüsü
- `play_store_open.txt`: intent başlatma çıktısı
- `focus.txt`: Windows odak tanılama çıktısı
