#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 2.1.87"
  exit 1
fi

VERSION="$1"
TAG="v${VERSION}"

# Update package.json version
cd "$(dirname "$0")/.."
bun x json -f package.json -e "this.version='${VERSION}'" -i

# Commit and tag
git add package.json
git commit -m "release ${TAG}" || true
git tag -a "${TAG}" -m "Release ${TAG}"

echo "Created tag ${TAG}. Pushing..."
git push origin HEAD "${TAG}"
