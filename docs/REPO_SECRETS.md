# Repository secrets and where to add them

This project can use a few repository secrets for CI, publishing, and integrations. Add these via GitHub → Settings → Secrets and variables → Actions.

Recommended secrets

- `PYPI_API_TOKEN` — Personal Access Token for publishing to PyPI (use the API token created on pypi.org). Scope: repository. Used by the `publish.yml` workflow to upload distributions.
- `CODECOV_TOKEN` — (optional) token for uploading coverage reports to Codecov.
- `SLACK_WEBHOOK` — (optional) incoming webhook for notifying a Slack channel about releases or CI failures.
- `DATASTORE_API_KEY` — (optional) key for any external datastore or artifact storage you may use.

How to add a secret (web UI)

1. Open the repository on GitHub.
2. Go to Settings → Secrets and variables → Actions.
3. Click "New repository secret".
4. Enter the name (e.g., `PYPI_API_TOKEN`) and paste the secret value.
5. Save.

How to add a secret (gh CLI)

If you have the `gh` CLI installed and authenticated, you can add a secret via:

```bash
gh secret set PYPI_API_TOKEN --body "$(cat ~/pypi_token.txt)" --repo sosahinolcay-tech/quant-trading
```

Notes

- Keep secrets in GitHub Secrets — do not hard-code tokens in files.
- If you use multiple environments (e.g., staging/production), prefer environment-scoped or organization secrets.
