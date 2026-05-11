#!/usr/bin/env bash
set -euo pipefail

# Make /bin/sh resolve to bash instead of dash so that Java ProcessBuilder
# commands like `sh -c "source venv/bin/activate && ..."` work correctly.
# `source` is a bash builtin; dash (the default sh on Ubuntu) does not have it.
sudo ln -sf bash /bin/sh

mkdir -p "$HOME/.local/bin"

# Install micromamba (platform-aware for both local macOS and Linux containers).
os="$(uname -s)"
arch="$(uname -m)"
case "$os" in
  Linux)
    case "$arch" in
      x86_64) platform="linux-64" ;;
      aarch64|arm64) platform="linux-aarch64" ;;
      *)
        echo "Unsupported Linux architecture: $arch" >&2
        exit 1
        ;;
    esac
    ;;
  Darwin)
    case "$arch" in
      arm64|aarch64) platform="osx-arm64" ;;
      x86_64) platform="osx-64" ;;
      *)
        echo "Unsupported macOS architecture: $arch" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    echo "Unsupported operating system: $os" >&2
    exit 1
    ;;
esac

curl -Ls "https://micro.mamba.pm/api/micromamba/${platform}/latest" | tar -xvj -C "$HOME/.local" bin/micromamba
export PATH="$HOME/.local/bin:$PATH"

# Initialize shell support and create the dataproduct environment.
export MAMBA_ROOT_PREFIX="$HOME/.micromamba"
"$HOME/.local/bin/micromamba" shell init -s bash -r "$HOME/.micromamba" -y || true
eval "$("$HOME/.local/bin/micromamba" shell hook --shell bash)"
micromamba create -n dataproduct -c defaults python=3.11 -y

# Install the Data Product CLI.
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
wget -O "$tmp_dir/cli.zip" "https://repository.uitwisselingsplatform.be/service/rest/v1/search/assets/download?repository=ddt-public-releases&group=be.ddtplatform&name=data-product-cli&sort=version&prerelease=false&maven.extension=zip"
unzip -q "$tmp_dir/cli.zip" -d "$tmp_dir"
bash "$tmp_dir/dp-cli-installer/installer-mac-linux.sh"

# Prepare Fuseki storage path expected by dp cli workflows.
mkdir -p "$HOME/.ddt/dp/data/fuseki"
chmod 777 -R "$HOME/.ddt/dp/data/fuseki"

# Prepare ClickHouse storage path expected by dp cli workflows.
mkdir -p "$HOME/.ddt/dp/data/clickhouse"
chmod 777 -R "$HOME/.ddt/dp/data/clickhouse"
