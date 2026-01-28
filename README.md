# Portal Vendrame — New Frontend (Flask + HTML/CSS)

Este repositório contém a base do **Portal Vendrame**, com foco inicial nas telas de **Login**, **Home** e **Esqueci minha senha**, utilizando:

- **Python + Flask** (backend)
- **HTML + CSS + JS** (frontend)
- **SQLite** (banco de dados local)

---

## Objetivo do Portal

O Portal Vendrame terá como objetivo permitir que:

- **Clientes** criem solicitações através de formulários
- **Clientes** acompanhem o status das solicitações
- **Consultores** tratem solicitações e atualizem o status

Nesta fase, o projeto contém a base de autenticação e layout inicial.

---

## Estrutura de Pastas

```txt
VENDRAME - NEW FRONTEND/
│
├── app.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── db.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── home.py
│       ├── home_admin.py
│       ├── home_consultor.py
│       ├── home_router.py
│       ├── minhas_solicitacoes.py
│       ├── solicitacao_agendamento.py
│       ├── solicitacoes_consultor.py
│       └── users_admin.py
│
├── database/
│   ├── Users.db
│   ├── init_db.py
│   ├── clear_admissional.py
│   ├── clear_periodico.py
│   ├── create_table_admissional.py
│   ├── create_table_avaliacao.py
│   ├── create_table_demissional.py
│   ├── create_table_mudanca.py
│   ├── create_table_periodico.py
│   ├── create_table_retorno.py
│   ├── migration_add_resposta_consultor.py
│   │
│   ├── Documentos_Admissional/
│   │   └── <PROTOCOLO>/
│   │       └── arquivos...
│   ├── Documentos_Avaliacao/
│   │   └── <PROTOCOLO>/
│   │       └── arquivos...
│   ├── Documentos_Demissional/
│   │   └── <PROTOCOLO>/
│   │       └── arquivos...
│   ├── Documentos_Mudanca/
│   │   └── <PROTOCOLO>/
│   │       └── arquivos...
│   ├── Documentos_Periodico/
│   │   └── <PROTOCOLO>/
│   │       └── arquivos...
│   └── Documentos_Retorno/
│       └── <PROTOCOLO>/
│           └── arquivos...
│
├── static/
│   ├── assets/
│   │   ├── acessos.png
│   │   ├── agendamentos.png
│   │   ├── andamento.png
│   │   ├── comparecimento.png
│   │   ├── icone.png
│   │   ├── login_bg.jpg
│   │   ├── logo_vendrame.png
│   │   ├── solicitacao.png
│   │   └── solicitacoes.png
│   │
│   ├── css/
│   │   ├── controle_usuarios.css
│   │   ├── home_consultor.css
│   │   ├── home.css
│   │   ├── login.css
│   │   ├── minhas_solicitacoes.css
│   │   ├── solicitacao_agendamento.css
│   │   ├── solicitacoes_consultor.css
│   │   └── tipos_solicitacao.css
│   │
│   └── js/
│       ├── controle_usuarios.js
│       ├── login.js
│       ├── minhas_solicitacoes.js
│       ├── solicitacao_agendamento.js
│       └── solicitacoes_consultor.js
│
└── templates/
    ├── home.html
    ├── home_admin.html
    ├── home_consultor.html
    ├── minhas_solicitacoes.html
    ├── solicitacao_agendamento.html
    ├── solicitacoes_consultor.html
    ├── tipos_solicitacao.html
    └── auth/
        ├── login.html
        └── forgot_password.html

```

---

## Como executar o projeto

### 1) Criar e ativar ambiente virtual

**Windows (PowerShell):**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Instalar dependências
```bash
pip install -r requirements.txt
```

### 3) Configurar `.env` (recomendado)

Crie/edite o arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=dev-secret-change-me
DATABASE_PATH=database/Users.db
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4) Criar/Recriar o banco (`Users.db`)

Você pode criar o banco e também inserir usuários de teste.

**Criar (mantém se já existir):**
```bash
python database/init_db.py --seed-defaults
```

**Recriar do zero (faz backup antes):**
```bash
python database/init_db.py --reset --seed-defaults
```

Usuários de teste criados:

- **admin / admin** (administrador)
- **consultor / consultor** (consultor)
- **cliente / cliente** (cliente)

### 5) Rodar o servidor
```bash
python app.py
```

Acesse no navegador:

- Login: `http://127.0.0.1:5000/login`
- Esqueci senha: `http://127.0.0.1:5000/esqueci-senha`
- Home: `http://127.0.0.1:5000/home`

---

## Rotas principais

### Autenticação (`backend/routes/auth.py`)
- `GET /login` → exibe tela de login
- `POST /login` → valida credenciais e cria sessão
- `GET /esqueci-senha` → exibe tela de redefinição
- `POST /esqueci-senha` → redefine a senha do usuário (se existir)

### Home (`backend/routes/home.py`)
- `GET /home` → tela inicial após login

---

## Banco de dados (SQLite)

Arquivo do banco:
- `database/Users.db`

Tabela principal:
- `"user"`: armazena usuários do portal

Campos:
- `user` (PK)
- `password`
- `type` (`cliente`, `consultor`, `administrador`)
- `email`
- `name`

---

## Observações importantes

- O `.env` é **opcional**, porém recomendado para manter `SECRET_KEY` e o caminho do banco fora do código.
- O arquivo `Users.db` pode ser ignorado no Git (recomendado) e recriado com `init_db.py`.
- A senha atualmente está em texto puro (fase inicial). Em produção, deve ser aplicado **hash** (ex.: `werkzeug.security`).
