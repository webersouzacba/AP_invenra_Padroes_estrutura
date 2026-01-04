from typing import Optional
from __future__ import annotations

import os
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ap.contract_adapter import ContractAdapter
from ap.facade import ActivityProviderFacade
from ap.instance_manager import InstanceManager
from ap.builder import WordSearchGameBuilder
from ap.store_json import JsonFileDatabase
from ap.persistence_proxy import PersistenceProxy
from ap.models import AnalyticsQueryRequest, AnalyticsListResponse, UserUrlResponse, ParamsResponse


def _base_url_from_env() -> str:
    return os.getenv("BASE_URL", "").strip()


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

    data_path = os.getenv("DATA_PATH", os.path.join(
        os.path.dirname(__file__), "data", "store.json"))
    db = JsonFileDatabase(data_path)
    proxy = PersistenceProxy(db)
    adapter = ContractAdapter()
    instance_manager = InstanceManager()
    builder = WordSearchGameBuilder()
    facade = ActivityProviderFacade(
        adapter=adapter,
        proxy=proxy,
        instance_manager=instance_manager,
        builder=builder,
        base_url=_base_url_from_env(),
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home():
        return """<html><body>
        <h2>Activity Provider – Inven!RA (Padrões Estruturais)</h2>
        <ul>
          <li><a href="/docs">Swagger UI</a></li>
          <li><a href="/config">GET /config</a></li>
          <li><a href="/params">GET /params</a></li>
          <li><a href="/deploy?activityID=TESTE123">GET /deploy?activityID=TESTE123</a></li>
          <li><a href="/analytics/available">GET /analytics/available</a></li>
          <li><a href="/static/index.html">Páginas de teste (HTML)</a></li>
        </ul>
        </body></html>"""

    @app.get("/config_url", response_class=HTMLResponse, tags=["InvenRA Contract"])
    @app.get("/config", response_class=HTMLResponse, tags=["Compatibility"])
    def config_url():
        return facade.get_config_html()

    @app.get("/json_params_url", response_model=ParamsResponse, tags=["InvenRA Contract"])
    @app.get("/params", response_model=ParamsResponse, tags=["Compatibility"])
    def json_params_url():
        return {"schema": facade.get_json_params_schema()}

    @app.get("/user_url", response_model=UserUrlResponse, tags=["InvenRA Contract"])
    @app.get("/deploy", response_model=UserUrlResponse, tags=["Compatibility"])
    def user_url(
        activityID: str = Query(..., description="Activity identifier"),
        userID: Optional[str] = Query(default=None),
    ):

        return facade.resolve_user_url(activityID, userID)

    @app.get("/analytics_list_url", response_model=AnalyticsListResponse, tags=["InvenRA Contract"])
    @app.get("/analytics/available", response_model=AnalyticsListResponse, tags=["Compatibility"])
    def analytics_list_url():
        return {"available_queries": facade.list_analytics()}

    @app.post("/analytics_url", tags=["InvenRA Contract"])
    @app.post("/analytics", tags=["Compatibility"])
    def analytics_url(req: AnalyticsQueryRequest):
        payload = adapter.adapt_analytics_request(req)
        result = facade.query_analytics(payload)
        return {"activityID": payload["activityID"], "query": payload["query"], "result": result}

    @app.get("/game/{activityID}", response_class=HTMLResponse, tags=["Demo"])
    def game_page(activityID: str, userID: str | None = None):
        facade.track_game_access(activityID, userID)
        return f"""<!doctype html>
<html lang='pt-br'>
<head><meta charset='utf-8'><title>Sopa de Letras</title></head>
<body>
  <h2>Sopa de Letras (Demo) – activityID={activityID}</h2>
  <p>Esta página simula o <strong>entry_url</strong> devolvido pela operação user_url/deploy.</p>
  <p>userID: {userID or "-"} </p>
  <p>Ao abrir esta página, um evento 'game_access' é gravado para permitir testar analytics.</p>
  <p><a href="/static/index.html">Voltar para páginas de teste</a></p>
</body>
</html>"""

    return app


app = create_app()
