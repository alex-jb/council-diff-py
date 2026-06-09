# Security Policy

## What council-diff-py handles

- Your `ANTHROPIC_API_KEY` (read from env or constructor arg)
- The decision text you pass in
- The voice verdicts Claude returns

## What council-diff-py does NOT do

- Persist any data anywhere by default (Brier audit module is purely in-memory until you persist)
- Send telemetry or analytics
- Log anything outside what you explicitly print

## Reporting a vulnerability

If you find a security issue, please **do not open a public GitHub issue**.

Email: **xji1@mail.yu.edu**

Include reproduction + severity assessment + your preferred disclosure timeline.

I'll respond within 72 hours.

## Dependency audit

`anthropic` is the only runtime dependency. Audit it however you'd audit any other LLM client.

## API key hygiene

- Never commit a real `ANTHROPIC_API_KEY`
- Use `python-dotenv` + `.env` + `.gitignore`
- Rotate keys if they leak

## Prompt injection

User-provided `decision` and `context` flow into the model. Treat any output as potentially adversarial — don't pass voice verdicts to `eval()`, don't execute them as code, and don't use them to drive automated actions without HITL review.
