# Publication dashboard

This directory is the sanitized GitHub Pages view of the private content-operation records.

## What is included

- topic names;
- per-platform text/video state;
- publication time when recorded;
- public work URLs when publicly verified;
- evidence notes for pending or blocked states.

## What is intentionally excluded

- local MP4 files and symlinks;
- private vault paths;
- full unpublished copy;
- cookies, tokens, credentials, or browser state.

## Data contract

`data.json` is the generated public projection. The local source of truth remains the Obsidian vault under `~/media/`. A local sync step should export only the public fields needed by this page.

The workflow in `.github/workflows/pages.yml` deploys this directory to GitHub Pages after a push to `main`.
