mkdir -p .data/postgis

docker compose --env-file .env -f docker-compose.dev.yml up --force-recreate