from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from .builder import WordSearchGameBuilder
from .contract_adapter import ContractAdapter
from .instance_manager import InstanceManager
from .persistence_proxy import PersistenceProxy

# Contrato de parâmetros da atividade no formato Inven!RA.
# Fonte única de verdade para o endpoint /params /json_params_url.
_PARAMS_CONTRACT: list[dict[str, str]] = [
    {"name": "nome", "type": "text/plain"},
    {"name": "orientacoes", "type": "text/plain"},
    {"name": "tempoLimiteSegundos", "type": "integer"},
    {"name": "tamanhoQuadro", "type": "integer"},
    {"name": "sensivelMaiusculas", "type": "boolean"},
    {"name": "permitirDiagonais", "type": "boolean"},
    {"name": "parametrosPalavras", "type": "json"},
]


class ActivityProviderFacade:
    """Facade (Structural Pattern) for Activity Provider use-cases."""

    def get_params_contract(self) -> list[dict[str, str]]:
        """
        Devolve o contrato de parâmetros no formato esperado pela Inven!RA:

        [
          {"name": "nome", "type": "text/plain"},
          ...
        ]
        """
        return self._params_contract

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
        self._params_contract = _PARAMS_CONTRACT

    def _effective_base_url(self, public_base_url: Optional[str] = None) -> str:
        """
        Preferir public_base_url (derivado do Request/Proxy),
        senão usar base_url (env BASE_URL), senão retornar string vazia (URLs relativas).
        """
        if public_base_url:
            return public_base_url.rstrip("/")
        if self.base_url:
            return self.base_url.rstrip("/")
        return ""

    def get_config_html(self, public_base_url: Optional[str] = None) -> str:
        """
        HTML igual ao projeto 20/20 (activity_provider_invenra).
        Não inclui botões; a Inven!RA recolhe campos diretamente.
        """
        _ = self._effective_base_url(
            # reservado (se quiser evoluir com <base href=...>)
            public_base_url)
        return """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8" />
        <title>Configuração – Sopa de Letras</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 1.5rem; }
            h1 { font-size: 1.4rem; }
            label { display: block; margin-top: 0.8rem; font-weight: bold; }
            input[type="text"], input[type="number"], textarea, select {
                width: 100%; max-width: 600px; padding: 0.3rem; margin-top: 0.2rem;
            }
            small { color: #555; display: block; margin-top: 0.15rem; }
            .checkbox-group { margin-top: 0.5rem; }
        </style>
    </head>
    <body>
        <h1>Configuração da Atividade – Jogo Sopa de Letras</h1>

        <label for="nome">Nome da atividade</label>
        <input id="nome" name="nome" type="text" value="Sopa de Letras – Vocabulário" />
        <small>Identificação da atividade para o professor.</small>

        <label for="orientacoes">Orientações para o aluno</label>
        <textarea id="orientacoes" name="orientacoes" rows="4">
Encontre todas as palavras relacionadas ao tema proposto, no idioma alvo, dentro do tempo limite.
        </textarea>
        <small>Texto exibido aos alunos com instruções da atividade.</small>

        <label for="tempoLimiteSegundos">Tempo limite por tentativa (segundos)</label>
        <input id="tempoLimiteSegundos" name="tempoLimiteSegundos" type="number" value="300" min="30" max="3600" />
        <small>Tempo máximo para o aluno completar uma tentativa.</small>

        <label for="tamanhoQuadro">Tamanho do quadro (linhas/colunas)</label>
        <input id="tamanhoQuadro" name="tamanhoQuadro" type="number" value="12" min="6" max="20" />
        <small>Define o tamanho da grelha de letras.</small>

        <div class="checkbox-group">
            <input id="sensivelMaiusculas" name="sensivelMaiusculas" type="checkbox" />
            <label for="sensivelMaiusculas" style="display:inline; font-weight:normal;">
                Diferenciar maiúsculas e minúsculas
            </label>
        </div>

        <div class="checkbox-group">
            <input id="permitirDiagonais" name="permitirDiagonais" type="checkbox" checked />
            <label for="permitirDiagonais" style="display:inline; font-weight:normal;">
                Permitir palavras na diagonal
            </label>
        </div>

        <label for="parametrosPalavras">Parâmetros de palavras (JSON)</label>
        <textarea id="parametrosPalavras" name="parametrosPalavras" rows="6">
{
  "idioma_nativo": ["cachorro", "gato", "casa"],
  "idioma_alvo": ["dog", "cat", "house"]
}
        </textarea>
        <small>JSON com listas de palavras no idioma nativo e no idioma de aprendizagem.</small>

        <!--
            Não há botão "Guardar" ou "OK": a Inven!RA recolhe os valores
            diretamente dos campos desta página.
        -->
    </body>
    </html>
        """.strip()

    def resolve_user_url(
        self,
        activity_id: str,
        user_id: Optional[str] = None,
        public_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Caminho completo (Facade -> Adapter -> InstanceManager -> Proxy -> Builder),
        evitando “retorno imediato” sem persistência.
        """
        activity_id = self.adapter.adapt_activity_id(activity_id)
        user_id = self.adapter.adapt_user_id(user_id)

        # 1) InstanceManager decide instance_id
        instance_id = self.instance_manager.get_instance_id(activity_id)
        if instance_id is None:
            instance_id = f"inst_{activity_id}"
            self.instance_manager.set_instance_id(activity_id, instance_id)

        # 2) Proxy verifica persistência
        existing = self.proxy.get_instance(instance_id)

        # 3) Builder cria config quando necessário
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

        # Se base estiver vazio, retorna URL relativa (funciona local e sob proxy)
        if base:
            entry_url = f"{base}/game/{activity_id}"
        else:
            entry_url = f"/game/{activity_id}"

        if user_id:
            entry_url = f"{entry_url}?userID={user_id}"

        return {
            "activityID": activity_id,
            "entry_url": entry_url,
            "instance_id": instance_id,
        }

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

        instance_id = self.instance_manager.get_instance_id(
            activity_id) or f"inst_{activity_id}"
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

        instance_id = self.instance_manager.get_instance_id(
            activity_id) or f"inst_{activity_id}"
        instance = self.proxy.get_instance(instance_id)

        if instance is None:
            # Mantém caminho completo: se alguém acessar /game direto, ainda cria/persiste corretamente
            game_cfg = self.builder.build()
            instance = {
                "instance_id": instance_id,
                "activityID": activity_id,
                "created_at": dt.datetime.utcnow().isoformat() + "Z",
                "game_config": game_cfg,
                "last_access": None,
                "access_count": 0,
            }

        instance["access_count"] = int(instance.get("access_count", 0)) + 1
        instance["last_access"] = dt.datetime.utcnow().isoformat() + "Z"
        self.proxy.upsert_instance(instance_id, instance)

        self.proxy.append_event({
            "ts": dt.datetime.utcnow().isoformat() + "Z",
            "type": "game_access",
            "activityID": activity_id,
            "userID": user_id,
        })
