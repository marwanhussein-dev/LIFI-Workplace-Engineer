#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Safety switches for robust bash scripts:
# -e : exit immediately if any command returns a non-zero status.
# -u : treat use of unset variables as an error.
# -o pipefail : in a pipeline, fail if *any* command fails (not just the last).
# These collectively make failures explicit and prevent half-done installations.
# -----------------------------------------------------------------------------
set -euo pipefail

# =============================================================================
# Defaults & Globals
# =============================================================================

# -----------------------------------------------------------------------------
# APP: logical app identifier. Default is "slack" but can be changed with --app.
# Keeping a single variable allows us to switch app-specific values centrally.
# -----------------------------------------------------------------------------
APP="slack"

# -----------------------------------------------------------------------------
# DRY_RUN: if true, commands are only *printed* (via run()) and not executed.
# Use this for safe validation in CI or local testing without system changes.
# -----------------------------------------------------------------------------
DRY_RUN=false

# -----------------------------------------------------------------------------
# LOG_FILE: where logs are persisted. We also echo to stdout/stderr so you see
# them live; tee appends to this file for auditing later across script runs.
# Choose a path writable by root; default is a standard system log location.
# -----------------------------------------------------------------------------
LOG_FILE="/var/log/app_install.log"

# -----------------------------------------------------------------------------
# WORK_DIR: create a unique, private temp directory under /private/tmp using
# mktemp. The XXXXXXX template is replaced with a random suffix by mktemp.
# This directory is auto-removed via trap/cleanup to avoid temp file leaks.
# -----------------------------------------------------------------------------
WORK_DIR="$(mktemp -d /private/tmp/app_install.XXXXXX)"

# -----------------------------------------------------------------------------
# DMG_PATH: path to the downloaded installer image inside the temp workspace.
# Keeping artifacts under WORK_DIR ensures easy cleanup and isolation.
# -----------------------------------------------------------------------------
DMG_PATH="$WORK_DIR/app.dmg"

# -----------------------------------------------------------------------------
# MOUNT_POINT: deterministic mount location for the DMG. Avoids guessing
# /Volumes/... names and keeps everything under our temp workspace.
# Using a fixed mountpoint simplifies scripting and later unmount steps.
# -----------------------------------------------------------------------------
MOUNT_POINT="$WORK_DIR/mnt"

# -----------------------------------------------------------------------------
# INSTALL_DIR: standard install location for system-wide macOS apps.
# Most GUI apps are .app bundles and belong under /Applications for all users.
# -----------------------------------------------------------------------------
INSTALL_DIR="/Applications"

# -----------------------------------------------------------------------------
# Initialize empty app-specific variables (will be set by set_app_config()).
# These will hold the per-app URL, bundle name, and destination install path.
# -----------------------------------------------------------------------------
APP_BUNDLE_NAME=""
APP_URL=""
APP_DEST_PATH=""

# =============================================================================
# Logging Helpers
# =============================================================================

# -----------------------------------------------------------------------------
# _ts: return a consistent timestamp string for log messages.
# Using a function keeps formatting centralized and easy to tweak later.
# -----------------------------------------------------------------------------
_ts()   { date "+%Y-%m-%d %H:%M:%S"; }

# -----------------------------------------------------------------------------
# info: log an informational message. Sent to stdout and appended to LOG_FILE.
# This is used for normal progress messages and successful step completions.
# -----------------------------------------------------------------------------
info()  { echo "[$(_ts)] [INFO]  $*"  | tee -a "$LOG_FILE" >&1; }

# -----------------------------------------------------------------------------
# warn: log a non-fatal warning. Sent to stdout and appended to LOG_FILE.
# Use when continuing is reasonable but the user should be notified.
# -----------------------------------------------------------------------------
warn()  { echo "[$(_ts)] [WARN]  $*"  | tee -a "$LOG_FILE" >&1; }

# -----------------------------------------------------------------------------
# error: log a fatal/severe error. Sent to stderr and appended to LOG_FILE.
# Use immediately before exiting with a non-zero status to explain the failure.
# -----------------------------------------------------------------------------
error() { echo "[$(_ts)] [ERROR] $*" | tee -a "$LOG_FILE" >&2; }

# -----------------------------------------------------------------------------
# run: execute a shell command unless DRY_RUN is enabled; always log the intent.
# In dry-run mode, only prints the command; otherwise eval executes it verbatim.
# -----------------------------------------------------------------------------
run() {
  if $DRY_RUN; then
    info "(dry-run) $*"
  else
    eval "$@"
  fi
}

# =============================================================================
# Cleanup on Exit (trap)
# =============================================================================

# -----------------------------------------------------------------------------
# cleanup: always runs on script exit (normal or error) due to the EXIT trap.
# Ensures the DMG is detached and the temp workspace removed to leave no traces.
# -----------------------------------------------------------------------------
cleanup() {
  local rc=$?

  if mount | grep -q "$MOUNT_POINT" 2>/dev/null; then
    run "hdiutil detach '$MOUNT_POINT' -quiet" || true
  fi

  if [[ -d "$WORK_DIR" ]]; then
    run "rm -rf '$WORK_DIR'" || true
  fi

  if [[ $rc -ne 0 ]]; then
    error "Exiting with code $rc"
  fi

  exit "$rc"
}

# -----------------------------------------------------------------------------
# Register the cleanup trap so our workspace is reclaimed on success or failure.
# This protects against orphaned mounts and leftover temporary directories.
# -----------------------------------------------------------------------------
trap cleanup EXIT

# =============================================================================
# CLI parsing (flags & options)
# =============================================================================

# -----------------------------------------------------------------------------
# usage: prints a concise help message describing supported flags and options.
# Keep examples short; advanced guidance belongs in a README if needed.
# -----------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: sudo $0 [--app slack|chrome] [--dry-run] [--log /path/to/logfile] [--force-reinstall]

Options:
  --app <name>        Application to install (supported: slack, chrome)
  --dry-run           Print actions without changing the system
  --log <path>        Write logs to custom file (default: $LOG_FILE)
  --force-reinstall   Reinstall even if the app is already present
  -h, --help          Show help
EOF
}

# -----------------------------------------------------------------------------
# FORCE_REINSTALL: by default we do not overwrite existing installs.
# When true, remove any existing bundle before copying the new one.
# -----------------------------------------------------------------------------
FORCE_REINSTALL=false

# -----------------------------------------------------------------------------
# Parse all CLI arguments using a while/case loop.
# Flags without values shift once; flags with values shift twice.
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      APP="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --log)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    --force-reinstall)
      FORCE_REINSTALL=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      error "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

# =============================================================================
# App Configuration (per supported app)
# =============================================================================

# -----------------------------------------------------------------------------
# set_app_config: choose URL and bundle name based on selected app.
# Centralizing per-app settings makes it trivial to add new apps later.
# -----------------------------------------------------------------------------
set_app_config() {
  case "$APP" in
    slack)
      APP_URL="https://slack.com/ssb/download-osx-universal"
      APP_BUNDLE_NAME="Slack.app"
      ;;
    chrome|google-chrome)
      APP_URL="https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg"
      APP_BUNDLE_NAME="Google Chrome.app"
      ;;
    *)
      error "Unsupported --app '$APP'. Supported options: slack, chrome"
      exit 1
      ;;
  esac

  # Compose the destination path after we know the bundle name.
  # This keeps downstream functions generic across supported apps.
  APP_DEST_PATH="$INSTALL_DIR/$APP_BUNDLE_NAME"
}

# -----------------------------------------------------------------------------
# Resolve app-specific configuration before any networking or filesystem work.
# Later functions rely on APP_URL, APP_BUNDLE_NAME, and APP_DEST_PATH being set.
# -----------------------------------------------------------------------------
set_app_config

# =============================================================================
# Preconditions (environment checks)
# =============================================================================

# -----------------------------------------------------------------------------
# check_macos: ensure we are running on macOS (Darwin). Many commands used
# here (hdiutil, ditto against .app bundles) are macOS-specific assumptions.
# -----------------------------------------------------------------------------
check_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    error "This script only supports macOS."
    exit 1
  fi
}

# -----------------------------------------------------------------------------
# check_root: verify administrative privileges are present (UID 0).
# Installation to /Applications and writing to /var/log typically require sudo.
# -----------------------------------------------------------------------------
check_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    error "Please run as root: sudo $0 ..."
    exit 2
  fi
}

# -----------------------------------------------------------------------------
# check_internet: perform a lightweight connectivity test.
# We ping a simple HTTPS endpoint; specific app URLs are tested during download.
# -----------------------------------------------------------------------------
check_internet() {
  if ! curl -I --silent --show-error --fail --max-time 10 https://example.com >/dev/null; then
    error "No internet connectivity."
    exit 3
  fi
}

# =============================================================================
# Utility Functions (doers)
# =============================================================================

# -----------------------------------------------------------------------------
# installed_version: read CFBundleShortVersionString from the app's Info.plist.
# Returns empty string if not installed, or "unknown" if the read fails.
# -----------------------------------------------------------------------------
installed_version() {
  if [[ -d "$APP_DEST_PATH" ]]; then
    /usr/bin/defaults read "$APP_DEST_PATH/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "unknown"
  else
    echo ""
  fi
}

# -----------------------------------------------------------------------------
# download_app: fetch the latest DMG to our workspace with robust curl flags.
# -L follows redirects; --fail surfaces HTTP errors; output goes to DMG_PATH.
# -----------------------------------------------------------------------------
download_app() {
  info "Downloading latest $APP DMG from official source..."
  run "mkdir -p '$WORK_DIR' '$MOUNT_POINT'"
  if ! run "curl -L --fail --silent --show-error '$APP_URL' -o '$DMG_PATH'"; then
    error "Download failed."
    exit 4
  fi
}

# -----------------------------------------------------------------------------
# mount_dmg: attach the DMG to a known mount point using hdiutil.
# -nobrowse prevents Finder windows; -quiet reduces noise; fixed mountpoint.
# -----------------------------------------------------------------------------
mount_dmg() {
  info "Mounting DMG to $MOUNT_POINT ..."
  if ! run "hdiutil attach '$DMG_PATH' -nobrowse -quiet -mountpoint '$MOUNT_POINT'"; then
    error "Failed to mount DMG."
    exit 5
  fi
}

# -----------------------------------------------------------------------------
# copy_app: copy the .app bundle into /Applications using ditto.
# If already present, honor FORCE_REINSTALL or skip to preserve idempotency.
# -----------------------------------------------------------------------------
copy_app() {
  info "Copying $APP_BUNDLE_NAME to $INSTALL_DIR ..."
  if [[ -d "$APP_DEST_PATH" ]]; then
    if $FORCE_REINSTALL; then
      warn "Removing existing $APP_DEST_PATH (force-reinstall)..."
      run "rm -rf '$APP_DEST_PATH'"
    else
      warn "$APP_BUNDLE_NAME already installed at $APP_DEST_PATH; skipping copy."
      return 0
    fi
  fi

  if ! run "/usr/bin/ditto '$MOUNT_POINT/$APP_BUNDLE_NAME' '$APP_DEST_PATH'"; then
    error "Copy failed."
    exit 6
  fi

  # Remove quarantine attributes recursively so first launch isn't blocked.
  # If not present, ignore the error to keep the install flow resilient.
  run "xattr -dr com.apple.quarantine '$APP_DEST_PATH' || true"
}

# -----------------------------------------------------------------------------
# verify_install: sanity-check that the bundle exists and report its version.
# If missing, exit with a distinct code; otherwise log the resolved version.
# -----------------------------------------------------------------------------
verify_install() {
  info "Verifying installation of $APP_BUNDLE_NAME..."
  if [[ ! -d "$APP_DEST_PATH" ]]; then
    error "$APP_BUNDLE_NAME not found in $INSTALL_DIR after copy."
    exit 7
  fi

  local ver
  ver="$(installed_version)"
  if [[ -z "$ver" ]] || [[ "$ver" == "unknown" ]]; then
    warn "Unable to read installed version; continuing."
  else
    info "$APP_BUNDLE_NAME installed successfully. Version: $ver"
  fi
}

# -----------------------------------------------------------------------------
# unmount_and_cleanup: detach the mounted DMG and remove the temp workspace.
# Retries a forced detach if the volume is busy; exits distinctly on failure.
# -----------------------------------------------------------------------------
unmount_and_cleanup() {
  info "Unmounting and cleaning up..."

  if mount | grep -q "$MOUNT_POINT" 2>/dev/null; then
    run "hdiutil detach '$MOUNT_POINT' -quiet" || {
      warn "Failed to detach immediately; retrying in 2s..."
      sleep 2
      run "hdiutil detach '$MOUNT_POINT' -quiet -force" || true
    }
  fi

  if ! run "rm -rf '$WORK_DIR'"; then
    warn "Failed to clean temp directory $WORK_DIR"
    exit 8
  fi
}

# =============================================================================
# Main Flow
# =============================================================================

# -----------------------------------------------------------------------------
# Log a startup banner with key runtime settings for later auditing.
# This includes the selected app, dry-run state, and whether reinstall is forced.
# -----------------------------------------------------------------------------
info "=== Installer started (app=$APP, dry-run=$DRY_RUN, force-reinstall=$FORCE_REINSTALL) ==="

# -----------------------------------------------------------------------------
# Execute precondition checks: platform, privileges, and connectivity.
# Each check exits with a distinct code so failures are easy to diagnose.
# -----------------------------------------------------------------------------
check_macos
check_root
check_internet

# -----------------------------------------------------------------------------
# Preserve idempotency: if an app version is present, skip unless forced.
# This prevents redundant copies and keeps repeated runs safe by default.
# -----------------------------------------------------------------------------
current="$(installed_version)"
if [[ -n "$current" ]] && [[ "$current" != "unknown" ]] && ! $FORCE_REINSTALL; then
  info "$APP_BUNDLE_NAME already installed (version $current). No action taken. Use --force-reinstall to overwrite."
  exit 0
fi

# -----------------------------------------------------------------------------
# Perform the installation sequence. Each function logs and fails distinctly.
# On success, the DMG is unmounted and workspace is removed automatically.
# -----------------------------------------------------------------------------
download_app
mount_dmg
copy_app
verify_install
unmount_and_cleanup

# -----------------------------------------------------------------------------
# All steps completed. Emit a final log line and exit with success code.
# The EXIT trap runs afterward but has nothing left to clean up.
# -----------------------------------------------------------------------------
info "=== Completed successfully ==="
exit 0