#!/bin/bash
set -e

# Get current version from __init__.py
CURRENT_VERSION=$(grep -oP '__version__ = "\K[^"]+' src/enecoq_data_fetcher/__init__.py)

# Parse version components
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Determine bump type
BUMP_TYPE="${1:-patch}"

case "$BUMP_TYPE" in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Usage: $0 {major|minor|patch}"
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"

echo "Bumping version from $CURRENT_VERSION to $NEW_VERSION"

# Update version in __init__.py
sed -i.bak "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/enecoq_data_fetcher/__init__.py
rm src/enecoq_data_fetcher/__init__.py.bak

# Commit and tag
git add src/enecoq_data_fetcher/__init__.py
git commit -m "chore: bump version to $NEW_VERSION"
git tag "v$NEW_VERSION"

echo "Version bumped to $NEW_VERSION"
echo "Run 'git push && git push --tags' to publish"
