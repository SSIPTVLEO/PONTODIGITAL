# Ponto App - Auth + Postgres (Login/Cadastro separados, 3000m)

Recursos:
- Cadastro e Login em telas separadas (`/cadastro` e `/login`)
- JWT no backend; frontend salva token em `localStorage`
- Distância máxima para registro: **3000 metros**
- PostgreSQL pronto via `DATABASE_URL` (Render) com fallback para SQLite
- Migrações com Flask-Migrate
- Registros imutáveis + validação de localização

## Rodar localmente (SQLite)
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

export FLASK_APP=src.app
flask db init
flask db migrate -m "initial"
flask db upgrade

python seed.py
python -m src.app
```
Acesse:
- `http://localhost:5000/login`
- `http://localhost:5000/cadastro`
- `http://localhost:5000/` (dashboard)

## Deploy no Render
- `Procfile` já configurado: `web: gunicorn src.app:app`
- Variáveis de ambiente recomendadas:
  - `DATABASE_URL` (Postgres do Render)
  - `SECRET_KEY` (gera com `openssl rand -hex 32`)
  - opcional: `JWT_EXP_DAYS` (padrão 7)

## Observações
- Edite as coordenadas em `src/utils.py` (EMPRESA_LAT/LNG).
- A distância de 3000m pode ser ajustada em `src/config.py` (MAX_DIST_METERS).
- Endpoints protegidos: envie `Authorization: Bearer <token>`.
