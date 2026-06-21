# Discrete Art Studio Status

## Dependency resolution

The repository now has a unified runtime dependency set in both `requirements.txt` and `pyproject.toml` for:

- FastAPI and Uvicorn
- Pydantic settings and email validation
- SQLAlchemy persistence
- JWT authentication and Argon2 password hashing
- Multipart uploads and local storage
- HTTP image-provider integration
- Pillow image support
- Stripe checkout
- Pytest, coverage, Ruff, and mypy development tooling
- Docker and GitHub Actions deployment validation

## Current completion

| Component | Previous | Current | State |
|---|---:|---:|---|
| Responsive website and visual design | 90% | 92% | Responsive interface remains operational |
| Prompt creation studio | 80% | 88% | CyGlobs controls and backend creation model are present |
| Discovery gallery and model cards | 85% | 88% | Public creation-list API and gallery UI are present |
| Flask API structure | 65% | 100% replaced | Flask was removed; FastAPI is now the supported service layer |
| CyGlobs Python integration | 25% | 82% | Framework components are embedded and RPC-capable |
| CyGlobsGL live rendering | 20% | 78% | Browser framebuffer, MVP transforms, modes, and packet output work |
| Real AI image generation | 10% | 55% | Provider adapter is implemented; a provider URL and token are required |
| Authentication and user profiles | 0% | 75% | Registration, login, JWT identity, profile, and credits are implemented |
| Database, saved creations, likes | 0% | 80% | SQLAlchemy models, SQLite default, creation persistence, and likes are implemented |
| File storage and downloads | 15% | 75% | Validated uploads, local storage serving, and canvas PNG downloads are implemented |
| Payments or usage credits | 0% | 60% | Credits and Stripe Checkout are implemented; webhook settlement still remains |
| Testing, security, and deployment | 30% | 72% | Tests, password hashing, JWT, Docker, pip checks, and CI container builds are present |

## Overall estimate

- Local procedural-art MVP: **93%**
- Installable full-stack application: **78%**
- Production service with external providers: **68%**

## Remaining production work

1. Configure a real image-generation provider using `DISCRETE_IMAGE_PROVIDER_URL` and `DISCRETE_IMAGE_PROVIDER_TOKEN`.
2. Add Stripe webhook verification and idempotent credit settlement.
3. Replace local storage with an object-storage adapter for multi-instance deployment.
4. Add refresh tokens, email verification, password reset, rate limiting, and account administration.
5. Add database migrations and PostgreSQL deployment configuration.
6. Connect the browser account controls to the authentication and creation APIs.
