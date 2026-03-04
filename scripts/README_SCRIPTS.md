# Quick version bump helpers
# These are convenience scripts for common version bumps

# PATCH bump (bug fixes)
# Usage: .\scripts\bump-patch.ps1 -Message "Fix ingestion bug"
param([Parameter(Mandatory=$true)][string]$Message)
.\scripts\bump-version.ps1 -Type patch -Message $Message

---

# MINOR bump (new features)
# Usage: .\scripts\bump-minor.ps1 -Message "Add new customer dimension"
param([Parameter(Mandatory=$true)][string]$Message)
.\scripts\bump-version.ps1 -Type minor -Message $Message

---

# MAJOR bump (breaking changes)
# Usage: .\scripts\bump-major.ps1 -Message "Refactor database schema"
param([Parameter(Mandatory=$true)][string]$Message)
.\scripts\bump-version.ps1 -Type major -Message $Message

