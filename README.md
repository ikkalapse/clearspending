# clearspending

Полнотекстовый поиск госконтрактов через API Госзатрат.
Источник данных: "Проект КГИ "Госзатраты" (clearspending.ru).

Извлекает подходящие по переданным параметрам контракты и сохраняет в JSON-файлы на диск в указанный каталог. 

## Как использовать

```python
  # Инициализация объекта-поисковика
  # с указанием каталога, куда скачивать найденные файлы с контрактами,
  # и префикса для скачиваемых файлов.
  cs = ClearspendingSearch(downloads_dir='pushkin', file_prefix='data')
  # Параметры для поиска по контрактам (см. в документации по API Госзатрат)
  cs.search_params = {'productsearchlist': 'Пушкин'}
  # Постраничное скачивание всех подходящих контрактов. 
  # На одной странице 50 конт рактов по усолчанию.
  cs.download_all()
```
