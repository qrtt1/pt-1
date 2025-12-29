# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.2] - 2025-12-29

### Changed
- Adjust wait command defaults: 0.5s polling, 30s max wait, status output throttled to 1s.
- Update prompt guidance for wait timeout and transcript review flow.

## [0.4.1] - 2025-12-25

### Fixed
- **Security: Path traversal vulnerability**
  - Added path validation in `download_file()` endpoint
  - Prevents directory traversal attacks using `../` in filename parameter
  - Validates resolved file paths stay within command folder bounds

- **Critical: JSON decode error handling**
  - Added error handling in `_load_tokens_file()` for corrupted JSON
  - Prevents server crash if `tokens.json` is malformed
  - Returns empty tokens list and logs error instead of crashing

### Changed
- **Code quality improvements from comprehensive code review**
  - Centralized all datetime operations into utility functions
  - Added clear documentation for naive datetime (UTC) design decision
  - Documented single-worker limitation and multi-worker considerations
  - Clarified `stable_id` and `client_id` relationship with comments
  - Added shutdown error handling note in lifespan context
  - Removed duplicate `import time` statement

- **Server configuration enhancements**
  - Support `PT1_HOST` environment variable (default: `0.0.0.0`)
  - Support `PT1_PORT` environment variable (default: `5566`)
  - Updated `SERVER_SETUP.md` with environment variable documentation
  - Removed screen deployment section from documentation

- **English-only API responses and commands**
  - Converted all error messages to English (auth endpoints)
  - Removed emojis and Unicode characters from AI guide
  - Added explicit guideline: AI assistants must send English-only PowerShell commands
  - Includes examples of good vs bad commands in AI guide

- **Documentation reorganization**
  - Moved `SERVER_SETUP.md` to `prompts/server-setup.md`
  - Moved `dev.prompt` to `prompts/dev-notes.md`
  - Standardized all prompt files to kebab-case naming
  - Updated all references in README.md

- **Code formatting**
  - Applied black formatter to all Python code
  - Consistent code style across entire codebase

### Technical Details
- Datetime utilities: `get_current_time()`, `parse_datetime_string()`, `format_datetime_string()`, `add_seconds()`
- All datetime operations use naive datetime in UTC timezone
- Multi-worker mode not supported (in-memory session storage limitation)
- Path traversal protection uses `Path.resolve()` and prefix validation

## [0.4.0] - 2025-12-25

### Changed
- **Major project restructure: separated CLI and Server components**
  - Created `pt1_cli/` package for CLI component
  - Created `pt1_server/` package for Server component
  - Clear separation of concerns between client and server code
  - Both components can be independently developed and maintained

- **Modernized FastAPI application**
  - Migrated from deprecated `@app.on_event("startup")` to `lifespan` context manager
  - Using modern async context manager pattern for resource management
  - Removed unused PUBLIC_URL feature (auto-detection from requests)
  - Simplified startup messages using proper logging

- **Command IDs shortened from 36 to 8 characters**
  - Changed from full UUID format (e.g., `018302b1-2d28-40fd-a8ef-f7e163009e1e`)
  - To short format using first 8 hex characters (e.g., `5b4e01bc`)
  - Applies to command IDs and client event IDs
  - 78% reduction in length for better CLI readability
  - Auth tokens remain full UUID for security

### Added
- **Version management system**
  - Added `__version__.py` files for both CLI and Server components
  - CLI now supports `pt1 --version` and `pt1 -V` commands
  - Centralized version management through `setup.py`

- **Session token persistence across server restarts**
  - Session tokens now saved to `.session_tokens.json`
  - Auto-load on server startup with expiry validation
  - Clients no longer need to re-authenticate after server restart

- **New console commands**
  - `pt1-server`: New command to start server (alternative to uvicorn)
  - Both `pt1` (CLI) and `pt1-server` (Server) entry points available

### Fixed
- CLI `get-transcript` command now correctly handles plain text responses
  - Previously failed with JSON parse error
  - Now properly displays PowerShell transcript content

- Removed duplicate server files from project root
  - Cleaned up old `routers/`, `services/`, `templates/` directories
  - Removed `auth.py` and `main.py` from root
  - All server code now properly organized in `pt1_server/`

- Fixed file path handling for templates, uploads, and tokens
  - Templates loaded from package directory using relative paths
  - Tokens and uploads use current working directory (runtime data)

### Removed
- Removed `uploads/` directory from git tracking
- Added `session_tokens.json` to `.gitignore`
- Removed PUBLIC_URL environment variable support (auto-detect only)

## [0.3.0] - 2025-12-22

### Added
- Client heartbeat mechanism to keep long-running commands alive
  - New `/heartbeat/{client_id}` endpoint
  - Heartbeat job in client install script
- Command timeout inspection for executing commands

### Changed
- Default API token rotation interval to 7 days
- Client registry UX improvements for status and timestamps
- Terminate command UX improvements for async shutdown feedback

## [0.2.0] - 2025-12-19

### Added
- Graceful client termination feature with `@PT1:GRACEFUL_EXIT@` command
  - New `pt1 terminate <client_id>` CLI command
  - Server API endpoint `POST /terminate_client/{client_id}`
  - Client-side handling in `client_install.ps1` and `win_agent.ps1`
  - Auto-polling verification for client shutdown status
  - Cleanup and resource management before termination

### Changed
- Updated `SERVER_SETUP.md` with correct systemd service name
  - Service name: `powershell-executor.service` (not `pt1-server`)
  - Deployment path: `$HOME/workspace/pt-1`
  - Reorganized service management section to front of document
  - Added git sync workflow and common systemctl operations

### Technical Details
- Client exit code mechanism for graceful shutdown detection
- Win agent now properly handles exit code 0 for termination
- Client submits acknowledgment before shutting down
- 30-second timeout with status polling every 2 seconds

## [0.1.0] - 2025-12-19

### Added
- Initial release of PT-1 PowerShell Remote Execution Tool
- CLI tool for managing remote PowerShell execution
- Server-side API for command management
- Client-side PowerShell scripts (client_install.ps1, win_agent.ps1)
- Basic command execution and result retrieval
- File upload and download capabilities
- Transcript recording and management
- Multi-client support with stable client IDs
- API token authentication

### Features
- `pt1 auth` - Verify API token
- `pt1 quickstart` - Generate client installation command
- `pt1 list-clients` - List all registered clients
- `pt1 send` - Send PowerShell command to a client
- `pt1 get-result` - Get command execution result
- `pt1 wait` - Wait for command completion (auto-polling)
- `pt1 history` - Show command execution history
- `pt1 list-files` - List files from command result
- `pt1 download` - Download file from command result
- `pt1 list-transcripts` - List agent execution transcripts
- `pt1 get-transcript` - Get transcript content
- `pt1 help` - Show detailed help
- `pt1 prompt` - Show AI agent quick reference

[0.3.0]: https://github.com/qrtt1/pt-1/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/qrtt1/pt-1/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/qrtt1/pt-1/releases/tag/v0.1.0
