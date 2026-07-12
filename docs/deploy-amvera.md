# Деплой на Amvera Cloud

Проект: **run-tarot-robobot**  
Git remote Amvera: `https://git.amvera.ru/ntshvrabota/run-tarot-robobot`

## 1. Переменные окружения в Amvera

В панели Amvera → проект → **Переменные окружения** добавь:

| Переменная | Обязательно | Пример |
|------------|-------------|--------|
| `BOT_TOKEN` | да | от @BotFather |
| `KIE_API_KEY` | да | ключ Kie.ai |
| `DASHBOARD_PASSWORD` | да | пароль админки |
| `ADMIN_IDS` | да | твой Telegram ID |
| `REFERRAL_BOT_USERNAME` | да | `tarot_robobot` |
| `DASHBOARD_SECRET` | да | случайная строка |

Остальные переменные уже заданы в `Dockerfile` (SQLite в `/data`, порт 80).

Шаблон: [amvera.env.example](../amvera.env.example)

## 2. Push в Amvera

```bash
cd /Users/admin/Desktop/bot

# один раз
git remote add amvera https://git.amvera.ru/ntshvrabota/run-tarot-robobot

# каждое обновление
git add .
git commit -m "описание изменений"
git push amvera main:master
```

Логин/пароль — учётная запись Amvera.

> Amvera использует ветку `master`. Локальная ветка `main` пушится как `main:master`.

## 3. Что происходит на сервере

- Сборка по `Dockerfile`
- Данные SQLite хранятся в **постоянном хранилище** `/data`
- Бот работает в фоне (polling)
- Дэшборд доступен по URL проекта Amvera (порт 80)

## 4. Проверка

1. Статус в Amvera: **Успешно развернуто**
2. Логи приложения — без ошибок `BOT_TOKEN`, `ModuleNotFoundError`
3. Напиши боту `/start` в Telegram
4. Открой URL проекта в Amvera → войди в дэшборд

## 5. Обновление

```bash
git push amvera main:master
```

База в `/data` сохраняется между деплоями.

## Ограничения Amvera

- `docker-compose` не поддерживается — один контейнер
- PostgreSQL/Redis не используются — SQLite + память (как локальный режим)
- FSM-состояния сбрасываются при перезапуске контейнера (Redis недоступен)

## Если не деплоится

- Проверь логи **сборки** и **приложения** в Amvera
- Убедись, что `amvera.yml` и `Dockerfile` в корне репозитория
- Напиши в support@amvera.ru с именем проекта `run-tarot-robobot`
