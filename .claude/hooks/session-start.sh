#!/usr/bin/env bash
# Hook SessionStart (#949): prepara el entorno de tests en las sesiones de
# Claude Code en la nube. En el PC no hace nada: .claude/settings.json está
# versionado y el PC también lo usa.
#
# La lógica vive en scripts/nube/preparar_entorno.sh para poder relanzarla a
# mano cuando el contenedor se recicla. Aquí solo se añade lo que únicamente
# puede hacer un hook: dejar el venv en el PATH de la sesión (CLAUDE_ENV_FILE).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
VENV="${BDDAT_VENV:-$HOME/.venvs/bddat}"

bash "$REPO/scripts/nube/preparar_entorno.sh"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    {
        echo "export VIRTUAL_ENV=\"$VENV\""
        echo "export PATH=\"$VENV/bin:\$PATH\""
        # Cobertura por test (tests/README.md): sin ctrace, los contextos
        # salen incompletos en Python ≥ 3.12. Solo afecta a las pasadas --cov.
        echo "export COVERAGE_CORE=ctrace"
    } >> "$CLAUDE_ENV_FILE"
fi
