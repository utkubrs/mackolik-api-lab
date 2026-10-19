# Maçkolik 8.5.4 — APK kaynaklı API yol haritası

**Önemli:** Bu yollar statik APK/Retrofit incelemesinden çıkarılmıştır. `https://api.mackolikfeeds.com` hostu uygulamada mevcut olsa da yolların her biri bu host altında canlı yanıt döndürüyor diye doğrulanmamıştır.

| Veri | GET yolu |
|---|---|
| Günlük maçlar | `/api/matches/` |
| Arama | `/soccer/api/search/` |
| Oyuncu | `/api/player/` |
| Oyuncunun maçları | `/api/player/matches` |
| Maç detayı | `/api/match/` |
| Maç-oyuncu istatistiği | `/statistics-service/match/{match_mid}/player/{player_mid}/stats` |
| Takım | `/api/team/` |
| Aktif kadro | `/team-service/soccer/team/{selectedTeamMid}/active-squad` |
| Oyuncu sezon istatistikleri | `/person-service/soccer/person/{playerId}/stats` |

APK model alanları: `possible_lineup`, `lineup`, `shotMap`, `statTopPlayers`, `statList`, `eventList`, `match`. Resmi kadro ve muhtemel 11'in gerçek JSON semantiği henüz kanıtlanmadı.

Hedef: oyuncu son beş maçı → her maç için oyuncu toplam şutu → `1-0-2-5-1`. **İsabetli şut ayrı tutulmalı; bulunamayan değer `null`, sıfır değil.**

HTTP 200 + JSON şema ilk olumlu sinyaldir; 401/403 kimlik doğrulama/erişim kısıtı, 404 yanlış yol/host olabilir. Engeller aşılmaya çalışılmaz.

## Arama yollarının ayrımı (DEX ile doğrulandı)

- `FootballSearchPlayerApi.getPlayerSearch` → **GET `/soccer/api/search/`** (params: `language`, `country`, `search`, `searchtypes`).
- `FootballExploreApi.getExploreSearch` → **GET `/api/search/`** (params: `language`, `country`, `search`).
- İki yol farklı Retrofit arayüzleridir. Aynı endpoint kabul edilmemeli. `/soccer/api/search/` çağrımızda `searchtypes` henüz belirlenmediğinden bile aynı istemin tüm zorunlu/opsiyonel parametrelerine sahip olduğunu varsayamayız.
