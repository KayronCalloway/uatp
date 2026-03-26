# Changelog

## [Unreleased]

### Breaking Changes
- **Key password derivation removed** - Keys encrypted with machine-derived passwords will not decrypt
  - Run `python scripts/migrate_keys.py` to migrate existing keys
  - Or delete `.uatp_keys/` to regenerate (old signatures won't verify)
  - Production now **requires** `UATP_KEY_PASSWORD` environment variable

### Fixed
- Frontend TypeScript build errors resolved
- CSRF token handling for cookie auth

### Security
- Simplified key password management (single source of truth)
- Removed fragile machine-UUID-based password derivation
