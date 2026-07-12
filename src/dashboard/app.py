from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.config import Settings, get_settings
from src.constants import PRODUCT_LABELS
from src.db.models import PurchaseStatus
from src.db.repositories import ChatMessageRepository, PurchaseRepository, UserRepository
from src.db.session import async_session_factory
from src.services.payment_fulfillment import confirm_purchase, reject_purchase

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

STATUS_LABELS = {
    PurchaseStatus.PENDING: "Ожидает",
    PurchaseStatus.PAID: "Оплачен",
    PurchaseStatus.CANCELLED: "Отклонён",
}

STATUS_BADGE = {
    PurchaseStatus.PENDING: "badge-pending",
    PurchaseStatus.PAID: "badge-paid",
    PurchaseStatus.CANCELLED: "badge-cancelled",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Astorobot Admin", docs_url=None, redoc_url=None)
    app.add_middleware(SessionMiddleware, secret_key=settings.dashboard_secret, max_age=86400 * 7)
    app.state.settings = settings

    def _is_authed(request: Request) -> bool:
        return bool(request.session.get("authed"))

    def _auth_redirect(request: Request) -> RedirectResponse | None:
        if not _is_authed(request):
            return RedirectResponse("/login", status_code=303)
        return None

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        if _is_authed(request):
            return RedirectResponse("/purchases", status_code=303)
        error = request.query_params.get("error")
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": error, "settings": settings},
        )

    @app.post("/login")
    async def login_submit(request: Request, password: str = Form(...)):
        if not settings.dashboard_password:
            return RedirectResponse("/login?error=no_password", status_code=303)
        if password != settings.dashboard_password:
            return RedirectResponse("/login?error=invalid", status_code=303)
        request.session["authed"] = True
        return RedirectResponse("/purchases", status_code=303)

    @app.get("/logout")
    async def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        if _is_authed(request):
            return RedirectResponse("/purchases", status_code=303)
        return RedirectResponse("/login", status_code=303)

    @app.get("/purchases", response_class=HTMLResponse)
    async def purchases_page(request: Request, status: str = "pending"):
        if redirect := _auth_redirect(request):
            return redirect
        status_filter: PurchaseStatus | None
        if status == "all":
            status_filter = None
        else:
            try:
                status_filter = PurchaseStatus(status)
            except ValueError:
                status_filter = PurchaseStatus.PENDING
                status = "pending"

        async with async_session_factory() as session:
            repo = PurchaseRepository(session)
            purchases = await repo.list_by_status(status_filter, limit=200)
            pending_count = await repo.count_by_status(PurchaseStatus.PENDING)
            paid_count = await repo.count_by_status(PurchaseStatus.PAID)

        return templates.TemplateResponse(
            request,
            "purchases.html",
            {
                "purchases": purchases,
                "status": status,
                "status_labels": STATUS_LABELS,
                "status_badge": STATUS_BADGE,
                "product_labels": PRODUCT_LABELS,
                "pending_count": pending_count,
                "paid_count": paid_count,
                "settings": settings,
            },
        )

    @app.post("/purchases/{purchase_id}/confirm")
    async def purchase_confirm(request: Request, purchase_id: int):
        if redirect := _auth_redirect(request):
            return redirect
        from aiogram import Bot

        bot = Bot(token=settings.bot_token)
        try:
            async with async_session_factory() as session:
                await confirm_purchase(bot, settings, session, purchase_id)
        finally:
            await bot.session.close()
        return RedirectResponse("/purchases?status=pending", status_code=303)

    @app.post("/purchases/{purchase_id}/reject")
    async def purchase_reject(request: Request, purchase_id: int):
        if redirect := _auth_redirect(request):
            return redirect
        from aiogram import Bot

        bot = Bot(token=settings.bot_token)
        try:
            async with async_session_factory() as session:
                await reject_purchase(bot, session, purchase_id)
        finally:
            await bot.session.close()
        return RedirectResponse("/purchases?status=pending", status_code=303)

    @app.get("/users", response_class=HTMLResponse)
    async def users_page(request: Request, q: str = ""):
        if redirect := _auth_redirect(request):
            return redirect
        async with async_session_factory() as session:
            users = await UserRepository(session).list_for_dashboard(search=q or None, limit=100)
            chat_repo = ChatMessageRepository(session)
            message_counts = {
                user.id: await chat_repo.count_for_user(user.id) for user in users
            }

        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "users": users,
                "search": q,
                "message_counts": message_counts,
                "settings": settings,
            },
        )

    @app.get("/users/{user_id}/chat", response_class=HTMLResponse)
    async def user_chat_page(request: Request, user_id: int):
        if redirect := _auth_redirect(request):
            return redirect
        async with async_session_factory() as session:
            user = await UserRepository(session).get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            messages = await ChatMessageRepository(session).list_for_user(user_id, limit=500)
            pending = await PurchaseRepository(session).list_by_status(PurchaseStatus.PENDING, limit=50)
            user_pending = [p for p in pending if p.user_id == user_id]

        return templates.TemplateResponse(
            request,
            "chat.html",
            {
                "user": user,
                "messages": messages,
                "pending_purchases": user_pending,
                "product_labels": PRODUCT_LABELS,
                "status_labels": STATUS_LABELS,
                "settings": settings,
            },
        )

    return app
