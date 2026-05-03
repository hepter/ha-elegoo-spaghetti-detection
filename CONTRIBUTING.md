# Contributing

Work locally, keep changes focused, and test in Home Assistant before opening a
pull request.

- Use clear commit messages.
- Do not commit Home Assistant tokens, camera proxy tokens, SSH keys, or local
  deployment notes.
- Keep the integration domain as `elegoo_spaghetti_detection`.
- Validate JSON, YAML, Python syntax, HACS, and Hassfest before opening a pull
  request.

## Local Validation

```bash
python -m json.tool hacs.json > /dev/null
python -m json.tool custom_components/elegoo_spaghetti_detection/manifest.json > /dev/null
python -m compileall custom_components/elegoo_spaghetti_detection addon/rootfs/app
```

The GitHub workflows run the full repository checks.
