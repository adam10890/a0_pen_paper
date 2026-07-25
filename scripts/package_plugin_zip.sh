#!/usr/bin/env bash
# Build an Agent Zero–ready plugin ZIP: a0_pen_paper/plugin.yaml at the archive root folder.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="${ROOT}/dist"
STAGE="${DIST}/stage"
PLUGIN_DIR="${STAGE}/a0_pen_paper"
OUT="${DIST}/a0_pen_paper.zip"

rm -rf "${STAGE}"
mkdir -p "${PLUGIN_DIR}"

rsync -a \
  --exclude '.git' \
  --exclude '.github' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'dist' \
  --exclude 'docs/dev-tracker.html' \
  --exclude '.toggle-*' \
  --exclude 'config.json' \
  --exclude 'usr/' \
  "${ROOT}/" "${PLUGIN_DIR}/"

mkdir -p "${DIST}"
rm -f "${OUT}"
(cd "${STAGE}" && zip -r "${OUT}" a0_pen_paper)

echo "Created ${OUT}"
