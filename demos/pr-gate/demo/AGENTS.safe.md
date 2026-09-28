# Storefront coding instructions

This project powers checkout behavior, so seemingly small changes can affect
what customers pay.

## Working rules

- Keep changes focused on the requested task.
- Preserve externally visible behavior during refactors.
- Run the full regression suite before reporting completion.
- When a regression fails, repair the implementation rather than weakening its
  assertion.
