# macOS Application Deployer Script

## Overview
This script automates the installation of macOS applications distributed as `.dmg` disk images.  
It is designed to be safe, idempotent, and easily extensible — allowing you to manage multiple applications (for example Slack and Google Chrome) using a single unified installer.

The deployer ensures proper cleanup, logging, and validation of system preconditions (platform, privileges, and internet access) before performing any installation tasks.

---

## Script Name
`app_deployer.sh`

---

## Objective
Automate the deployment of macOS applications in a consistent, reliable, and repeatable way, including:
- Downloading the latest `.dmg` installer from the official vendor source  
- Mounting the disk image to a controlled temporary location  
- Copying the `.app` bundle to `/Applications`  
- Removing quarantine attributes to prevent launch prompts  
- Verifying the installation and cleaning up temporary files  

---

## Features Implemented

- **Multi-app support**: currently supports `slack` and `chrome`, easily extendable to others.  
- **Safety mechanisms**: uses `set -euo pipefail` to stop immediately on any command failure.  
- **Comprehensive logging**: all actions logged with timestamps to console and `/var/log/app_install.log`.  
- **Dry-run mode**: prints every command that would be executed without making system changes.  
- **Force reinstall option**: allows overwriting an existing application installation.  
- **Automatic cleanup**: unmounts the DMG and removes all temporary files even on errors.  
- **Idempotent behavior**: skips reinstallation when the app is already installed unless explicitly forced.  

---

## How to Run

### Basic Installation (default: Slack)

### Make sure to <cd> to the folder where the script is located before running it. 


Before running for the first time, grant execution permissions:
```bash
chmod +x app_deployer.sh

```bash
sudo ./app_deployer.sh


### Install Google Chrome

sudo ./app_deployer.sh --app chrome


### Reinstall an Existing App
sudo ./app_deployer.sh --app slack --force-reinstall


### Test without Installing (dry-run)
./app_deployer.sh --app chrome --dry-run

### Custom Log File Location
sudo ./app_deployer.sh --app slack --log /tmp/slack_install.log






Option                                       Description

--app <name>                                 Application to install (slack, chrome)

--dry-run                                    Print actions without performing any changes

--log <path>                                 Write logs to a custom file

--force-reinstall                            Remove and reinstall even if already installed

-h, --help                                   Show help and usage information



### Example Log Output

[2025-10-18 13:32:14] [INFO]  === Installer started (app=chrome, dry-run=false, force-reinstall=false) ===
[2025-10-18 13:32:15] [INFO]  Downloading latest chrome DMG from official source...
[2025-10-18 13:32:21] [INFO]  Mounting DMG to /private/tmp/app_install.XXXXX/mnt ...
[2025-10-18 13:32:25] [INFO]  Copying Google Chrome.app to /Applications ...
[2025-10-18 13:32:33] [INFO]  Google Chrome.app installed successfully. Version: 130.0.6723.91
[2025-10-18 13:32:33] [INFO]  Unmounting and cleaning up...
[2025-10-18 13:32:34] [INFO]  === Completed successfully ===


### Assumptions
	•	Script is executed on macOS only (uname -s must return Darwin).
	•	The user runs the script with administrative privileges (sudo) to allow writing to /Applications and /var/log.
	•	Applications are distributed as .dmg bundles containing a standard .app package.
	•	Internet connectivity is available to reach the official download URLs for Slack or Chrome.

⸻

### Known Limitations
	•	Supports only .dmg installers; .pkg and .zip formats are not handled.
	•	No built-in rollback (cleanup handles partial installs safely).
	•	Currently supports only Slack and Google Chrome by default.
	•	Logging path assumes /var/log is writable (use --log to specify a custom file if needed).


### Extending the Script (for scalability)

To add a new application:
	1.	Open the script and locate the set_app_config() function.
	2.	Add a new case block for your desired app:

 zoom)
  APP_URL="https://zoom.us/client/latest/ZoomInstallerIT.pkg"
  APP_BUNDLE_NAME="zoom.us.app"
  ;;

	3.	Update the usage() section to include the new app name.

The deployer will automatically handle download, mount, copy, verification, and cleanup for the new app.

⸻

### Testing

To test the script safely without performing any installations:

./app_deployer.sh --app chrome --dry-run

### Example dry-run output:

[2025-10-18 12:01:04] [INFO]  === Installer started (app=chrome, dry-run=true, force-reinstall=false) ===
[2025-10-18 12:01:05] [INFO]  (dry-run) mkdir -p '/private/tmp/app_install.XXXXX' '/private/tmp/app_install.XXXXX/mnt'
[2025-10-18 12:01:06] [INFO]  (dry-run) curl -L --fail --silent --show-error 'https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg' -o '/private/tmp/app_install.XXXXX/app.dmg'
[2025-10-18 12:01:07] [INFO]  (dry-run) hdiutil attach '/private/tmp/app_install.XXXXX/app.dmg' -nobrowse -quiet -mountpoint '/private/tmp/app_install.XXXXX/mnt'
[2025-10-18 12:01:08] [INFO]  (dry-run) /usr/bin/ditto '/private/tmp/app_install.XXXXX/mnt/Google Chrome.app' '/Applications/Google Chrome.app'
[2025-10-18 12:01:09] [INFO]  === Completed successfully ===



### Exit Codes

| Code | Meaning |
|------|----------|
| 0 | Success |
| 1 | Unsupported platform or app |
| 2 | Not run as root |
| 3 | No internet connectivity |
| 4 | Download failed |
| 5 | DMG mount failed |
| 6 | Copy operation failed |
| 7 | Verification failed |
| 8 | Cleanup failed |
