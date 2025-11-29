.PHONY: release-patch release-minor release-major help

help:
	@echo "Available commands:"
	@echo "  make release-patch  - Bump patch version (x.x.1) and push"
	@echo "  make release-minor  - Bump minor version (x.1.0) and push"
	@echo "  make release-major  - Bump major version (1.0.0) and push"

release-patch:
	@./scripts/bump_version.sh patch
	@git push && git push --tags

release-minor:
	@./scripts/bump_version.sh minor
	@git push && git push --tags

release-major:
	@./scripts/bump_version.sh major
	@git push && git push --tags
