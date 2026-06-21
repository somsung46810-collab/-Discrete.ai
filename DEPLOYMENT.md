# Native Continuous Deployment

Discrete Art Studio deploys without Docker or a Python web framework. GitHub Actions builds a source archive and Python distributions, then deploys the archive to a Linux host over SSH.

## Workflow behavior

### Continuous integration

`.github/workflows/python-ci.yml` runs on pushes and pull requests to `main`.

### Automatic staging

After a successful `Python CI` run on `main`, `.github/workflows/deploy.yml`:

1. Checks out the exact successful commit.
2. Re-runs dependency checks, linting, tests, and package builds.
3. Creates a versioned deployment archive and SHA-256 manifest.
4. Uploads the build as a GitHub Actions artifact.
5. Deploys through the protected `staging` environment.
6. Writes environment-scoped secrets to the remote shared configuration.
7. Runs `scripts/migrate.py` against the shared SQLite database.
8. Installs the release in an isolated virtual environment.
9. Switches the `current` symlink to the new release.
10. Restarts `discrete-ai-staging.service`.
11. Checks `/api/health` up to 20 times.
12. Restores the `previous` symlink and restarts the old release if health checks fail.

### Production promotion

Production deployment occurs in either of these ways:

- Run `Native Deployment` manually and select `production` plus a branch, tag, or commit.
- Push a version tag such as `v0.4.1`.

A successful version-tag deployment publishes a GitHub Release containing the source archive, wheel, source distribution, and checksum manifest.

## GitHub environments

Create two repository environments:

- `staging`
- `production`

Configure required reviewers on `production` to make production deployment an approval gate. Optional staging reviewers may also be configured.

Each environment should define these secrets:

| Secret | Purpose |
|---|---|
| `DEPLOY_HOST` | Remote Linux host name or IP address |
| `DEPLOY_USER` | SSH account used for deployment |
| `DEPLOY_SSH_KEY` | Private Ed25519 deployment key |
| `DEPLOY_SSH_PORT` | SSH port; defaults to 22 when empty |
| `DISCRETE_SECRET_KEY` | HMAC signing secret |
| `OPENAI_API_KEY` | Image provider key when OpenAI mode is used |
| `DISCRETE_IMAGE_PROVIDER_URL` | Optional provider endpoint override |
| `DISCRETE_IMAGE_PROVIDER_TOKEN` | Generic provider token |
| `DISCRETE_STRIPE_SECRET_KEY` | Optional checkout secret |

Each environment should define these variables:

| Variable | Example |
|---|---|
| `DEPLOY_ROOT` | `/home/discrete/apps/staging` or `/home/discrete/apps/production` |
| `DEPLOY_PUBLIC_URL` | Public environment URL |
| `DISCRETE_PORT` | `8001` for staging and `8000` for production |
| `DISCRETE_IMAGE_PROVIDER` | `openai` or `generic` |
| `DISCRETE_IMAGE_MODEL` | `gpt-image-2` or another provider model |

Use different `DEPLOY_ROOT` and `DISCRETE_PORT` values for staging and production, even when both environments share one host.

## Remote host prerequisites

The deployment user needs:

- Linux with Python 3.11 or newer
- `bash`, `tar`, `curl`, and OpenSSH
- user-level systemd support
- permission to write under `DEPLOY_ROOT`
- lingering enabled when the service must continue after logout:

```bash
loginctl enable-linger DEPLOY_USER
```

The deployment account does not require root access when user-level systemd is available.

## Remote release layout

```text
DEPLOY_ROOT/
├── current -> releases/current-release
├── previous -> releases/previous-release
├── incoming/
├── releases/
│   ├── release-1/
│   └── release-2/
└── shared/
    ├── .env
    ├── discrete_art_studio.db
    └── storage/
```

The database, generated images, and environment file survive release changes because they remain under `shared/`.

## Database migrations

`scripts/migrate.py` records applied versions in `schema_migrations`. Deployment stops before the service switch when migration execution fails.

Migrations must be backward-compatible with the previous release so automatic rollback remains safe.

## Rollback

The remote script records the old `current` release as `previous`. When the new service fails `/api/health`, it restores `current` to `previous` and restarts the service.

A manual rollback can use:

```bash
ln -sfn "$(readlink -f PREVIOUS_PATH)" CURRENT_PATH
systemctl --user restart discrete-ai-production.service
```

Replace the paths with the environment's actual `DEPLOY_ROOT/current` and `DEPLOY_ROOT/previous` values.

## Version promotion

Before creating a production version tag:

1. Update the version in `pyproject.toml`.
2. Merge and confirm the staging deployment.
3. Create and push an annotated tag:

```bash
git tag -a v0.4.1 -m "Discrete Art Studio v0.4.1"
git push origin v0.4.1
```

The protected `production` environment can require approval before deployment proceeds.
