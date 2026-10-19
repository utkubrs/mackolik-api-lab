# Maçkolik bağımsız çözüm: ESPN maç bazında oyuncu toplam şutları

## Doğrulanmış durum — 19 Ekim 2026

Maçkolik özel API yolları GitHub Actions ve Türkiye PHP sunucusunda HTTP 403 döndürdü. Emülatör şart değil: **ESPN'nin site futbol JSON'u**, aynı GitHub runner üzerinde HTTP 200 ve gerçek oyuncu verileri sağladı.

### Doğrulanmış URL yapısı

- Takımın lig maçları: `https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams/{team_id}/schedule`
- Tek maçın özeti: `https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={event_id}`
- Takım kadrosu ve oyuncu kimliği: `https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams/{team_id}/roster`

**Bunlar ESPN'nin yayımladığı, resmî geliştirme sözleşmesi bulunmayan site uç noktalarıdır.** Başarılı test bunların kullanım hakkını, SLA'sını, sürekli çalışacağını veya bütün ligleri kapsadığını garanti etmez. Yoğun sorgu yerine önbellek ve düşük frekans kullan.

### Gerçek JSON alanları

- `rosters[].roster[].athlete.id` — oyuncu kimliği
- `rosters[].roster[].starter` — ilk 11
- `rosters[].formation` — diziliş
- `rosters[].roster[].stats[]` içinde `name === "appearances"` ve `value >= 1` — maçta oynamış
- `rosters[].roster[].stats[]` içinde `name === "totalShots"` ve sayısal `value` — **toplam şut**
- `rosters[].roster[].stats[]` içinde `name === "shotsOnTarget"` — **ayrı** isabetli şut

Eksik istatistiği kesinlikle 0'a dönüştürme. Son 5 **oynanan lig maçını** takvimden yeni → eski sırala, kadroda bulunmayan veya oynamamış oyuncuyu atla. Kupa/diğer turnuvalar ayrıca eklenmelidir.

### İki gerçek 5 maçlık örnek

| Oyuncu | Lig | Takım | ESPN ID | Son 5 toplam şut |
|---|---|---|---|---|
| Rayan | eng.1 | Bournemouth (349) | 357719 | **7-2-0-5-1** |
| Harry Winks | ita.1 | Cagliari (2925) | 202332 | **1-1-0-1-0** |

- [Rayan canlı veri raporu](../data/espn_last5_latest.json)
- [Harry Winks canlı veri raporu](../data/harry_winks_latest.json)
- [Gerçek oyuncu bazında alanların kanıtı](../data/espn_player_details.json)
- [Canlı PHP sayfası](https://duvar.applerehberi.com/mackolik-api-lab/espn_last5.php)
- [PHP JSON kaynağı](https://duvar.applerehberi.com/mackolik-api-lab/espn_last5.php?format=json)
- [Harry Winks mobil sayfa](https://duvar.applerehberi.com/mackolik-api-lab/espn_last5.php?league=ita.1&team_id=2925&player_id=202332)

### Proje kodları

- `scripts/espn_last5.py`: gerçek son beş maç hesaplayıcısı
- `scripts/espn_find_winks.py`: Cagliari kadrosundan doğrulanan gerçek ESPN oyuncu ID'si
- `php/espn_last5.php`: tek başına çalışan PHP 8+ mobil panel + `?format=json`, 15 dakika önbellek
- `.github/workflows/espn_last5.yml`: mobil GitHub Actions'dan tekrar çalıştırılabilir test
- `utkubrs/duvar-arena/.github/workflows/mackolik-ftp-probe.yml`: ayrı FTP test klasörüne PHP dağıtımı; canlı Rayan 5/5 doğrulandı.

### Gelecek entegrasyon

1. ESPN oyuncu ve takım ID'lerini normalize eden eşleştirme tablosu.
2. Diğer ligleri kontrollü birer gerçek maçla doğrula.
3. Misli MBS1 şut bahis veri kaynağı ile ilk 11 eşleştirmesini **yalnız kendi veri erişim hakkıyla** kur.
4. Bahis oranı ve başarı kayıtlarını ayrı depola. ESPN kendi başına Misli oranlarını sunmaz.
5. Güncel kadronun resmî mi muhtemel mi olduğunu maç durumu ve kadro yayınıyla ayrıca doğrula.
