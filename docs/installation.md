# Installation

## HACS Custom Repository

This repository is a HACS `integration`. It is not a dashboard card or Lovelace
plugin.

Until it is accepted into the default HACS store, add it manually:

1. Open Home Assistant.
2. Open `HACS`.
3. Open the three-dot menu.
4. Choose `Custom repositories`.
5. Repository:

   ```text
   https://github.com/hepter/ha-elegoo-spaghetti-detection
   ```

6. Category: `Integration`.
7. Install `Elegoo Spaghetti Detection`.
8. Restart Home Assistant.

## Manual Install

Copy:

```text
custom_components/elegoo_spaghetti_detection
```

to:

```text
/config/custom_components/elegoo_spaghetti_detection
```

Restart Home Assistant.

## ML Server

The integration needs the local ML server before setup can complete. See
[ML server and logs](ml-server.md).
