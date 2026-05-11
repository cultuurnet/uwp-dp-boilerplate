#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.local/bin"

# Restore micromamba shell functions for each new terminal session.
if [ -x "$HOME/.local/bin/micromamba" ]; then
  export PATH="$HOME/.local/bin:$PATH"
  export MAMBA_ROOT_PREFIX="$HOME/.micromamba"
  eval "$("$HOME/.local/bin/micromamba" shell hook --shell bash)"
fi
