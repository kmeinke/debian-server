#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  highstate    Full highstate dry-run (default)"
    echo "  apply        Full highstate for real (installs packages, writes files)"
    echo "  test STATE   Dry-run a single state (e.g. security.firewall)"
    echo "  pillar       Show rendered pillar data"
    echo "  shell        Drop into the container for debugging"
    echo "  build        Build the Docker image only"
    echo ""
    echo "Examples:"
    echo "  $0                          # dry-run all states"
    echo "  $0 test security.firewall   # dry-run one state"
    echo "  $0 shell                    # interactive shell"
}

CMD="${1:-highstate}"

case "$CMD" in
    highstate)
        docker compose up --build
        ;;
    apply)
        docker compose run --rm salt salt-call --local state.highstate
        ;;
    test)
        STATE="${2:?Error: specify a state name, e.g. $0 test security.firewall}"
        docker compose run --rm salt salt-call --local state.apply "$STATE" test=True
        ;;
    pillar)
        docker compose run --rm salt salt-call --local pillar.items
        ;;
    shell)
        docker compose run --rm salt bash
        ;;
    build)
        docker compose build
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
