include .env
export

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn

run-dev:
	@if [ -d "$(VENV)" ]; then \
		$(UVICORN) main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "Виртуальное окружение не найдено. Создайте его с помощью make venv"; \
		exit 1; \
	fi

venv: # 
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

# Установка зависимостей
install: 
	$(PIP) install -r requirements.txt

# Создание новой миграции
makemigrations:
	alembic revision --autogenerate -m "$(m)"

# Применение всех миграций
migrate:
	alembic upgrade head

# Откат на одну миграцию
downgrade:
	alembic downgrade -1

# Откат до конкретной ревизии
downgrade-to:
	alembic downgrade $(rev)

# Применение до конкретной версии
upgrade-to:
	alembic upgrade $(rev)

# Показать историю миграций
history:
	alembic history --verbose

# Текущая версия миграций
current:
	alembic current

# Создать пустую миграцию (без autogenerate)
makemigrations-empty:
	alembic revision -m "$(m)"
