from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from ap.builder import WordSearchGameBuilder
from ap.contract_adapter import ContractAdapter
from ap.facade import ActivityProviderFacade
from ap.instance_manager import InstanceManager
from ap.models import (
    AnalyticsListResponse,
    AnalyticsQueryRequest,
    UserUrlResponse,
)
from ap.persistence_proxy import PersistenceProxy
from ap.store_json import JsonFileDatabase


def _base_url_from_env() -> str:
    return os.getenv("BASE_URL", "").strip()


def _public_base_url(request: Request) -> str:
    """
    Resolve a URL pública considerando reverse-proxy (Nginx) e subpath (root_path).

    Prioridade:
    - X-Forwarded-Proto / X-Forwarded-Host (proxy)
    - request.url (execução local)
    - X-Forwarded-Prefix OU root_path (subpath)
    """
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.netloc
    )
    prefix = request.headers.get("x-forwarded-prefix") or (
        request.scope.get("root_path") or ""
    )
    prefix = prefix.rstrip("/")
    return f"{proto}://{host}{prefix}"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Activity Provider – Inven!RA (Padrões Estruturais)",
        version="1.0.0",
        description="Sopa de Letras – APSI/MEIW: Facade + Adapter + Proxy (com suporte de Builder/Singleton).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    data_path = os.getenv(
        "DATA_PATH",
        os.path.join(os.path.dirname(__file__), "data", "store.json"),
    )
    db = JsonFileDatabase(data_path)
    proxy = PersistenceProxy(db)
    adapter = ContractAdapter()
    instance_manager = InstanceManager()
    builder = WordSearchGameBuilder()

    # Mantém BASE_URL como fallback (útil em ambientes sem proxy),
    # mas preferimos derivar dinamicamente por request quando possível.
    facade = ActivityProviderFacade(
        adapter=adapter,
        proxy=proxy,
        instance_manager=instance_manager,
        builder=builder,
        base_url=_base_url_from_env(),
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Home extremamente simples: redireciona para static/index.html
    @app.get("/", include_in_schema=False)
    def home(request: Request):
        base = (request.scope.get("root_path") or "").rstrip("/")
        target = f"{base}/static/index.html"
        # 307 preserva método, mas aqui é GET; poderia ser 302 também.
        return RedirectResponse(url=target, status_code=307)

    # ------------------------------------------------------------------
    # /config_url e /config
    # ------------------------------------------------------------------
    @app.get("/config_url", response_class=HTMLResponse, tags=["InvenRA Contract"])
    @app.get("/config", response_class=HTMLResponse, tags=["Compatibility"])
    def config_url(request: Request):
        # Gera HTML coerente com o host/proto/prefixo do ambiente atual
        public_base = _public_base_url(request)
        return facade.get_config_html(public_base_url=public_base)

    # ------------------------------------------------------------------
    # /json_params_url e /params
    # ------------------------------------------------------------------
    @app.get("/json_params_url", tags=["InvenRA Contract"])
    @app.get("/params", tags=["Compatibility"])
    def json_params_url():
        """
        Endpoint de contrato Inven!RA para parâmetros da atividade.

        Devolve uma lista JSON de objetos:
        [
          {"name": "nome", "type": "text/plain"},
          ...
        ]
        """
        return facade.get_params_contract()

    # ------------------------------------------------------------------
    # /user_url e /deploy
    # ------------------------------------------------------------------
    @app.get("/user_url", response_model=UserUrlResponse, tags=["InvenRA Contract"])
    @app.get("/deploy", response_model=UserUrlResponse, tags=["Compatibility"])
    def user_url(
        request: Request,
        activityID: str = Query(..., description="Activity identifier"),
        userID: Optional[str] = Query(default=None),
    ):
        public_base = _public_base_url(request)
        return facade.resolve_user_url(activityID, userID, public_base_url=public_base)

    # ------------------------------------------------------------------
    # /analytics_list_url e /analytics/available
    # ------------------------------------------------------------------
    @app.get(
        "/analytics_list_url",
        tags=["InvenRA Contract"],
    )
    @app.get(
        "/analytics/available",
        tags=["Compatibility"],
    )
    def analytics_list_url():
        """
        Lista de analytics disponíveis no formato da app anterior (20/20):

        {
          "qualAnalytics":  [ { "name": "...", "type": "..." }, ... ],
          "quantAnalytics": [ { "name": "...", "type": "..." }, ... ]
        }
        """
        return facade.list_analytics()

    # ------------------------------------------------------------------
    # /analytics_url e /analytics
    # ------------------------------------------------------------------
    @app.post("/analytics_url", tags=["InvenRA Contract"])
    @app.post("/analytics", tags=["Compatibility"])
    def analytics_url(req: AnalyticsQueryRequest):
        """
        Serviço de analytics no formato da app anterior (20/20).

        Request típico (exemplo):
        {
          "activityID": "TESTE123"
        }

        Resposta (mock):

        [
          {
            "inveniraStdID": 1001,
            "quantAnalytics": [...],
            "qualAnalytics": [...]
          },
          ...
        ]
        """
        payload = adapter.adapt_analytics_request(req)
        return facade.query_analytics(payload)

    # ------------------------------------------------------------------
    # /game/{activityID} – página demo para simular entry_url
    # ------------------------------------------------------------------
    @app.get("/game/{activityID}", response_class=HTMLResponse, tags=["Demo"])
    def game_page(request: Request, activityID: str, userID: Optional[str] = None):
        facade.track_game_access(activityID, userID)
        base = (request.scope.get("root_path") or "").rstrip("/")
        return f"""<!doctype html>
<html lang='pt-br'>
<head><meta charset='utf-8'><title>Sopa de Letras</title></head>
<body>
  <h2>Sopa de Letras (Demo) – activityID={activityID}</h2>
  <p>Esta página simula o <strong>entry_url</strong> devolvido pela operação user_url/deploy.</p>
  <p>userID: {userID or "-"} </p>
  <p>Ao abrir esta página, um evento 'game_access' é gravado para permitir testar analytics.</p>
  <p><a href="{base}/static/index.html">Voltar para páginas de teste</a></p>
</body>
</html>"""

    return app


app = create_app()
