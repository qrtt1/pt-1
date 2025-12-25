# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Command IDs shortened from 36 to 8 characters**
  - Changed from full UUID format (e.g., `018302b1-2d28-40fd-a8ef-f7e163009e1e`)
  - To short format using first 8 hex characters (e.g., `5b4e01bc`)
  - Applies to command IDs and client event IDs
  - 78% reduction in length for better CLI readability
  - Auth tokens remain full UUID for security

### Added
- **Session token persistence across server restarts**
  - Session tokens now saved to `.session_tokens.json`
  - Auto-load on server startup with expiry validation
  - Clients no longer need to re-authenticate after server restart

### Fixed
- CLI `get-transcript` command now correctly handles plain text responses
  - Previously failed with JSON parse error
  - Now properly displays PowerShell transcript content

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
