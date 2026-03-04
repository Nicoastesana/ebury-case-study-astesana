# Script to automate semantic version bumping
# Usage: .\scripts\bump-version.ps1 -Type minor -Message "Add new feature"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("major", "minor", "patch")]
    [string]$Type,

    [Parameter(Mandatory=$true)]
    [string]$Message,

    [Parameter(Mandatory=$false)]
    [switch]$CreateTag = $true
)

# Get current version
$versionFile = "VERSION"
if (-not (Test-Path $versionFile)) {
    Write-Error "VERSION file not found"
    exit 1
}

$currentVersion = Get-Content $versionFile -Raw
$currentVersion = $currentVersion.Trim()

# Parse version
$parts = $currentVersion -split '\.'
if ($parts.Count -ne 3) {
    Write-Error "Invalid version format: $currentVersion"
    exit 1
}

$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2]

# Calculate new version
switch ($Type) {
    "major" {
        $major++
        $minor = 0
        $patch = 0
    }
    "minor" {
        $minor++
        $patch = 0
    }
    "patch" {
        $patch++
    }
}

$newVersion = "$major.$minor.$patch"

Write-Host "Bumping version from $currentVersion to $newVersion ($Type)" -ForegroundColor Green

# Update VERSION file
$newVersion | Out-File -FilePath $versionFile -NoNewline -Encoding UTF8

# Update CHANGELOG.md
$changelogFile = "CHANGELOG.md"
$today = Get-Date -Format "yyyy-MM-dd"

$changelogContent = @"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$newVersion] - $today

### Changed

- $Message

"@

$existingChangelog = Get-Content $changelogFile -Raw
$existingChangelog = $existingChangelog -replace '# Changelog.*?and this project adheres to \[Semantic Versioning\]\(https://semver\.org/spec/v2\.0\.0\.html\)\.', ''
$changelogContent += $existingChangelog

$changelogContent | Out-File -FilePath $changelogFile -Encoding UTF8

# Update docker-compose.yml comment
$dockerFile = "docker-compose.yml"
$dockerContent = Get-Content $dockerFile -Raw
$dockerContent = $dockerContent -replace "# ELT Pipeline Version: [\d.]+", "# ELT Pipeline Version: $newVersion"
$dockerContent | Out-File -FilePath $dockerFile -Encoding UTF8

# Git operations
Write-Host "Staging changes..." -ForegroundColor Blue
git add VERSION CHANGELOG.md docker-compose.yml

Write-Host "Creating commit..." -ForegroundColor Blue
$commitMessage = "[release] - Bump version to $newVersion`n`n$Message"
git commit -m $commitMessage

if ($CreateTag) {
    Write-Host "Creating git tag..." -ForegroundColor Blue
    git tag -a "v$newVersion" -m "Release version $newVersion"
    Write-Host "Tag created: v$newVersion" -ForegroundColor Green
}

Write-Host "`n✓ Version bumped successfully!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git log -1"
Write-Host "  2. Push to remote: git push && git push --tags"

