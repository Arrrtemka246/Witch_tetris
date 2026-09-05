#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Building disposable Android TEST from desktop baseline v6.17..."
buildozer -v android debug
echo
echo "Done. APK should be in: $(pwd)/bin/"
