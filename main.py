from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ap.builder import WordSearchGameBuilder
from ap.contract_adapter import ContractAdapter
from ap.facade import ActivityProviderFacade
from ap.instance_manager import InstanceManager
from ap.models import (
    AnalyticsListResponse,
    AnalyticsQueryRequest,
    ParamsResponse,
    UserUrlResponse,
)
from ap.persistence_proxy import PersistenceProxy
from ap.store_json import JsonFileDatabase


def _base_url_from_env() -> str:
    return os.getenv("BASE_URL", "").strip()


def _path_prefix(request: Request) -> str:
    """
    Prefixo de path (subpath) onde a app está publicada.

    Prioridade:
      1) X-Forwarded-Prefix (quando definido no Nginx)
      2) root_path (quando definido pelo uvicorn --root-path)
      3) vazio
    """
    prefix = request.headers.get(
        "x-forwarded-prefix") or (request.scope.get("root_path") or "")
    return prefix.rstrip("/")


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

    prefix = request.headers.get(
        "x-forwarded-prefix") or (request.scope.get("root_path") or "")
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

    # Página principal com o layout da entrega 20/20, mas consciente do prefixo (subpath).
    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        base = _path_prefix(request)

        return f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Provider – Inven!RA</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2rem;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
        }}
        .card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 100%;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        h2 {{
            color: #555;
            font-size: 1.1rem;
            margin-top: 0;
            margin-bottom: 0.5rem;
            font-weight: normal;
        }}
        .project-title {{
            color: #0066cc;
            font-weight: bold;
            font-size: 1.3rem;
            margin-top: 1.5rem;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.5rem;
        }}
        .section-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-top: 1.5rem;
            color: #333;
        }}
        ul {{
            line-height: 1.8;
            background: #fafafa;
            padding: 1rem 2rem;
            border-radius: 8px;
            border: 1px solid #eee;
        }}
        a {{
            color: #0066cc;
            font-weight: bold;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f2f2f2;
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
        }}
    </style>
</head>
<body>

    <div class="card">
        <h1>MEIW – Mestrado em Engenharia Informática e Tecnologia Web</h1>
        <h2>Arquitetura e Padrões de Software (APSI)</h2>
        <h2>Ano letivo 2025/2026</h2>

        <div class="project-title">Arquitetura Inven!RA - Activity Provider – Sopa de Letras (Padrões Estruturais)</div>

        <p>Bem-vindo. Abaixo encontra uma lista dos serviços REST disponíveis para integração:</p>

        <h3 class="section-title">📡 Endpoints</h3>
        <ul>
            <li><a href="{base}/config" target="_blank">{base}/config</a> – Página de configuração da atividade (HTML)</li>
            <li><a href="{base}/params" target="_blank">{base}/params</a> – Lista de parâmetros configuráveis (JSON)</li>
            <li><a href="{base}/analytics/available" target="_blank">{base}/analytics/available</a> – Lista de analytics disponíveis (JSON)</li>
            <li><a href="{base}/deploy?activityID=TESTE123" target="_blank">{base}/deploy?activityID=TESTE123</a> – Simulação de Deploy</li>
        </ul>

        <h3 class="section-title">🧪 Testes</h3>
        <ul>
            <li><a href="{base}/static/teste_analytics_POST.html" target="_blank">Página de teste do POST /analytics</a></li>
        </ul>

        <h3 class="section-title">📘 Documentação</h3>
        <ul>
            <li><a href="{base}/docs" target="_blank">Swagger UI</a> – Interface de documentação</li>
        </ul>
    </div>

</body>
</html>"""

    @app.get("/config_url", response_class=HTMLResponse, tags=["InvenRA Contract"])
    @app.get("/config", response_class=HTMLResponse, tags=["Compatibility"])
    def config_url(request: Request):
        public_base = _public_base_url(request)
        # Requer que facade.get_config_html aceite public_base_url (ajuste no facade.py).
        return facade.get_config_html(public_base_url=public_base)

    @app.get("/json_params_url", response_model=ParamsResponse, tags=["InvenRA Contract"])
    @app.get("/params", response_model=ParamsResponse, tags=["Compatibility"])
    def json_params_url():
        return {"schema": facade.get_json_params_schema()}

    @app.get("/user_url", response_model=UserUrlResponse, tags=["InvenRA Contract"])
    @app.get("/deploy", response_model=UserUrlResponse, tags=["Compatibility"])
    def user_url(
        request: Request,
        activityID: str = Query(..., description="Activity identifier"),
        userID: Optional[str] = Query(default=None),
    ):
        public_base = _public_base_url(request)
        # Requer que facade.resolve_user_url aceite public_base_url (ajuste no facade.py).
        return facade.resolve_user_url(activityID, userID, public_base_url=public_base)

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
    def game_page(request: Request, activityID: str, userID: Optional[str] = None):
        facade.track_game_access(activityID, userID)
        base = _path_prefix(request)
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
