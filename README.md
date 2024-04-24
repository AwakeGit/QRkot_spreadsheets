# QRkot_spreadseets

Фонд собирает пожертвования на различные целевые проекты, связанные с
поддержкой кошачьей популяции, включая медицинское обслуживание нуждающихся
хвостатых, обустройство кошачьей колонии в подвале и предоставление корма
оставшимся без попечения кошкам.

## Ключевые возможности сервиса

- Создание благотворительных проектов
- Создание пожертвований для этих проектов
- Автоматическая система распределения пожертвований между проектами
- Генерация отчётов в гугл-таблицах по проектам

## Использованные технологии

- Python 3.9
- FastAPI
- Alembic
- Uvicorn
- SQLAlchemy
- Google API

## Как установить проект

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:AwakeGit/QRkot_spreadsheets.git
```

```bash
cd QRkot_spreadsheets/
```

Создать и активировать виртуальное окружение:

```bash
python3 -m venv venv

source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```bash
python3 -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

Создать файл .env:

```bash
touch .env
```

И наполнить его переменными по примеру из файла `.env.example`

Инициализировать проект:

```bash
alembic init --template async alembic     
```

Создать первую миграцию:

```bash
alembic revision --autogenerate -m "First migration"          
```

Применить миграции:

```bash
alembic upgrade head
```

Запустить проект:

```bash
uvicorn app.main:app
```

Сервис QRKot будет доступен по
адресу:  [http://127.0.0.1:8000](http://127.0.0.1:8000/docs)

