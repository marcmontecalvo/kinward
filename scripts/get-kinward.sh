#!/usr/bin/env bash
# Kinward one-line installer entry point.
#
#   curl -fsSL https://raw.githubusercontent.com/marcmontecalvo/kinward/main/scripts/get-kinward.sh | bash
#
# Installs Docker (via Docker's own get-docker.sh convenience script) if it is
# missing, clones this repository, then hands off to the interactive setup
# wizard at scripts/kinward-setup.sh. Safe to re-run: it updates an existing
# checkout instead of re-cloning.
#
# Environment overrides:
#   KINWARD_REPO_URL     - defaults to the public Kinward repository
#   KINWARD_REPO_REF     - branch/tag to check out (default: main)
#   KINWARD_INSTALL_DIR  - checkout location (default: $HOME/kinward)
set -Eeuo pipefail

readonly REPO_URL="${KINWARD_REPO_URL:-https://github.com/marcmontecalvo/kinward.git}"
readonly REPO_REF="${KINWARD_REPO_REF:-main}"
readonly INSTALL_DIR="${KINWARD_INSTALL_DIR:-${HOME}/kinward}"

log()  { printf '==> %s\n' "$*"; }
fail() { printf '\033[31mkinward install: FAIL: %s\033[0m\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Linux|Darwin) ;;
  *) fail "unsupported OS: $(uname -s). Run this on Linux or macOS." ;;
esac

sudo_cmd() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    fail "this step needs root privileges and 'sudo' is not available. Re-run as root, or install: $*"
  fi
}

install_with_package_manager() {
  local package="$1"
  if command -v apt-get >/dev/null 2>&1; then
    sudo_cmd apt-get update -y && sudo_cmd apt-get install -y "${package}"
  elif command -v dnf >/dev/null 2>&1; then
    sudo_cmd dnf install -y "${package}"
  elif command -v yum >/dev/null 2>&1; then
    sudo_cmd yum install -y "${package}"
  elif command -v pacman >/dev/null 2>&1; then
    sudo_cmd pacman -Sy --noconfirm "${package}"
  elif command -v brew >/dev/null 2>&1; then
    brew install "${package}"
  else
    return 1
  fi
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker is already installed."
  else
    log "Docker was not found. Installing it with Docker's official convenience script..."
    local tmp_script
    tmp_script="$(mktemp)"
    curl -fsSL https://get.docker.com -o "${tmp_script}"
    sudo_cmd sh "${tmp_script}"
    rm -f "${tmp_script}"
    command -v docker >/dev/null 2>&1 || fail "Docker installation did not complete. Install Docker manually and re-run this script."
  fi

  if ! docker info >/dev/null 2>&1; then
    if [[ "$(id -u)" -ne 0 ]] && command -v sudo >/dev/null 2>&1 && ! groups "$(whoami)" 2>/dev/null | grep -qw docker; then
      log "Adding $(whoami) to the 'docker' group so it can talk to the daemon without sudo..."
      sudo_cmd usermod -aG docker "$(whoami)"
      fail "Log out and back in (or run 'newgrp docker'), then re-run this script to pick up the new group membership."
    fi
    fail "the Docker daemon is unreachable. Is it running?"
  fi
}

ensure_command() {
  local cmd="$1" package="${2:-$1}"
  command -v "${cmd}" >/dev/null 2>&1 && return 0
  log "Installing ${package}..."
  install_with_package_manager "${package}" || fail "'${cmd}' is required but could not be installed automatically. Install it manually and re-run this script."
}

install_docker
ensure_command git
ensure_command curl
# whiptail gives the setup wizard a checklist UI; it degrades to plain prompts
# without it, so a failure here is not fatal.
command -v whiptail >/dev/null 2>&1 || install_with_package_manager whiptail || true

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  log "Found an existing checkout at ${INSTALL_DIR}; updating ${REPO_REF}..."
  git -C "${INSTALL_DIR}" fetch --quiet origin "${REPO_REF}"
  git -C "${INSTALL_DIR}" checkout --quiet "${REPO_REF}"
  git -C "${INSTALL_DIR}" pull --quiet --ff-only origin "${REPO_REF}"
else
  log "Cloning Kinward into ${INSTALL_DIR}..."
  git clone --branch "${REPO_REF}" --depth 1 --quiet "${REPO_URL}" "${INSTALL_DIR}"
fi

log "Handing off to the setup wizard..."
exec bash "${INSTALL_DIR}/scripts/kinward-setup.sh" "$@"
