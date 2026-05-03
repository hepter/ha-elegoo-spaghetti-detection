# HACS Publishing Checklist

This repository is a HACS `integration` because it installs a Home Assistant
custom integration under `custom_components/elegoo_spaghetti_detection`.
It is not a HACS `plugin`/Dashboard item. Dashboard plugins are JavaScript
frontend assets, usually installed from `dist/`.

## Current HACS Requirements

For a custom integration repository:

- The repository must be public and hosted on GitHub.
- The repository must have a clear GitHub description.
- The repository must have GitHub topics.
- GitHub issues must be enabled.
- The repository must have a README that explains how to use the integration.
- `hacs.json` must exist in the repository root and contain at least `name`.
- There must be only one integration directory under `custom_components/`.
- All files required for the integration itself must be inside
  `custom_components/elegoo_spaghetti_detection/`.
- The integration `manifest.json` must define at least:
  - `domain`
  - `documentation`
  - `issue_tracker`
  - `codeowners`
  - `name`
  - `version`
- The integration must provide brand assets. This repo includes:
  - `custom_components/elegoo_spaghetti_detection/brand/icon.png`
  - `custom_components/elegoo_spaghetti_detection/brand/logo.png`
- If submitted as a default HACS repository, these GitHub Actions must pass:
  - HACS Action with `category: integration`
  - Hassfest
- A full GitHub release is required before submitting to `hacs/default`. A tag
  alone is not enough.

## Default Store Submission

To request inclusion in the default HACS store:

1. Confirm the repository can be added manually as a HACS custom repository.
2. Confirm HACS Action passes without errors or ignored checks.
3. Confirm Hassfest passes.
4. Create a full GitHub release, for example `v1.0.0`.
5. Fork `hacs/default`.
6. Add `hepter/ha-elegoo-spaghetti-detection` alphabetically to the
   `integration` file.
7. Open a PR from a branch in the fork. Do not submit the PR from an
   organization account, because the PR must be editable.

HACS default repository reviews can take months. Until it is accepted, users can
install this repo through HACS as a custom repository.

## Repository Metadata To Set On GitHub

These were set on GitHub on 2026-05-01. Verify them before opening a HACS
default PR:

- Description:
  - `Elegoo FDM printer spaghetti detection for Home Assistant with a local Obico ML server`
- Topics:
  - `home-assistant`
  - `hacs`
  - `hacs-integration`
  - `custom-integration`
  - `elegoo`
  - `fdm`
  - `3d-printer`
  - `spaghetti-detection`
  - `obico`
- Issues:
  - Enabled

## Workflows In This Repo

- `.github/workflows/validate.yaml`
  - Runs `hacs/action@main` with `category: integration`.
- `.github/workflows/hassfest.yaml`
  - Runs `home-assistant/actions/hassfest@master`.
- `.github/workflows/ci.yaml`
  - Runs basic JSON, Python syntax, and YAML validation.
- `.github/dependabot.yml`
  - Keeps GitHub Actions versions current.

## Release Notes

For the first HACS-ready release:

- Use a SemVer tag such as `v1.0.0`.
- Ensure `custom_components/elegoo_spaghetti_detection/manifest.json`
  contains the matching version without the leading `v`, for example `1.0.0`.
- Publish a full GitHub release after workflows pass.

## References

- HACS publish general requirements:
  - https://hacs.xyz/docs/publish/start/
- HACS integration requirements:
  - https://hacs.xyz/docs/publish/integration/
- HACS default repository inclusion:
  - https://hacs.xyz/docs/publish/include/
- HACS validation action:
  - https://hacs.xyz/docs/publish/action/
- Home Assistant integration manifest:
  - https://developers.home-assistant.io/docs/creating_integration_manifest/
- Local custom integration brand assets:
  - https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api
