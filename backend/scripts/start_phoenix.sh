#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PHOENIX_VENV="${BACKEND_DIR}/.phoenix-venv"
PYTHON_BIN="${BACKEND_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON_BIN}" ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.11)"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_OK="$("${PYTHON_BIN}" -c 'import sys; print(int((3, 10) <= sys.version_info[:2] < (3, 15)))')"

if [ "${PYTHON_OK}" != "1" ]; then
  echo "Phoenix requires Python >=3.10,<3.15. Found ${PYTHON_VERSION} at ${PYTHON_BIN}."
  echo "Create the backend .venv with Python 3.11, then run this script again."
  exit 1
fi

if [ -x "${PHOENIX_VENV}/bin/python" ]; then
  EXISTING_VERSION="$("${PHOENIX_VENV}/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ "${EXISTING_VERSION}" != "${PYTHON_VERSION}" ]; then
    echo "Recreating Phoenix venv with Python ${PYTHON_VERSION}..."
    rm -rf "${PHOENIX_VENV}"
  fi
fi

if [ ! -x "${PHOENIX_VENV}/bin/python" ]; then
  "${PYTHON_BIN}" -m venv "${PHOENIX_VENV}"
fi

"${PHOENIX_VENV}/bin/python" -m pip install --upgrade pip
"${PHOENIX_VENV}/bin/python" -m pip install "arize-phoenix==15.11.0"

exec "${PHOENIX_VENV}/bin/phoenix" serve
