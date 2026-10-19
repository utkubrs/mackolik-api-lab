# Agent çalışma kuralları (Maçkolik API Lab)

Bu depo keşif/teşhis amaçlıdır. Herkese açık olabileceğinden ham özel verileri saklama. Kullanıcı çoğunlukla **Android telefon** üzerinden çalışır; her değişiklik GitHub Actions ve Summary/Artifacts üzerinden izlenebilir olmalı. Üretim sistemi PHP 8+ cron ile uyumlu geliştirilecektir.

## Hedefler

1. APK 8.5.4 içindeki Retrofit yollarını, gerçek istekle **kanıtlandığı ölçüde** doğrula. Tahmini URL veya sahte JSON gösterme.
2. Oyuncunun oynadığı son beş maçı belirle; her maç için **toplam şut** (isabetli şut değil) sayısını `son maç → eski maç` şeklinde çıkar. `0` ve `null` ayrımını koru.
3. `possible_lineup` (muhtemel kadro) ve resmî ilk 11 kaynaklarını sahici JSON üzerinden doğrula, yedekleri ayıkla. Bilinmeyen isim/ID eşleştirmelerini kayıt altında göster.
4. Sonuçları telefondan GitHub Actions Summary ve artifact JSON + `web/index.html` ekranında incelenebilir kıl.
5. JSON şemaları doğrulandıktan sonra PHP 8+ (cURL) uygulama/cron katmanını ekle.

## Kanıt politikası

- "APK'de yol mevcut", "HTTP 200 gördük", "JSON alanını doğruladık" ve "istatistik semantiğini doğruladık" birbirinden farklı durumlar. Her bulguyu hangi kanıta dayandığıyla belirt.
- HTTP 403/401/429 => takip edilen engel; kimlik doğrulama ve kota mekanizmasını taklit etme/aşma.
- Servis şartları ve veri lisansına uy; API erişimi uygun değilse izinli/ücretsiz alternatifler sun.
- API kimliği, cookie, auth header, device fingerprint, kişi telefonu/e-postası ve tüm üçüncü taraf gövdesini GitHub loglarına koyma. Artefaktlarda hassas alanlar redakte edilmeli.
- Ağ isteklerini yüksek sıklıkla veya sunucuyu zorlayacak şekilde çalıştırma; 10 dakikalık kontrol ve 403 sonrası 60 dakikalık soğuma kuralına uy; manual testi suistimal etme.
- Özel APK ve telif hakkına tabi uygulama dosyaları repoya yüklenmeyecek. Üçüncü taraf kod/decompiled kaynak depolanmayacak.
- Betiklerin yalnızca sabit `https://api.mackolikfeeds.com` sunucusu ve allowlist GET yollarını kullanmasını koru; kullanıcıdan keyfi URL alma.

## Her kod değişikliğinde

- `python3 -m unittest discover -s tests -v` çalıştır.
- GitHub Actions summary ve rapor JSON'unu geriye uyumlu tut.
- Kod ekliyorsan, uydurma saha verisiyle değil `tests/fixtures` altında açıkça **temsili fixture** olarak işaretlenmiş verilerle test et. Gerçek JSON elde edilirse izin/hassas veri incelemesi yapmadan commit etme.
- README ve docs/API_MAP.md güncelle; doğrulanmamış iddiaları kesinmiş gibi yazma.
- Mümkünse GitHub Issue'da HTTP status, field-path, tarih, yöntem ve kesinleştirilen iddiayı kaynakla kaydet.

## Devreye alma sırası

1. `smoke` job sonucuna bak; status ve response key'leri doğrula.
2. Sahici oyuncu ID ve maç ID eşleştirmelerini belirle.
3. Son 5 şut ve 11 verileri için yeni unit test/iş akışı yaz; sadece doğrulanmış alan isimlerine dayan.
4. PHP cron adaptorü ve mobil gösterimi bağla.
- GitHub Actions kontrol iş akışı UTC :07, :17, :27, :37, :47 ve :57 dakikalarına planlandı; 403 için 60 dakikalık soğuma uygulanır. 10 dakika kontrol **10 dakika boyunca tekrar 403 istemek demek değildir**. Zamanlama kesin değildir.
- Split APK bütünlük denetimleri ve açılış kanıtları için `scripts/apk_bundle_validator.py`, `tests/test_apk_bundle_validator.py` ve `docs/EMULATOR_TEST.md` dosyalarını esas al.


## Çalışan alternatif: ESPN (19 Ekim 2026)

- [docs/ESPN_SUCCESS.md](docs/ESPN_SUCCESS.md) içindeki kanıtlar doğrulandı. Maçkolik 403'ü çözmeden ESPN verisi kullanılabiliyor.
- Kaynak `rosters[].roster[].stats[]`, anahtar `name=totalShots`, değer `value` (sayısal) — `shotsOnTarget` ayrı.
- `appearances>=1` olmayan oyuncunun maçını son beşe dahil etme. `totalShots` eksikse NULL, sıfır değil.
- `php/espn_last5.php` 15 dakika önbellekli mobil paneli ve JSON çıktısını FTP'de sunuyor.
- Son 5 maç hesapları **lig bazlıdır**; farklı turnuvalar için kupa eşleştirmesi ayrı gerekir.
- ESPN site uç noktaları üçüncü taraf, resmî geliştirici sözleşmesi değildir; yoğun otomatik sorgular/erişim engeli aşma yapılmaz.
