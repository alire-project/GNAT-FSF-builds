#!/bin/sh

classic=$(xcrun --find ld-classic 2>/dev/null) || true

if [ -n "$classic" ]; then
    exec $classic "$@"
else
    exec ld "$@"
fi

