from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from .builder import WordSearchGameBuilder
from .contract_adapter import ContractAdapter
from .instance_manager import InstanceManager
from .persistence_proxy import PersistenceProxy


class ActivityProviderFacade:
    """Facade (Structural Pattern) for Activity Provider use-cases."""

    def __init__(
        self,
        adapter: ContractAdapter,
        proxy: PersistenceProxy,
        instance_manager: InstanceManager,
        builder: WordSearchGameBuilder,
        base_url: str = "",
    ) -> None:
        self.adapter = adapter
        self.proxy = proxy
        self.instance_manager = instance_manager
        self.builder = builder
        self.base_url = (base_url or "").rstrip("/")

    def _effective_base_url(self, public_base_url: str = "") -> str:
        """
        Resolve a base URL final para montar links públicos.

        Prioridade:
          1) public_base_url (calculado no main via Request/proxy/root_path)
          2) self.base_url (via BASE_URL, fallback)
          3) "" (permite gerar URLs relativas, se necessário)
        """
        public_base_url = (public_base_url or "").strip().rstrip("/")
        if public_base_url:
            return public_base_url
        if self.base_url:
            return self.base_url
        return ""

    def get_config_html(self, public_base_url: str = "") -> str:
        base = self._effective_base_url(public_base_url)
        docs_href = f"{base}/docs" if base else "/docs"
        params_href = f"{base}/params" if base else "/params"
        deploy_href = f"{base}/deploy?activityID=TESTE123" if base else "/deploy?activityID=TESTE123"
        return f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Sopa de Letras - Config</title></head>
<body>
  <h2>Configuração - Sopa de Letras</h2>
  <p>Exemplo de página de configuração para o professor (APSI / Inven!RA).</p>

  <p><strong>Atalhos:</strong></p>
  <ul>
    <li><a href="{docs_href}">Swagger UI</a></li>
    <li><a href="{params_href}">GET /params</a></li>
    <li><a href="{deploy_href}">GET /deploy?activityID=TESTE123</a></li>
  </ul>

  <form>
    <label>Tamanho do tabuleiro: <input name="size" type="number" value="10"/></label><br/>
    <label>Palavras (separadas por vírgula): <input name="words" value="APSI,INVENIRA,FACADE,ADAPTER,PROXY"/></label><br/>
    <button type="button">Guardar (exemplo)</button>
  </form>
</body>
</html>"""

    def get_json_params_schema(self) -> Dict[str, Any]:
        return {
            "activity": "Sopa de Letras",
            "params": [
                {"name": "size", "type": "int", "default": 10, "min": 5, "max": 20},
                {"name": "words", "type": "list[str]", "default": [
                    "APSI", "INVENIRA", "FACADE", "ADAPTER", "PROXY"]},
            ],
        }

    def resolve_user_url(
        self,
        activity_id: str,
        user_id: Optional[str] = None,
        public_base_url: str = "",
    ) -> Dict[str, Any]:
        activity_id = self.adapter.adapt_activity_id(activity_id)
        user_id = self.adapter.adapt_user_id(user_id)

        instance_id = self.instance_manager.get_instance_id(activity_id)
        if instance_id is None:
            instance_id = f"inst_{activity_id}"
            self.instance_manager.set_instance_id(activity_id, instance_id)

        existing = self.proxy.get_instance(instance_id)
        if existing is None:
            game_cfg = self.builder.build()
            payload = {
                "instance_id": instance_id,
                "activityID": activity_id,
                "created_at": dt.datetime.utcnow().isoformat() + "Z",
                "game_config": game_cfg,
                "last_access": None,
                "access_count": 0,
            }
            self.proxy.upsert_instance(instance_id, payload)

        base = self._effective_base_url(public_base_url)

        # Se base estiver vazio, devolve URL relativa (útil em cenários locais simples).
        if base:
            entry_url = f"{base}/game/{activity_id}"
        else:
            entry_url = f"/game/{activity_id}"

        if user_id:
            if base:
                entry_url = f"{base}/game/{activity_id}?userID={user_id}"
            else:
                entry_url = f"/game/{activity_id}?userID={user_id}"

        return {"activityID": activity_id, "entry_url": entry_url, "instance_id": instance_id}

    def list_analytics(self) -> List[Dict[str, Any]]:
        return [
            {"id": "access_count", "label": "Total de acessos (por atividade)", "method": "POST analytics", "params": [
                "activityID"]},
            {"id": "events_count", "label": "Total de eventos (por atividade)", "method": "POST analytics", "params": [
                "activityID"]},
            {"id": "user_events_count",
                "label": "Eventos por aluno (activityID+userID)", "method": "POST analytics", "params": ["activityID", "userID"]},
        ]

    def query_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        activity_id = payload["activityID"]
        user_id = payload.get("userID")
        query = payload.get("query") or "default"

        instance_id = f"inst_{activity_id}"
        instance = self.proxy.get_instance(instance_id)
        access_count = (instance or {}).get("access_count", 0)

        events = self.proxy.list_events(
            activity_id=activity_id, user_id=user_id)
        result: Dict[str, Any] = {"activityID": activity_id, "query": query}

        if query in ("default", "access_count"):
            result["access_count"] = access_count
            result["created_at"] = (instance or {}).get("created_at")
        if query in ("default", "events_count"):
            result["events_count"] = len(
                self.proxy.list_events(activity_id=activity_id))
        if query == "user_events_count":
            result["user_events_count"] = len(events)
            result["userID"] = user_id

        return result

    def track_game_access(self, activity_id: str, user_id: Optional[str]) -> None:
        activity_id = self.adapter.adapt_activity_id(activity_id)
        user_id = self.adapter.adapt_user_id(user_id)

        instance_id = f"inst_{activity_id}"
        instance = self.proxy.get_instance(instance_id) or {
            "instance_id": instance_id,
            "activityID": activity_id,
            "created_at": dt.datetime.utcnow().isoformat() + "Z",
            "game_config": self.builder.build(),
            "last_access": None,
            "access_count": 0,
        }

        instance["access_count"] = int(instance.get("access_count", 0)) + 1
        instance["last_access"] = dt.datetime.utcnow().isoformat() + "Z"
        self.proxy.upsert_instance(instance_id, instance)

        self.proxy.append_event(
            {
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "type": "game_access",
                "activityID": activity_id,
                "userID": user_id,
            }
        )
