# Security Policy

## Do not commit secrets

This repository must never contain:
- `XHS_COOKIE`
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- Any `secrets/` folder or config files containing tokens
- Captured media (videos/images) or raw exports that may contain personal data

## Recommended setup

- Use environment variables for secrets.
- Use `.env` locally if you prefer, but keep it out of git.

## Reporting

If you discover a security issue, please open a GitHub issue with minimal sensitive detail.
