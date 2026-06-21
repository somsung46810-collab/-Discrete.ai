# Production Completion Runbook

This runbook completes the seven production-readiness steps that can be automated in the repository and identifies the infrastructure inputs required for live execution.

## 1. Confirm CI execution

Opening the production-readiness pull request triggers `Python CI` on the branch. The workflow runs the all-file checkup before tests and package creation.

## 2. Run repository checkup, tests, and build

CI executes:

```bash
python scripts/check_all.py
ruff check ai_generation.py cyglobs_app.py graphics_runtime.py cyglobs_framework scripts tests
pytest --cov=ai_generation --cov=cyglobs_app --cov=cyglobs_framework --cov=graphics_runtime
python -m build
python scripts/build_production_package.py
```

## 3. Configure deployment environments

GitHub environment administration requires repository-owner settings and real secret values. Create `staging` and `production` and populate the values documented in `DEPLOYMENT.md`.

Production should require at least one reviewer who is not the deployment initiator.

## 4. Verify staging

After staging deploys, run **Actions → Verify Deployment** with `staging`. It verifies `/api/health`, `/api/features`, and CyGlobsGL runtime reporting.

Equivalent local command:

```bash
python scripts/production_smoke_test.py https://staging.example.com
```

## 5. Verify DUPE and rollback

Run **Actions → DUPE Deployment** against staging with a known-good source release and a new target release. Confirm the service passes its health check. A deliberately broken staging release should restore the `previous` symlink automatically.

## 6. Harden production operations

The repository now includes:

- all-file secret and syntax scanning
- explicit workflow permissions
- protected production-environment integration
- release identifier validation
- SQLite migrations
- SQLite online backup and integrity checking
- health verification
- automatic rollback
- immutable DUPE releases

Schedule backups on the host, for example:

```bash
0 2 * * * /path/current/scripts/backup_database.sh /path/shared/discrete_art_studio.db /path/shared/backups 14
```

Centralized metrics, alert routing, verified payment webhooks, account recovery, and an external security review remain operational follow-ups.

## 7. Promote a release

After staging and DUPE verification pass:

```bash
git tag -a v0.4.1 -m "Discrete Art Studio v0.4.1"
git push origin v0.4.1
```

The production environment approval gate must be approved before deployment. Run **Verify Deployment** with `production` after promotion.

## Completion boundary

Repository automation is complete when this pull request passes CI and merges. Live deployment completion additionally requires real GitHub environment configuration, an accessible Linux host, deployment credentials, provider credentials, and a successful approved workflow run.
