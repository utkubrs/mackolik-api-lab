# Maçkolik API Lab — Son kontrol

GitHub Actions her 10 dakikada bir kontrolü *planlar*; 403 tekrarı varsa 60 dakikalık istek bekleme süresi uygulanır; GitHub yoğunluğunda gecikebilir.
**UTC:** 2026-10-20T05:01:57.778733+00:00  |  **GitHub logları:** [Çalışmayı aç](https://github.com/utkubrs/mackolik-api-lab/actions/runs/39372695320)

| Kontrol | HTTP | JSON | Sonuç | Süre |
|---|---:|---|---|---:|
| matches | 403 | Hayır | http_or_schema_error | 441 ms |
| search | 403 | Hayır | http_or_schema_error | 19 ms |
| remote_matches | 403 | Hayır | http_or_schema_error | 195 ms |
| remote_search | 403 | Hayır | http_or_schema_error | 112 ms |

Gerçek JSON örnekleri için ilgili çalışmanın **Artifacts** bölümündeki dosyayı aç.
Bu tablo gerçek API erişimi doğrulanana kadar 'veri geliyor' iddiası değildir.
