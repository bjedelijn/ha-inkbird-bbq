#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/bjedelijn/ha-inkbird-bbq.git"
REPO="/config/ha-inkbird-bbq"
TARGET="/config/custom_components/inkbird_bbq"
COMPONENT_PATH="custom_components/inkbird_bbq"
BACKUP_ROOT="/config/.inkbird_bbq_backups"

AUTO_RESTART=0
REQUESTED_REF=""

usage() {
    cat <<'EOF'
INKBIRD BBQ updater for Home Assistant

Temporary development updater until HACS becomes the normal installation and
update path.

Usage:
  /config/update_inkbird_bbq.sh
  /config/update_inkbird_bbq.sh <tag-or-branch>
  /config/update_inkbird_bbq.sh --yes <tag-or-branch>

Options:
  -y, --yes    Restart Home Assistant automatically after successful validation.
  -h, --help   Show this help.

Without a ref, an interactive menu lists recent release tags and remote branches.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        -y|--yes)
            AUTO_RESTART=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [ -n "$REQUESTED_REF" ]; then
                echo "ERROR: only one tag, branch or commit can be specified."
                exit 1
            fi
            REQUESTED_REF="$1"
            shift
            ;;
    esac
done

echo "========================================"
echo " INKBIRD BBQ for Home Assistant updater"
echo "========================================"

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is not available."
    exit 1
fi

if ! command -v ha >/dev/null 2>&1; then
    echo "ERROR: Home Assistant CLI ('ha') is not available."
    echo "This updater is intended for Home Assistant OS / Supervised."
    exit 1
fi

if [ ! -d "$REPO/.git" ]; then
    echo
    echo "[setup] Local repository not found."
    echo "Cloning $REPO_URL to $REPO ..."
    git clone "$REPO_URL" "$REPO"
fi

cd "$REPO"

echo
echo "[1/8] Fetching branches and release tags..."
git fetch --all --tags --prune

resolve_ref() {
    local requested="$1"

    if git show-ref --verify --quiet "refs/tags/$requested"; then
        printf '%s' "refs/tags/$requested"
        return 0
    fi

    if git show-ref --verify --quiet "refs/remotes/origin/$requested"; then
        printf '%s' "refs/remotes/origin/$requested"
        return 0
    fi

    if git rev-parse --verify --quiet "$requested^{commit}" >/dev/null; then
        printf '%s' "$requested"
        return 0
    fi

    return 1
}

choose_ref() {
    local -a refs labels
    local tag branch_name choice index custom_ref

    refs=()
    labels=()

    while IFS= read -r tag; do
        [ -n "$tag" ] || continue
        refs+=("refs/tags/$tag")
        labels+=("Release tag: $tag")
    done < <(git tag --sort=-version:refname | head -n 10)

    while IFS= read -r branch_name; do
        [ -n "$branch_name" ] || continue
        [ "$branch_name" = "HEAD" ] && continue
        refs+=("refs/remotes/origin/$branch_name")
        labels+=("Branch: $branch_name")
    done < <(
        git for-each-ref             --format='%(refname:strip=3)'             --sort=refname             refs/remotes/origin/
    )

    if [ "${#refs[@]}" -eq 0 ]; then
        echo "ERROR: no tags or remote branches found."
        exit 1
    fi

    echo
    echo "Available versions:"
    index=1
    for tag in "${labels[@]}"; do
        printf "  %2d) %s\n" "$index" "$tag"
        index=$((index + 1))
    done
    printf "  %2d) Enter custom Git ref\n" "$index"
    echo

    while true; do
        read -r -p "Select version [1-$index]: " choice
        case "$choice" in
            ''|*[!0-9]*)
                echo "Enter a number."
                ;;
            *)
                if [ "$choice" -ge 1 ] && [ "$choice" -lt "$index" ]; then
                    SELECTED_REF="${refs[$((choice - 1))]}"
                    return 0
                fi
                if [ "$choice" -eq "$index" ]; then
                    read -r -p "Git tag, branch or commit: " custom_ref
                    if SELECTED_REF="$(resolve_ref "$custom_ref")"; then
                        return 0
                    fi
                    echo "Unknown Git ref: $custom_ref"
                else
                    echo "Invalid selection."
                fi
                ;;
        esac
    done
}

if [ -n "$REQUESTED_REF" ]; then
    if ! SELECTED_REF="$(resolve_ref "$REQUESTED_REF")"; then
        echo "ERROR: unknown tag, branch or commit: $REQUESTED_REF"
        exit 1
    fi
else
    choose_ref
fi

SELECTED_COMMIT="$(git rev-parse "$SELECTED_REF^{commit}")"
SELECTED_SHORT="$(git rev-parse --short "$SELECTED_COMMIT")"
SELECTED_LABEL="$SELECTED_REF"

case "$SELECTED_REF" in
    refs/tags/*) SELECTED_LABEL="${SELECTED_REF#refs/tags/}" ;;
    refs/remotes/origin/*) SELECTED_LABEL="${SELECTED_REF#refs/remotes/origin/}" ;;
esac

echo
echo "[2/8] Selected version:"
echo "Ref    : $SELECTED_LABEL"
echo "Commit : $SELECTED_SHORT"

if ! git cat-file -e "$SELECTED_COMMIT:$COMPONENT_PATH/manifest.json" 2>/dev/null; then
    echo "ERROR: selected ref does not contain $COMPONENT_PATH/manifest.json"
    exit 1
fi

TMP_DIR="$(mktemp -d /tmp/inkbird-bbq-update.XXXXXX)"
BACKUP_DIR=""

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo
echo "[3/8] Exporting selected integration..."
git archive "$SELECTED_COMMIT" "$COMPONENT_PATH" | tar -x -C "$TMP_DIR"
SOURCE="$TMP_DIR/$COMPONENT_PATH"

echo
echo "[4/8] Validating integration package..."

for required in "__init__.py" "manifest.json" "config_flow.py" "const.py"; do
    if [ ! -f "$SOURCE/$required" ]; then
        echo "ERROR: required file missing: $required"
        exit 1
    fi
done

if ! grep -q '"domain"[[:space:]]*:[[:space:]]*"inkbird_bbq"' "$SOURCE/manifest.json"; then
    echo "ERROR: manifest domain is not inkbird_bbq."
    exit 1
fi

if ! grep -q '"version"[[:space:]]*:' "$SOURCE/manifest.json"; then
    echo "ERROR: manifest has no version."
    exit 1
fi

echo "Selected manifest:"
grep -E '"name"|"domain"|"version"' "$SOURCE/manifest.json" || true

echo
echo "[5/8] Creating backup and installing..."

mkdir -p "$BACKUP_ROOT"

if [ -d "$TARGET" ]; then
    BACKUP_DIR="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -a "$TARGET" "$BACKUP_DIR/inkbird_bbq"
    echo "Backup: $BACKUP_DIR/inkbird_bbq"
fi

rm -rf "$TARGET"
mkdir -p "$(dirname "$TARGET")"
cp -a "$SOURCE" "$TARGET"

printf '%s\n' "$SELECTED_COMMIT" > "$TARGET/.installed_revision"
printf '%s\n' "$SELECTED_LABEL" > "$TARGET/.installed_ref"

rollback() {
    echo
    echo "Validation failed. Rolling back..."
    rm -rf "$TARGET"

    if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR/inkbird_bbq" ]; then
        cp -a "$BACKUP_DIR/inkbird_bbq" "$TARGET"
        echo "Previous integration restored."
    else
        echo "No previous installation was available to restore."
    fi
}

echo
echo "[6/8] Running Home Assistant configuration check..."

set +e
ha core check
CHECK_RESULT=$?
set -e

if [ "$CHECK_RESULT" -ne 0 ]; then
    rollback
    echo
    echo "ERROR: Home Assistant configuration check failed."
    echo "Home Assistant has NOT been restarted."
    exit "$CHECK_RESULT"
fi

echo
echo "[7/8] Validation successful."
echo "Installed ref    : $SELECTED_LABEL"
echo "Installed commit : $SELECTED_SHORT"

echo
echo "[8/8] Restart Home Assistant?"

if [ "$AUTO_RESTART" -eq 1 ]; then
    RESTART_ANSWER="y"
else
    read -r -p "Restart Home Assistant now? [y/N]: " RESTART_ANSWER
fi

case "$RESTART_ANSWER" in
    y|Y|yes|YES)
        ha core restart
        echo
        echo "Home Assistant restart requested."
        ;;
    *)
        echo
        echo "Installation complete. Home Assistant was not restarted."
        echo "Restart manually before using the new integration code."
        ;;
esac

echo
echo "Update complete."
