#!/bin/bash
# Install git hooks for SkyCast
set -e

echo "📦 Installing SkyCast git hooks..."

HOOKS_DIR=".githooks"
GIT_HOOKS_DIR=".git/hooks"

for hook in "$HOOKS_DIR"/*; do
    name=$(basename "$hook")
    target="$GIT_HOOKS_DIR/$name"
    cp "$hook" "$target"
    chmod +x "$target"
    echo "  ✅ Installed $name hook"
done

echo ""
echo "🎯 Hooks installed:"
ls -la "$GIT_HOOKS_DIR"/pre-*
