#!/bin/bash

# Find all TSX/TS files with potential hardcoded English strings
# Excludes: test files, node_modules, .next, already translated files

echo "🔍 Scanning for untranslated strings in components..."
echo ""

# Find files with English text in JSX/TSX that don't use translations
find app components -type f \( -name "*.tsx" -o -name "*.ts" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -name "*.test.*" \
  ! -name "*.spec.*" \
  ! -name "*.d.ts" \
  ! -name "index.ts" \
  ! -name "types.ts" \
  ! -name "constants.ts" \
  ! -name "utils.ts" \
  ! -name "config.ts" \
  -exec sh -c '
    file="$1"
    # Check if file has English strings in JSX/HTML context
    if grep -qE "(>|title=|placeholder=|aria-label=)[A-Z][a-z]{2,}" "$file" 2>/dev/null; then
      # Check if file uses translations
      if ! grep -q "useTranslations\|loadTranslations" "$file" 2>/dev/null; then
        # Count potential English strings
        count=$(grep -oE "(>|title=|placeholder=|aria-label=)[A-Z][a-z]{2,}" "$file" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
          echo "$file ($count potential strings)"
        fi
      fi
    fi
  ' sh {} \; | sort -t'(' -k2 -rn | head -50

echo ""
echo "✅ Scan complete. Showing top 50 files with most untranslated strings."
