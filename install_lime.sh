#!/usr/bin/env bash
# lime 0.2.0.1 ships a setup.py that breaks under setuptools >= 70:
#     AttributeError: install_layout
# Its runtime code is fine; only the build step fails. This drops the package
# directory straight into site-packages, which is what pip would have done.
set -euo pipefail

if python3 -c "import lime" 2>/dev/null; then
  echo "lime already importable - nothing to do"; exit 0
fi

echo "trying pip first..."
if pip install "lime==0.2.0.1" 2>/dev/null; then
  echo "pip install succeeded"; exit 0
fi

echo "pip build failed (expected on modern setuptools); installing from sdist..."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
pip download lime==0.2.0.1 --no-deps --no-binary :all: -d "$tmp" >/dev/null
tar xzf "$tmp"/lime-*.tar.gz -C "$tmp"
site=$(python3 -c "import site,sys; print(site.getsitepackages()[0] if hasattr(site,'getsitepackages') else site.getusersitepackages())")
cp -r "$tmp"/lime-0.2.0.1/lime "$site"/
pip install --quiet "scikit-image>=0.12" tqdm
python3 -c "import lime; print('lime installed ->', lime.__file__)"
