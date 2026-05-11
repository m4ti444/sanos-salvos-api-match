# Sanos y Salvos - API Match

API del motor de coincidencias entre reportes de mascotas perdidas y encontradas.

## Stack

- FastAPI
- SQLAlchemy async
- PostgreSQL
- RabbitMQ para eventos
- Docker

## Variables de entorno

Copia `.env.example` como `.env` y ajusta los valores.

## Ejecucion local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

## Docker

```bash
docker build -t sanos-salvos-api-match .
docker run --env-file .env -p 8003:8003 sanos-salvos-api-match
```

## Endpoints principales

- `GET /api/matches/`
- `GET /api/matches/{match_id}`
- `GET /api/matches/report/{report_id}`
- `PATCH /api/matches/{match_id}/status`
