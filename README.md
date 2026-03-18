# BOOKFLIX MVP Core

MVP de streaming inteligente para EPUB -> áudio sob demanda.

## Stack

- Backend: FastAPI + SQLite + Redis + edge-tts (fallback Piper)
- Frontend: PWA Vanilla JS + HTML5 audio

## Estrutura

- backend/app/main.py: API principal
- backend/app/api/routes/books.py: upload e metadados EPUB
- backend/app/api/routes/audio.py: manifesto de capítulo e stream por chunk
- backend/app/api/routes/progress.py: progresso e bookmarks
- frontend/index.html: app web

## Requisitos

- Python 3.11+
- Redis local (opcional, mas recomendado)

## Backend

1. Criar e ativar ambiente virtual.
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Configurar ambiente:

```bash
copy .env.example .env
```

4. Subir API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Executar dentro de `backend`.

## Frontend

No diretório `frontend`, sirva os arquivos estáticos com qualquer servidor local.

Exemplo com Python:

```bash
python -m http.server 5500
```

Acesse:
- Frontend: http://localhost:5500
- API: http://localhost:8000

## Fluxo do MVP

1. Fazer upload de EPUB no painel.
2. Selecionar livro na biblioteca.
3. Escolher capítulo e clicar Play.
4. O backend gera áudio de cada chunk sob demanda.
5. Progresso e bookmarks são salvos por session_id local.

## Endpoints principais

- POST /api/v1/books/upload
- GET /api/v1/books
- GET /api/v1/books/{book_id}
- GET /api/v1/audio/{book_id}/chapter/{chapter_index}/manifest
- GET /api/v1/audio/{book_id}/chapter/{chapter_index}/chunk/{chunk_index}
- POST /api/v1/progress
- GET /api/v1/progress/{session_id}/{book_id}
- POST /api/v1/bookmarks
- GET /api/v1/bookmarks/{session_id}/{book_id}

## Observações

- A voz escolhida no frontend fica salva localmente no browser. Nesta etapa, a troca de voz em runtime nao envia override por requisição (próxima iteração).
- Fallback Piper requer configuração de `BOOKFLIX_PIPER_BIN` e `BOOKFLIX_PIPER_MODEL`.
