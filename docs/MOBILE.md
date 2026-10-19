# Telefondan testleri izleme

1. [Actions ekranını](https://github.com/utkubrs/mackolik-api-lab/actions) aç.
2. "Maçkolik API Bağlantı Testi" iş akışını seç; manuel başlatmak istersen `Run workflow` ile `smoke` seç.
3. Her 10 dakikada bir planlanan otomatik test sonuçlarını aynı sayfada gör. 403 sürerse denemelerin 60 dakikalık geri çekilme aralığına girdiğini unutma; GitHub'un gecikmeleri nedeniyle tam dakikasında başlamayabilir.
4. Test çalışmasını aç → `Summary` kısmında HTTP durumunu ve JSON olup olmadığını gör.
5. `Artifacts` arşivinde tam tanılama logu ve redakte edilmiş JSON örneği bulunur.
6. Otomatik yayımlanan [son durum raporunu](../reports/SON_DURUM.md) ve [en güncel JSON'u](../data/latest.json) incele; bu dosyalar ancak ilk başarılı Actions işi sonrasında oluşur.

**Dikkat:** GitHub Actions job `queued` görünüyorsa henüz isteğin atıldığı kanıtlanmış değildir. 401/403/429 yanıtları aşılamaz. FTP aktarımı, ayrı sunucu kimlik bilgileri ve deploy ayarı bulunmadıkça yapılmaz.
