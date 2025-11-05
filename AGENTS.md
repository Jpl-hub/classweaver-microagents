# Repository Guidelines

## Project Structure & Module Organization
- Backend lives under `src/`, grouped by responsibility: `config/` (Django settings), `core/` (models/admin), `api/` (DRF views/serializers), `agents/` (planner/rewriter/tutor runtime), `services/` (pipeline, scoring, PPT extraction), and `kb/` (RAG ingest/store/retrieve). Templates and static assets are in `src/templates/` and `src/static/`.
- Frontend SPA resides in `webapp/` with Vite + Vue 3. Key folders: `webapp/src/views/` (pages), `webapp/src/components/`, `webapp/src/services/` (API client), and `webapp/src/assets/` (Tailwind styles). Build artifacts deploy to `webapp/dist/`.
- Tests live in `tests/`, mirroring backend modules. Add new test files alongside related features.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` — install backend dependencies.
- `python manage.py migrate && python manage.py runserver` — apply migrations and start the Django dev server (defaults to `127.0.0.1:8000`).
- `cd webapp && npm install` — install frontend dependencies.
- `npm run dev` (in `webapp/`) — launch Vite dev server with hot module reload.
- `npm run build` — produce production assets, later served by Django.
- `pytest` — run backend test suite (LLM calls mocked).

## Coding Style & Naming Conventions
- Python code follows PEP 8 with 4-space indentation. Prefer descriptive module-level names (`services/pipeline.py`, `agents/runtime.py`). Use type hints and docstrings for complex functions.
- Vue/TypeScript uses 2-space indentation and PascalCase SFC filenames (`HomeView.vue`). Keep composables and utility modules under `webapp/src/services/` or `webapp/src/types/`.
- TailwindCSS is configured via `webapp/tailwind.config.js`; keep custom CSS minimal and scoped within `assets/`.
- Run formatters before committing: `ruff`/`black` (if added) for Python, `npm run lint` (when configured) for frontend.

## Testing Guidelines
- Use `pytest` for backend; name files `test_*.py` and target edge cases (e.g., mocked planner outputs, scoring calculators).
- Frontend tests are not yet scaffolded—add Vitest + Testing Library under `webapp/tests/` with filenames ending `.spec.ts`.
- Ensure new endpoints or services include unit coverage and, where feasible, integration tests using Django’s test client.

## Commit & Pull Request Guidelines
- Follow concise, imperative commit messages (`feat: add prestudy pipeline RAG hooks`). Group related changes; avoid mixing backend/frontend refactors in one commit when possible.
- Pull requests should link relevant issues, describe the problem, outline the solution, and note testing results (`pytest`, `npm run build`). Attach screenshots or GIFs for UI changes.

## Agent & Configuration Tips
- Keep `.env` secrets out of source control. Copy `.env.example` and set `BASE_URL`, `API_KEY`, and FAISS paths before running agents.
- Mock agent responses in tests to avoid real SiliconFlow usage. Ensure fallback logic preserves `model_trace` completeness.
