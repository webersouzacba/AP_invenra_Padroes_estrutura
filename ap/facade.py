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

    # Utilitário interno para resolver o base_url efetivo

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

    # /config_url  (HTML de configuração – contrato Inven!RA)
    def get_config_html(self, public_base_url: Optional[str] = None) -> str:
        """
        HTML de configuração. A Inven!RA recolhe diretamente os valores dos campos desta página.
        """
        _ = self._effective_base_url(
            public_base_url)  # reservado para evolução

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

    # /user_url  (deploy – contrato Inven!RA)
    def resolve_user_url(
        self,
        activity_id: str,
        user_id: Optional[str] = None,
        public_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve o entry_url da atividade, percorrendo o caminho:
        Facade -> Adapter -> InstanceManager -> Proxy -> Builder.
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

    # /analytics_list_url  (lista de analytics disponíveis – contrato Inven!RA)
    def list_analytics(self) -> Dict[str, Any]:
        """
        Devolve a lista de analytics disponíveis no MESMO formato
        da aplicação anterior (20/20):

        {
          "qualAnalytics":  [ { "name": "...", "type": "..." }, ... ],
          "quantAnalytics": [ { "name": "...", "type": "..." }, ... ]
        }
        """
        return {
            "qualAnalytics": [
                {"name": "ultima_palavra_encontrada", "type": "text/plain"},
                {"name": "sequencia_cliques", "type": "array/string"},
            ],
            "quantAnalytics": [
                {"name": "tentativas_total", "type": "integer"},
                {"name": "tentativas_corretas", "type": "integer"},
                {"name": "tentativas_erradas", "type": "integer"},
                {"name": "tempo_medio_por_acerto_s", "type": "number"},
                {"name": "percentual_acertos", "type": "number"},
                {"name": "percentual_erros", "type": "number"},
            ],
        }

    # /analytics_url  (analytics – contrato Inven!RA + mock)
    def query_analytics(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Versão MOCK do serviço /analytics, devolvendo um JSON
        [
          {
            "inveniraStdID": 1001,
            "quantAnalytics": [ { "name": "...","value": ... }, ... ],
            "qualAnalytics":  [ { "name": "...","value": ... }, ... ]
          },
          ...
        ]

        O parâmetro 'query' é aceite (via ContractAdapter), mas aqui
        é ignorado para simplificar; em cenário real, poderia filtrar
        ou agregar com base nos eventos em proxy.list_events(...).
        """
        activity_id = payload["activityID"]
        # user_id = payload.get("userID")
        # query = payload.get("query") or "default"
        # params = payload.get("params") or {}

        # Poderíamos usar self.proxy.list_events(...) aqui para gerar
        # dados reais; para a UC, basta MOCK reproduzindo o formato.

        # Dataset MOCK
        mock_data: List[Dict[str, Any]] = [
            {
                "inveniraStdID": 1001,
                "quantAnalytics": [
                    {"name": "tentativas_total", "value": 5},
                    {"name": "tentativas_corretas", "value": 4},
                    {"name": "tentativas_erradas", "value": 1},
                    {"name": "tempo_medio_por_acerto_s", "value": 42.5},
                    {"name": "percentual_acertos", "value": 80},
                    {"name": "percentual_erros", "value": 20},
                ],
                "qualAnalytics": [
                    {"name": "ultima_palavra_encontrada", "value": "house"},
                    {
                        "name": "sequencia_cliques",
                        "value": ["h(1,1)", "o(1,2)", "u(1,3)", "s(1,4)", "e(1,5)"],
                    },
                ],
            },
            {
                "inveniraStdID": 1002,
                "quantAnalytics": [
                    {"name": "tentativas_total", "value": 3},
                    {"name": "tentativas_corretas", "value": 1},
                    {"name": "tentativas_erradas", "value": 2},
                    {"name": "tempo_medio_por_acerto_s", "value": 60},
                    {"name": "percentual_acertos", "value": 33.3},
                    {"name": "percentual_erros", "value": 66.7},
                ],
                "qualAnalytics": [
                    {"name": "ultima_palavra_encontrada", "value": "cat"},
                    {
                        "name": "sequencia_cliques",
                        "value": ["c(2,1)", "a(2,2)", "t(2,3)"],
                    },
                ],
            },
        ]

        # Futuramente diferenciar por activityID, trocar o dataset
        # com base em activity_id; aqui retornamos o mesmo conjunto.
        _ = activity_id  # apenas para deixar claro que está disponível
        return mock_data

    # ---------------------------------------------------------------------
    # Tracking de acesso ao jogo (para futura ligação com analytics real)
    # ---------------------------------------------------------------------
    def track_game_access(self, activity_id: str, user_id: Optional[str]) -> None:
        """
        Regista um evento de acesso ao jogo.

        Hoje é usado apenas para permitir cenários de analytics simples
        (contagem de acessos / eventos). Mesmo que o /analytics esteja
        em MOCK, este fluxo demonstra o uso do Proxy e do JsonFileDatabase.
        """
        activity_id = self.adapter.adapt_activity_id(activity_id)
        user_id = self.adapter.adapt_user_id(user_id)

        instance_id = self.instance_manager.get_instance_id(
            activity_id) or f"inst_{activity_id}"
        instance = self.proxy.get_instance(instance_id)

        if instance is None:
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
