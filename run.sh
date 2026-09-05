#!/usr/bin/env bash
# Release + push + GitHub Release (triggers PyPI publish workflow).
# Usage:
#   ./run.sh              # bump patch (0.1.1 -> 0.1.2), commit, tag, push, release
#   ./run.sh 0.2.0        # set exact version, then same
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f src/pucit/__about__.py ]]; then
  echo "error: run from the pucit repo (missing src/pucit/__about__.py)" >&2
  exit 1
fi

current="$(python -c "import pathlib; t=pathlib.Path('src/pucit/__about__.py').read_text(); import re; print(re.search(r'__version__\s*=\s*\"([^\"]+)\"', t).group(1))")"

if [[ "${1:-}" != "" ]]; then
  next="$1"
else
  # bump patch: x.y.z -> x.y.(z+1)
  next="$(python -c "v='$current'.split('.'); print('.'.join(v[:-1]+[str(int(v[-1])+1)]))")"
fi

echo "==> current: $current"
echo "==> release: $next"

# update version file
python -c "
from pathlib import Path
p = Path('src/pucit/__about__.py')
p.write_text(f'__version__ = \"$next\"\n', encoding='utf-8')
"

git add -A
if git diff --cached --quiet; then
  echo "nothing to commit (working tree clean with version $next already?)"
else
  git commit -m "release: $next"
fi

tag="v$next"
if git rev-parse "$tag" >/dev/null 2>&1; then
  echo "error: tag $tag already exists" >&2
  exit 1
fi

git tag "$tag"
echo "==> pushing main + $tag"
git push origin HEAD
git push origin "$tag"

if command -v gh >/dev/null 2>&1; then
  echo "==> creating GitHub Release $tag (PyPI publish runs from this)"
  if gh release create "$tag" --title "$tag" --generate-notes; then
    echo "==> done. Watch: gh run list --workflow=publish.yml"
    echo "    PyPI: https://pypi.org/project/pucit/$next/"
  else
    echo "warn: gh release failed (login with: gh auth login)" >&2
    echo "      Create release manually for $tag on GitHub to publish to PyPI." >&2
    exit 1
  fi
else
  echo "warn: gh not installed — tag pushed; create a GitHub Release for $tag to publish." >&2
  echo "      https://github.com/mudassir-cpp/pucit/releases/new?tag=$tag" >&2
fi
