#!/bin/bash
# Остановить локальный бот и дэшборд (чтобы не конфликтовали с сервером)
set -e
pkill -f "python3 -m src.main" 2>/dev/null && echo "Stopped local bot" || echo "Local bot was not running"
pkill -f "python3 -m src.dashboard" 2>/dev/null && echo "Stopped local dashboard" || echo "Local dashboard was not running"
