# Contributing

Thanks for helping! Issues and pull requests are welcome, especially:
- new job sources (`jobsearch/sources/`, see [docs/sources.md](docs/sources.md));
- built-in patterns for more countries (`jobsearch/textutil.py → COUNTRIES`);
- fixes to the filters, with a test showing the advert text that went wrong.

## Before you open a pull request

1. Run the tests: `python -m pytest` (from the project's `.venv`). They use their own settings in
   `tests/fixtures/`, so your personal config does not affect them.
2. Add or update a test for any behaviour change, and keep `docs/` in step.
3. **Check `git status` for personal data.** Your `config/settings.json`, `config/profile.md`,
   `config/companies.json`, `config/secrets.json`, `cvs/`, `data/` and `output/` are git-ignored;
   make sure none of their contents slipped into tracked files (code, docs, tests or the
   `*.example` templates).

## Ground rules for sources

- Public endpoints only: no logins, no applying, no CAPTCHA or bot-protection workarounds.
- Be polite: pause between requests and back off on HTTP 429. Call `ctx.wanted()` before any
  per-job request so already-seen jobs cost nothing.

Style: small modules, plain dicts for jobs, comments only where the reason is not obvious.
