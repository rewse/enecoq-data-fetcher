#!/bin/bash
# Bumps the package version, commits it, and tags the commit.
#
# Usage: scripts/bump_version.sh {major|minor|patch} [--push]
#
# With --push, sends main and the new tag to origin in one atomic push,
# which triggers the release workflow.

set -euo pipefail

readonly VERSION_FILE="src/enecoq_data_fetcher/__init__.py"
readonly RELEASE_BRANCH="main"

die() {
  echo "Error: $*" >&2
  exit 1
}

usage() {
  echo "Usage: $0 {major|minor|patch} [--push]" >&2
  exit 1
}

cd "$(dirname "$0")/.."

[[ $# -eq 1 || $# -eq 2 ]] || usage
bump_type="$1"
push=false
if [[ $# -eq 2 ]]; then
  [[ "$2" == "--push" ]] || usage
  push=true
fi

current_version=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$VERSION_FILE")
[[ "$current_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] \
  || die "Unexpected version in $VERSION_FILE: '$current_version'"
major="${BASH_REMATCH[1]}"
minor="${BASH_REMATCH[2]}"
patch="${BASH_REMATCH[3]}"

case "$bump_type" in
  major) new_version="$((major + 1)).0.0" ;;
  minor) new_version="$major.$((minor + 1)).0" ;;
  patch) new_version="$major.$minor.$((patch + 1))" ;;
  *) usage ;;
esac
readonly tag="v$new_version"

# Refuse to release anything but a clean, pushed main, so the release commit
# contains only the version change and the tag points at published history.
[[ -z "$(git status --porcelain)" ]] \
  || die "Working tree has uncommitted or untracked files"
[[ "$(git symbolic-ref --quiet --short HEAD || true)" == "$RELEASE_BRANCH" ]] \
  || die "Releases must be made from $RELEASE_BRANCH"
git fetch --quiet origin "$RELEASE_BRANCH"
[[ "$(git rev-parse HEAD)" == "$(git rev-parse "origin/$RELEASE_BRANCH")" ]] \
  || die "$RELEASE_BRANCH is not in sync with origin/$RELEASE_BRANCH"
! git rev-parse --quiet --verify "refs/tags/$tag" >/dev/null \
  || die "Tag $tag already exists locally"
[[ -z "$(git ls-remote --tags origin "refs/tags/$tag")" ]] \
  || die "Tag $tag already exists on origin"

echo "Bumping version from $current_version to $new_version"
sed -i.bak "s/^__version__ = \"$current_version\"$/__version__ = \"$new_version\"/" \
  "$VERSION_FILE"
rm "$VERSION_FILE.bak"

git commit --quiet -m "chore: bump version to $new_version" -- "$VERSION_FILE"
git tag "$tag"
echo "Created commit and tag $tag"

if [[ "$push" == true ]]; then
  git push --atomic origin "$RELEASE_BRANCH" "refs/tags/$tag"
else
  echo "Run 'git push --atomic origin $RELEASE_BRANCH refs/tags/$tag' to publish"
fi
