#!/usr/bin/env bash
set -euo pipefail

# Local ZMK build helper that mirrors the upstream build-user-config workflow.
# Requirements on the host: docker. Everything else happens inside the
# zmkfirmware/zmk-build-arm:stable container.

BUILD_MATRIX_PATH=${BUILD_MATRIX_PATH:-build.yaml}
CONFIG_PATH=${CONFIG_PATH:-config}
OUT_DIR=${OUT_DIR:-out}
BASE_DIR=${BASE_DIR:-.west-workdir}
ZMK_IMAGE=${ZMK_IMAGE:-zmkfirmware/zmk-build-arm:stable}

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to run this script" >&2
  exit 1
fi

# Use -it only if running interactively
DOCKER_FLAGS="--rm"
if [ -t 0 ]; then
  DOCKER_FLAGS="--rm -it"
fi

# Run everything inside the official ZMK build container so toolchains match the CI.
docker run $DOCKER_FLAGS \
  -v "${PWD}:/work" \
  -w /work \
  -e BUILD_MATRIX_PATH \
  -e CONFIG_PATH \
  -e OUT_DIR \
  -e BASE_DIR \
  "${ZMK_IMAGE}" \
  bash -s <<'IN_CONTAINER'
set -euo pipefail

BUILD_MATRIX_PATH=${BUILD_MATRIX_PATH:-build.yaml}
CONFIG_PATH=${CONFIG_PATH:-config}
OUT_DIR=${OUT_DIR:-out}
BASE_DIR=${BASE_DIR:-.west-workdir}

# Ensure PyYAML is available for matrix parsing.
python3 - <<'PY'
import subprocess, sys
try:
    import yaml  # type: ignore
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
PY

# Parse build.yaml into a JSON matrix we can iterate over.
MATRIX_JSON=$(python3 - <<'PY'
import json, sys, yaml  # type: ignore
from pathlib import Path
path = Path("${BUILD_MATRIX_PATH}")
data = yaml.safe_load(path.read_text()) or {}
entries = []
for inc in data.get("include", []):
    board = inc.get("board")
    if not board:
        continue
    shield = inc.get("shield", "")
    cmake = inc.get("cmake-args", "")
    artifact = inc.get("artifact-name")
    if not artifact:
        artifact = f"{shield + '-' if shield else ''}{board.replace('/', '_')}-zmk"
    entries.append({
        "board": board,
        "shield": shield,
        "cmake": cmake,
        "artifact": artifact,
    })
print(json.dumps(entries))
PY)

echo "Build matrix: ${MATRIX_JSON}"

# Prepare west workspace (kept in ${BASE_DIR}).
if [ ! -d "${BASE_DIR}" ]; then
  west init -l "${CONFIG_PATH}" "${BASE_DIR}"
fi

west update --fetch-opt=--filter=tree:0
west zephyr-export

# Build each entry.
echo "Using ZMK_CONFIG=/work/${CONFIG_PATH}"
mkdir -p "${OUT_DIR}"

# shellcheck disable=SC2034
for row in $(python3 - <<'PY'
import json
import shlex
import sys
rows = json.loads("""${MATRIX_JSON}""")
for r in rows:
    parts = []
    for k in ["board", "shield", "cmake", "artifact"]:
        v = r.get(k, "")
        parts.append(shlex.quote(v))
    print("|".join(parts))
PY); do
  IFS='|' read -r BOARD SHIELD CMAKE_ARGS ARTIFACT <<<"${row}"
  BUILD_DIR="${OUT_DIR}/${ARTIFACT}"
  EXTRA_CMAKE="${SHIELD:+-DSHIELD=\"${SHIELD}\"}"
  echo "\n=== Building ${ARTIFACT} (board=${BOARD} shield=${SHIELD}) ==="
  west build -s zmk/app -d "${BUILD_DIR}" -b "${BOARD}" -- \
    -DZMK_CONFIG="/work/${CONFIG_PATH}" ${EXTRA_CMAKE} ${CMAKE_ARGS}
  if [ -f "${BUILD_DIR}/zephyr/zmk.uf2" ]; then
    cp "${BUILD_DIR}/zephyr/zmk.uf2" "${BUILD_DIR}/${ARTIFACT}.uf2"
  elif [ -f "${BUILD_DIR}/zephyr/zmk.bin" ]; then
    cp "${BUILD_DIR}/zephyr/zmk.bin" "${BUILD_DIR}/${ARTIFACT}.bin"
  fi
  echo "Artifacts stored under ${BUILD_DIR}"
done
IN_CONTAINER
