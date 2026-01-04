# Activity Provider – Inven!RA
### Jogo Sopa de Letras – Padrões Estruturais (Facade + Adapter + Proxy)

### UC: Arquitetura e Padrões de Software (APSI) – MEIW – UAb/UTAD  
### Autor: Weber Marcelo Guirra de Souza

---

## Objetivo do Projeto

Este projeto implementa um **Activity Provider** compatível com a plataforma **Inven!RA**, com foco na e-atividade de **padrões estruturais**, evidenciando explicitamente:

- **Facade**: `ActivityProviderFacade` como ponto único para os casos de uso do Activity Provider
- **Adapter**: `ContractAdapter` para normalização/validação e adaptação do contrato (requests/DTOs)
- **Proxy**: `PersistenceProxy` para intermediar o acesso à persistência (cache + lazy load + centralização de acesso)

Como suporte (de atividades anteriores), este projeto mantém:
- **Builder**: `WordSearchGameBuilder` para criação/configuração da instância do jogo
- **Singleton (apoio)**: `InstanceManager` para registo em memória (mapeamento activityID → instance_id)

O Activity Provider permite que a plataforma Inven!RA:
- Renderize a página de configuração da atividade
- Obtenha a lista de parâmetros configuráveis
- Resolva a URL de acesso à instância (user_url / deploy – 1ª fase)
- Obtenha a lista de analytics disponíveis
- Consulte analytics agregados (POST)

---

## Tecnologias Utilizadas

- Python 3.x
- FastAPI – Framework para APIs REST
- Uvicorn – Servidor ASGI
- HTML/JS – Páginas estáticas de teste (sem Postman)

---

# URL de Produção (VPS)

O serviço está publicado em:

`http://69.6.220.255:9000/`

---

# Endpoints Implementados (versão final)

Os endpoints abaixo seguem o **modelo do repositório anterior** (compatibilidade) e mantêm **aliases do contrato**.

> Nota importante: **user_url é GET** (e não POST).

---

## 1) Página de configuração da atividade

### `GET /config`  (alias contrato: `GET /config_url`)

Retorna HTML contendo os campos de configuração.

Exemplo:

```text
http://69.6.220.255:9000/config
```

---

## 2) Lista de parâmetros configuráveis

### `GET /params` (alias contrato: `GET /json_params_url`)

Retorna JSON com schema/parametrização.

Exemplo:

```text
http://69.6.220.255:9000/params
```

---

## 3) Deploy / Resolução de user_url (1ª fase)

### `GET /deploy?activityID=XXXX` (alias contrato: `GET /user_url?activityID=XXXX`)

Retorna JSON com `entry_url` (URL de acesso ao jogo para o aluno).

Exemplo:

```text
http://69.6.220.255:9000/deploy?activityID=TESTE123
```

---

## 4) Analytics agregados

### `POST /analytics` (alias contrato: `POST /analytics_url`)

URL:

```text
http://69.6.220.255:9000/analytics
```

Body exemplo:

```json
{
  "activityID": "TESTE123",
  "query": "default",
  "params": {},
  "userID": "ALUNO_01"
}
```

---

## 5) Lista de analytics disponíveis

### `GET /analytics/available` (alias contrato: `GET /analytics_list_url`)

Exemplo:

```text
http://69.6.220.255:9000/analytics/available
```

---

## Página de teste do POST `/analytics`

Para testar o endpoint sem Postman, use a página HTML interativa:

```text
http://69.6.220.255:9000/static/teste_analytics_POST.html
```

---

## Swagger (documentação automática)

```text
http://69.6.220.255:9000/docs
```

---

# Páginas de teste (HTML)

No mesmo estilo do repositório anterior:

- Índice: `/static/index.html`
- Deploy (GET): `/static/teste_deploy_GET.html`
- Analytics (POST): `/static/teste_analytics_POST.html`

Exemplo:

```text
http://69.6.220.255:9000/static/index.html
```

---

# Estrutura do Projeto

```
AP_invenra_Padrões_estrutura/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   ├── index.html
│   ├── teste_deploy_GET.html
│   └── teste_analytics_POST.html
└── ap/
    ├── facade.py              # Facade
    ├── contract_adapter.py    # Adapter
    ├── persistence_proxy.py   # Proxy
    ├── store_json.py          # persistência simples (JSON)
    ├── builder.py             # Builder (suporte)
    ├── instance_manager.py    # Singleton (suporte)
    └── models.py              # DTOs (Pydantic)
```

---

# Como os padrões aparecem no código (mapeamento rápido)

- **Facade**: `ap/facade.py` → `ActivityProviderFacade`
- **Adapter**: `ap/contract_adapter.py` → `ContractAdapter`
- **Proxy**: `ap/persistence_proxy.py` → `PersistenceProxy` (usa `ap/store_json.py`)
- **Suporte (atividade anterior)**:
  - `ap/builder.py` → `WordSearchGameBuilder`
  - `ap/instance_manager.py` → `InstanceManager`

---

# Executando Localmente

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

Abrir:
- `http://127.0.0.1:8080/`
- `http://127.0.0.1:8080/docs`
- `http://127.0.0.1:8080/static/index.html`

---

# Executando no VPS (porta 9000)

Exemplo de execução:

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9000
```

---

# Repositório no GitHub

Nome do repositório:

`AP_invenra_Padrões_estrutura`

---

# Contato

Weber Marcelo Guirra de Souza  
MEIW – Universidade Aberta / UTAD