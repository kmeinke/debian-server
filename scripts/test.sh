#!/usr/bin/env bash
set -euo pipefail

CONTAINER="server-salt"

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build   Remove container and rebuild image"
    echo "  shell     Start container with systemd, open shell"
    echo "  test    Start container with systemd, run highstate"
    echo "  clean   Remove container and image"
    echo ""
}

ensure_running() {
    if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
        docker compose up -d --build
        echo "Waiting for systemd to boot..."
        sleep 3
    fi
}

CMD="${1:-test}"

case "$CMD" in
    build)
        docker compose down
        docker compose build
        ;;
    shell)
        ensure_running
        docker exec -it "$CONTAINER" bash
        ;;
    test)
        ensure_running
        docker exec "$CONTAINER" salt-call --local state.highstate
        ;;
    clean)
        docker compose down --rmi all --volumes
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        echo "Unknown command: $CMD"
        usage
        exit 1
        ;;
esac
