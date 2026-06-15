# Location Service

Сервис хранит каталог локаций в отдельной БД и отдаёт API для поиска, фильтрации и избранного.

## API

- `GET /api/locations` - список активных локаций с фильтрами `search`, `region`, `city`, `country`, `activity_id`, `style`, `level`, `limit`, `offset`;
- `GET /api/locations/{location_id}` - карточка активной локации;
- `GET /api/locations/filters` - доступные значения фильтров;
- `GET /api/locations/favorites` - избранные локации текущего пользователя;
- `POST /api/locations/{location_id}/favorite` - добавить в избранное;
- `DELETE /api/locations/{location_id}/favorite` - удалить из избранного.

### Фильтры локаций

`region`, `city`, `country`, `style`, `level` и `activity_id` принимают одиночное значение, повторяющиеся query-параметры и CSV.

Примеры:

- `GET /api/locations?region=Краснодарский край`
- `GET /api/locations?region=Краснодарский край&region=Карачаево-Черкесия`
- `GET /api/locations?region=Краснодарский край,Карачаево-Черкесия&style=ski,freeride`
- `GET /api/locations?activity_id=1&activity_id=2`
- `GET /api/locations?activity_id=1,2`

Значения внутри одного поля объединяются через `OR`, разные поля - через `AND`. Например `region=Краснодарский край,Карачаево-Черкесия&style=ski,freeride` ищет локации в одном из указанных регионов и с одним из указанных стилей. `activity_id` в OpenAPI описан как массив integer, но также поддерживает CSV для удобства клиентов.

`search` применяется как общее ограничение ко всему результату. Публичный API всегда возвращает только активные локации и не принимает `is_active` как query-параметр.

`location_id` и `activity_id` должны помещаться в диапазон PostgreSQL `integer`: от `1` до `2147483647`. Значения выше этого диапазона возвращают `404 Not Found`, чтобы не передавать некорректный integer в БД.

### Активность локаций

По умолчанию сервисные методы чтения возвращают только локации с `is_active=true`:

- `LocationService.get_location(...)`;
- `LocationService.list_locations(...)`;
- `get_location_by_id(..., only_active=True)`.

Для админских сценариев, где нужны все локации, включая неактивные, используется явное снятие ограничения:

- `LocationService.get_location_for_admin(...)`;
- `LocationService.list_all_locations(...)`;
- `get_location_by_id(..., only_active=False)`.

В избранное можно добавлять только активные локации. Попытка добавить неактивную локацию возвращает `400`.

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
