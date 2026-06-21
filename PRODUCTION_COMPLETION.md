# Production Completion Runbook

This runbook completes the production-readiness steps for the CyGlobsGL-only Discrete Art Studio runtime.

## 1. Confirm CI execution

Opening the CyGlobsGL migration pull request triggers `Python CI`. The workflow runs the repository checkup before tests and package creation.

## 2. Run repository checkup, tests, and build

```bash
python scripts/check_all.py
ruff check ai_generation.py cyglobsgl_generation.py cyglobs_app.py graphics_runtime.py cyglobs_framework scripts tests
pytest --cov=cyglobsgl_generation --cov=cyglobs_app --cov=cyglobs_framework --cov=graphics_runtime
python -m build
python scripts/build_production_package.py
```

## 3. Configure deployment environments

Create `staging` and `production` and populate the host, SSH, signing, port, root, and public URL values documented in `DEPLOYMENT.md`. No image-provider credential is required.

Production should require at least one reviewer who is not the deployment initiator.

## 4. Verify staging

After staging deploys, run **Actions → Verify Deployment** with `staging`.

```bash
python scripts/production_smoke_test.py https://staging.example.com
```

Verify that the health response reports CyGlobsGL and that generated artwork is stored as local SVG output.

## 5. Verify DUPE and rollback

Run **Actions → DUPE Deployment** against staging with a known-good source release and a new target release. Confirm the service passes its health check. A deliberately broken staging release should restore the `previous` symlink automatically.

## 6. Harden production operations

The repository includes:

- all-file secret and syntax scanning
- explicit workflow permissions
- protected production-environment integration
- release identifier validation
- SQLite migrations
- SQLite online backup and integrity checking
- local CyGlobsGL SVG generation
- health verification
- automatic rollback
- immutable DUPE releases

Schedule backups on the host:

```bash
0 2 * * * /path/current/scripts/backup_database.sh /path/shared/discrete_art_studio.db /path/shared/backups 14
```

Centralized metrics, alert routing, verified payment webhooks, account recovery, and an external security review remain operational follow-ups.

## 7. Promote a release

After staging and DUPE verification pass:

```bash
git tag -a v0.5.0 -m "Discrete Art Studio CyGlobsGL v0.5.0"
git push origin v0.5.0
```

Approve the production environment gate, then run **Verify Deployment** with `production`.

## Completion boundary

Repository automation is complete when the migration pull request passes CI and merges. Live deployment completion additionally requires GitHub environment configuration, an accessible Linux host, deployment credentials, and a successful approved workflow run.
