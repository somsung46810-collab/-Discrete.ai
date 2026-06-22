# Native Continuous Deployment

Discrete Art Studio uses a direct Python deployment model. GitHub Actions builds the CyGlobsGL Python application and deploys it to a Linux host over SSH.

## Workflow behavior

### Continuous integration

`.github/workflows/python-ci.yml` runs repository checks, CyGlobsGL generation tests, media diagnostics, package builds, and production packaging on pushes and pull requests to `main`.

### Automatic staging

After a successful `Python CI` run on `main`, `.github/workflows/deploy.yml`:

1. Checks out the exact successful commit.
2. Runs checkups, linting, tests, and package builds.
3. Creates a versioned deployment archive and SHA-256 manifest.
4. Uploads the release artifact.
5. Deploys through the protected `staging` environment.
6. Writes application secrets to the remote shared configuration.
7. Runs versioned SQLite migrations.
8. Installs the release in an isolated virtual environment.
9. Switches the `current` symlink.
10. Restarts `discrete-ai-staging.service`.
11. Checks `/api/health`.
12. Restores the previous release when the health check fails.

### Production promotion

Production deployment occurs by manually selecting `production` or by pushing a version tag such as `v0.5.0`. A successful tagged deployment publishes a GitHub Release.

## GitHub environments

Create:

- `staging`
- `production`

Configure required reviewers on `production`.

Each environment should define these secrets:

| Secret | Purpose |
|---|---|
| `DEPLOY_HOST` | Remote Linux host name or IP address |
| `DEPLOY_USER` | SSH deployment account |
| `DEPLOY_SSH_KEY` | Private Ed25519 deployment key |
| `DEPLOY_SSH_PORT` | SSH port; defaults to 22 |
| `DISCRETE_SECRET_KEY` | HMAC signing secret |
| `DISCRETE_STRIPE_SECRET_KEY` | Optional checkout secret |

Each environment should define these variables:

| Variable | Example |
|---|---|
| `DEPLOY_ROOT` | `/home/discrete/apps/staging` or `/home/discrete/apps/production` |
| `DEPLOY_PUBLIC_URL` | Public environment URL |
| `DISCRETE_PORT` | `8001` for staging and `8000` for production |

No image-provider secrets, provider endpoints, model identifiers, or outbound generation credentials are required.

## Remote host prerequisites

The deployment user needs:

- Linux with Python 3.11 or newer
- `bash`, `tar`, `curl`, and OpenSSH
- user-level systemd support
- permission to write under `DEPLOY_ROOT`
- lingering enabled when the service must continue after logout

```bash
loginctl enable-linger DEPLOY_USER
```

## Remote release layout

```text
DEPLOY_ROOT/
├── current -> releases/current-release
├── previous -> releases/previous-release
├── incoming/
├── releases/
└── shared/
    ├── .env
    ├── discrete_art_studio.db
    └── storage/
```

The database, generated CyGlobsGL SVG files, and environment file survive release changes because they remain under `shared/`.

## Database migrations and rollback

`scripts/migrate.py` records applied versions in `schema_migrations`. Deployment stops before promotion when migration execution fails. When `/api/health` fails after promotion, the remote script restores the previous release and restarts the service.

## Version promotion

1. Update the version in `pyproject.toml`.
2. Merge and confirm staging.
3. Create and push an annotated tag:

```bash
git tag -a v0.5.0 -m "Discrete Art Studio CyGlobsGL v0.5.0"
git push origin v0.5.0
```

The protected `production` environment can require approval before deployment proceeds.
