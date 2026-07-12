from __future__ import annotations

import uvicorn

from src.config import get_settings
from src.dashboard.app import create_app


def main() -> None:
    settings = get_settings()
    if not settings.dashboard_password:
        raise SystemExit(
            "Задай DASHBOARD_PASSWORD в .env перед запуском дэшборда.\n"
            "Пример: DASHBOARD_PASSWORD=your_secure_password"
        )
    app = create_app(settings)
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port, log_level="info")


if __name__ == "__main__":
    main()
