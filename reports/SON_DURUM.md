# Maçkolik API Lab — Son kontrol

GitHub Actions her 10 dakikada bir kontrolü *planlar*; 403 tekrarı varsa 60 dakikalık istek bekleme süresi uygulanır; GitHub yoğunluğunda gecikebilir.
**UTC:** 2026-10-23T07:32:21.797630+00:00  |  **GitHub logları:** [Çalışmayı aç](https://github.com/utkubrs/mackolik-api-lab/actions/runs/39918415910)

| Kontrol | HTTP | JSON | Sonuç | Süre |
|---|---:|---|---|---:|
| matches | 403 | Hayır | http_or_schema_error | 564 ms |
| search | 403 | Hayır | http_or_schema_error | 29 ms |
| remote_matches | 403 | Hayır | http_or_schema_error | 209 ms |
| remote_search | 403 | Hayır | http_or_schema_error | 105 ms |

Gerçek JSON örnekleri için ilgili çalışmanın **Artifacts** bölümündeki dosyayı aç.
Bu tablo gerçek API erişimi doğrulanana kadar 'veri geliyor' iddiası değildir.
