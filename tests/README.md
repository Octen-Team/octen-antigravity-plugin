# Tests

`test_plugin.py` checks the plugin files offline, against the rules in the Antigravity [Build plugins](https://antigravity.google/docs/build-plugins) guide:

- `plugin.json` validates against the official schema (pinned in `fixtures/plugin.schema.json`) and has every field the Marketplace requires; the version is a stable `MAJOR.MINOR.PATCH` release; the logo is a valid square 8-bit RGB or RGBA PNG of at least 128 px with transparent padding.
- `mcp_config.json` bundles only the hosted Octen server and carries no credentials, so users sign in with OAuth.
- Each skill's frontmatter follows the spec, and the guide and the README list exactly the hosted tools pinned in `fixtures/hosted-tools.json`.
- README links to local files and headings resolve.
- Tracked text files and their names contain no Chinese, Japanese or Korean characters.

```bash
pip install -r tests/requirements.txt
python -m unittest discover -s tests -v
```

`check_drift.py` compares the pinned fixtures with the live schema and the live tool list, and checks the links in the README and the skill. The tool list needs an Octen API key in `OCTEN_API_KEY` (the repository secret of the same name in CI); without it that check is skipped.

```bash
python tests/check_drift.py
```

CI runs the unit tests and `agy plugin validate --strict .` on every pull request, and the drift check every Monday.
