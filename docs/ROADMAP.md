# Geliştirme yol haritası

- [x] APK'den statik endpoint izlerini belgele.
- [x] Python GET/JSON teşhis aracı ve PHP test sayfası ekle.
- [x] GitHub Actions üzerinden her 15 dakikada planlanan test ve log arşivleme düzeni.
- [x] Son kontrol ve sınırlı geçmişi GitHub deposunda yayımlayacak otomasyon.
- [ ] GitHub-hosted runner canlı testi tamamlasın; HTTP/JSON sonuçlarını doğrula.
- [ ] Gerçek istek URL/host/parametreleri ile saha testi.
- [ ] Oyuncu ID ve maç ID eşleştir; son 5 maç toplam şut istatistiği.
- [ ] Muhtemel ilk 11 ve resmi ilk 11 karşılaştırması.
- [ ] PHP cron + kullanıcıya yönelik görünüm; erişim ve lisans koşullarını değerlendir.
- [ ] İstenirse FTP üzerinden yayımlama; doğru sunucu ve GitHub Secrets olmadan gerçekleşmez.

Agent, gerçek örnek görmeden JSON alanı veya veri sayısı uydurmamalı; her değişiklik test ve açıklamalı commit gerektirir.
