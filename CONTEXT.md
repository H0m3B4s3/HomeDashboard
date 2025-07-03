# HomeBase Project Context

## Python Version
- Always use `python3` for all commands, scripts, and server runs.
- Do not use `python` (may point to Python 2 or system Python).

## WatchFiles Warnings
- When running the dev server with `--reload`, you may see warnings like:
  > WARNING:  WatchFiles detected changes in 'venv/lib/python3.9/site-packages/pydantic/...'
- These are **normal** if your `venv` is inside the project directory.
- **You can safely ignore these warnings.**
- To avoid them, move your `venv` outside the project directory or configure WatchFiles to ignore `venv`. 