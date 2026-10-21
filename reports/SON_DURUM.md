# Maçkolik API Lab — Son kontrol

GitHub Actions her 10 dakikada bir kontrolü *planlar*; 403 tekrarı varsa 60 dakikalık istek bekleme süresi uygulanır; GitHub yoğunluğunda gecikebilir.
**UTC:** 2026-10-21T00:11:26.767856+00:00  |  **GitHub logları:** [Çalışmayı aç](https://github.com/utkubrs/mackolik-api-lab/actions/runs/39519780681)

| Kontrol | HTTP | JSON | Sonuç | Süre |
|---|---:|---|---|---:|
| matches | 403 | Hayır | http_or_schema_error | 611 ms |
| search | 403 | Hayır | http_or_schema_error | 51 ms |
| remote_matches | 403 | Hayır | http_or_schema_error | 212 ms |
| remote_search | 403 | Hayır | http_or_schema_error | 115 ms |

Gerçek JSON örnekleri için ilgili çalışmanın **Artifacts** bölümündeki dosyayı aç.
Bu tablo gerçek API erişimi doğrulanana kadar 'veri geliyor' iddiası değildir.
