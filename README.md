# RetailFlow — E-Commerce Web Application

Aplicação web de e-commerce construída com **FastAPI**, **SQLAlchemy 2.0 (assíncrono)**, **PostgreSQL 16** e **Jinja2**, desenvolvida com arquitetura modular e preparada para servir como sistema-alvo para futuras automações de testes com Robot Framework (em repositório dedicado).

> **Aviso Importante:** Este repositório (`alicemavila/retailflow-ecommerce`) contém exclusivamente a aplicação de e-commerce e seus testes unitários/integração com Pytest. O projeto de automação com Robot Framework será mantido em um repositório independente.

---

## 1. Tecnologias Utilizadas

* **Linguagem:** Python 3.12+
* **Framework Web:** FastAPI (endpoints assíncronos)
* **Persistência / ORM:** SQLAlchemy 2.0 Assíncrono com driver `asyncpg`
* **Migrações de Banco:** Alembic (com suporte a async)
* **Banco de Dados:** PostgreSQL 16
* **Interface / SSR:** Jinja2 + HTML5/CSS/JavaScript
* **Configuração:** Pydantic Settings (validação via `.env`)
* **Containerização:** Docker e Docker Compose
* **Testes Internos:** Pytest + `pytest-asyncio` + `httpx`

---

## 2. Pré-requisitos

Para executar o projeto, certifique-se de possuir instalado em sua máquina:
* [Docker](https://docs.docker.com/get-docker/) (versão 20.10+) e Docker Compose (v2+)
* [Python 3.12+](https://www.python.org/downloads/) (caso queira executar a aplicação ou testes fora do container)
* Git

---

## 3. Configuração de Variáveis de Ambiente

Antes de inicializar a aplicação, crie o arquivo `.env` a partir do modelo ilustrativo `.env.example`:

```bash
# No Linux/macOS
cp .env.example .env

# No Windows PowerShell
Copy-Item .env.example .env
```

Abra o arquivo `.env` gerado e defina valores seguros para:
* `SECRET_KEY`: Chave aleatória de no mínimo 32 caracteres (ex.: gerada com `openssl rand -hex 32`).
* `POSTGRES_DEV_PASSWORD`: Senha segura para o usuário do banco de desenvolvimento.
* `POSTGRES_TEST_PASSWORD`: Senha segura para o usuário do banco de testes.
* `INITIAL_ADMIN_PASSWORD`: Senha para criação do primeiro usuário administrador.

> **Atenção:** O arquivo `.env` contém credenciais e está devidamente incluído no `.gitignore`. **Nunca faça commit do `.env` real no controle de versão.**

---

## 4. Executando a Aplicação com Docker Compose

O Docker Compose orquestra o banco PostgreSQL 16 e o serviço web do FastAPI em uma rede isolada.

### Iniciar os serviços:
```bash
docker compose up -d --build
```

O comando irá:
1. Criar o volume de dados persistente `retailflow_postgres_data`.
2. Provisionar o container do PostgreSQL (`db`).
3. Executar o script de inicialização `init-databases.sh` que cria os bancos `retailflow_dev` e `retailflow_test` com usuários e privilégios independentes.
4. Aguardar o `healthcheck` do banco de dados ser aprovado.
5. Iniciar o container da aplicação (`web`) expondo a porta `8000`.

### Acompanhar os logs em tempo real:
```bash
docker compose logs -f web
```

### Encerrar os serviços:
```bash
# Para parar os containers preservando todos os dados gravados no banco:
docker compose down

# Para parar os containers e apagar completamente os volumes de dados:
# ATENÇÃO: 'down -v' remove o volume 'retailflow_postgres_data', causando PERDA IRREVERSÍVEL de todos os dados locais.
docker compose down -v
```

---

## 5. Verificação de Saúde da Aplicação

Com os serviços em execução, você pode validar a conectividade e integridade do sistema acessando:

* **Endpoint de Saúde (JSON):**
  [http://localhost:8000/health](http://localhost:8000/health)

  Exemplo de resposta esperada:
  ```json
  {
    "status": "healthy",
    "app": "RetailFlow E-Commerce",
    "environment": "development",
    "version": "0.1.0",
    "database": "connected"
  }
  ```

* **Documentação Interativa Swagger/OpenAPI:**
  [http://localhost:8000/docs](http://localhost:8000/docs)

* **Documentação ReDoc:**
  [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Arquitetura de Bancos: Desenvolvimento vs. Testes

Para garantir que a execução de testes automatizados nunca corrompa ou apague dados utilizados no desenvolvimento ou em demonstrações manuais, a instância PostgreSQL conta com **dois bancos lógicos totalmente separados**:

| Propriedade | Banco de Desenvolvimento | Banco de Testes |
| :--- | :--- | :--- |
| **Nome do Banco** | `retailflow_dev` | `retailflow_test` |
| **Usuário Exclusivo** | `retailflow_dev_user` | `retailflow_test_user` |
| **Privilégios** | Restrito a `retailflow_dev` | Restrito a `retailflow_test` |
| **Finalidade** | Desenvolvimento local, navegação web e API manual | Execução automatizada da suíte Pytest |
| **Variável de Conexão** | `DATABASE_URL` | `TEST_DATABASE_URL` |

### Particularidades Críticas de Inicialização do PostgreSQL:
1. **Execução Única na Criação do Volume:** O script `docker/postgres/init-databases.sh` é montado em `/docker-entrypoint-initdb.d/` e é **executado pelo container do PostgreSQL exclusivamente na primeira inicialização de um volume de dados novo e vazio**.
2. **Alterações Posteriores no Script:** Modificações feitas em `init-databases.sh` após a criação inicial do volume **NÃO são aplicadas automaticamente** a um volume já existente.
3. **Reset e Recriação dos Bancos:** Caso seja necessário reexecutar o script de provisionamento dos bancos ou redefinir permissões do zero, é obrigatório destruir o volume existente com `docker compose down -v` e reiniciar com `docker compose up -d` (lembrando que essa operação apaga todos os dados locais do banco).

### Salvaguarda do Ambiente de Testes (`scripts/verify_db_safety.py`):
Todas as rotas de teste e futuros scripts de limpeza são obrigados a validar a conexão por meio da função `assert_safe_test_environment`:
* Valida se `ENVIRONMENT == "test"`.
* Valida se o banco apontado na URL é exatamente `retailflow_test`.
* Valida se o usuário pertence à lista de autorizados (`retailflow_test_user`).
* Valida se o host pertence à lista autorizada (`localhost`, `127.0.0.1`, `db`, `retailflow_postgres`, `postgres`).
* Nunca expõe senhas ou credenciais em mensagens de erro ou logs (sanitização estrita).

Para executar a validação de salvaguarda manualmente:
```bash
python scripts/verify_db_safety.py
```

---

## 7. Próximos Passos (Planejamento)

A implementação segue as fases planejadas:
* [x] **Etapa 1:** Configuração Base, Ambientes e Docker (Atual)
* [ ] **Etapa 2:** Modelagem do Banco, Migrações Alembic e Scripts de Seed
* [ ] **Etapa 3:** Segurança, Autenticação e CSRF
* [ ] **Etapa 4:** Categorias, Catálogo e Movimentação de Estoque
* [ ] **Etapa 5:** Carrinho de Compras
* [ ] **Etapa 6:** Checkout, Pagamento Simulado e Idempotência
* [ ] **Etapa 7:** Painel Administrativo
* [ ] **Etapa 8:** Suíte de Testes Pytest e Documentação Final
