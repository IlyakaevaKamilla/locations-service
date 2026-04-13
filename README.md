# Location Service

Сервис хранит каталог локаций в отдельной БД и отдаёт API для поиска, фильтрации и избранного.

## API

- `GET /api/locations` - список локаций с фильтрами `search`, `region`, `city`, `country`, `activity_id`, `style`, `level`, `limit`, `offset`;
- `GET /api/locations/{location_id}` - карточка локации;
- `GET /api/locations/filters` - доступные значения фильтров;
- `GET /api/locations/favorites` - избранные локации текущего пользователя;
- `POST /api/locations/{location_id}/favorite` - добавить в избранное;
- `DELETE /api/locations/{location_id}/favorite` - удалить из избранного.

Локации создаются, обновляются и удаляются через отдельную админку. Этот сервис только читает каталог и хранит пользовательские избранные.

## Конфигурация

Переменные окружения:

- `DB_LOCATION_SERVICE_HOST`
- `DB_LOCATION_SERVICE_PORT`
- `DB_LOCATION_SERVICE_NAME`
- `DB_LOCATION_SERVICE_USER`
- `DB_LOCATION_SERVICE_PASS`

Для тестовой БД:

- `TEST_DB_LOCATION_SERVICE_NAME`

Health-check: `GET /api/locations/health`
