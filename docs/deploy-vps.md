# Деплой на VPS (Timeweb / свой сервер)

## Сервер

- **IP:** `5.129.213.49`
- **Путь проекта:** `/opt/tarot-robobot`
- **Git:** https://github.com/ntshv-maker/tarot-robobot

## Что запущено

```bash
docker compose -f docker-compose.prod.yml ps
```

| Сервис | Порт |
|--------|------|
| bot | Telegram polling |
| dashboard | http://5.129.213.49:8080 |
| postgres | внутренний |
| redis | внутренний |

## Автодеплой

Каждые **5 минут** cron на сервере проверяет GitHub и перезапускает контейнеры при новых коммитах в `main`.

Лог: `/var/log/tarot-robobot-deploy.log`

Ручной деплой на сервере:

```bash
cd /opt/tarot-robobot
./scripts/server/deploy.sh
```

## Первичная настройка (с Mac)

```bash
VPS_HOST=5.129.213.49 VPS_USER=root VPS_PASSWORD='...' ./scripts/server/setup-vps.sh
```

## Обновление секретов

```bash
POSTGRES_PASSWORD=$(ssh root@5.129.213.49 'grep POSTGRES_PASSWORD /opt/tarot-robobot/.env')
POSTGRES_PASSWORD=$POSTGRES_PASSWORD python3 scripts/server/build-server-env.py > /tmp/server.env
scp /tmp/server.env root@5.129.213.49:/opt/tarot-robobot/.env
ssh root@5.129.213.49 'cd /opt/tarot-robobot && docker compose -f docker-compose.prod.yml up -d'
```

## Безопасность

- Смени root-пароль после настройки
- Настрой SSH-ключ вместо пароля
- Не коммить `.env` в git
