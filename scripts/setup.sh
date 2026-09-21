#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

readonly -a RELEASE_ACTIONS=(install-dev install-prod upgrade rollback)

usage() {
  printf 'Usage: %s <install-dev|install-prod|upgrade>\n' "${0##*/}" >&2
  printf '       %s rollback <version>\n' "${0##*/}" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 2
}

contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "${item}" == "${needle}" ]] && return 0
  done
  return 1
}

main() {
  local action="${1:-}"
  local version="${2:-}"

  [[ -n "${action}" ]] || {
    usage
    die "missing action"
  }
  contains "${action}" "${RELEASE_ACTIONS[@]}" || {
    usage
    die "unknown action: ${action}"
  }

  case "${action}" in
    install-dev)
      uv sync
      ;;
    install-prod)
      uv sync --no-dev
      ;;
    upgrade)
      uv sync -U
      ;;
    rollback)
      [[ -n "${version}" ]] || die "rollback requires an explicit version: ${0##*/} rollback <version>"
      git checkout "${version}" -- .
      uv sync
      ;;
  esac
}

main "$@"
