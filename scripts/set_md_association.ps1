<#
.SYNOPSIS
    Registers Friedrich as the handler for Markdown files (per-user, no admin).

.DESCRIPTION
    Creates the "Friedrich.md" ProgId under HKCU\Software\Classes with an open
    command of `"<exe>" "%1"` and associates the .md extension with it. The exe
    receives the file path as its positional argument and opens it exactly like
    the "Open file" menu action (see md_reader.py).

    Windows 11 protects the *default app* choice with a hashed UserChoice key
    that cannot be set from a script. After running this once, confirm the
    default via:
        Right-click a .md file -> Open with -> Choose another app ->
        select Friedrich -> tick "Always use this app" -> OK.

    Re-run this script after every rebuild if the exe path changes.

.PARAMETER ExePath
    Path to Friedrich.exe. Defaults to ..\dist\Friedrich.exe relative to this
    script.

.PARAMETER Remove
    Unregisters the association (removes the ProgId and the .md class entry).

.EXAMPLE
    .\set_md_association.ps1

.EXAMPLE
    .\set_md_association.ps1 -ExePath 'D:\apps\Friedrich.exe'

.EXAMPLE
    .\set_md_association.ps1 -Remove
#>
[CmdletBinding()]
param(
    [string] $ExePath = (Join-Path $PSScriptRoot '..\dist\Friedrich.exe'),
    [switch] $Remove
)

$ErrorActionPreference = 'Stop'

$progId    = 'Friedrich.md'
$progIdKey = "HKCU:\Software\Classes\$progId"
$extKey    = 'HKCU:\Software\Classes\.md'

function Invoke-ShellChangeNotify {
    Add-Type -Namespace Win32 -Name Shell -MemberDefinition `
        '[DllImport("shell32.dll")] public static extern void SHChangeNotify(int e, int f, IntPtr a, IntPtr b);'
    # SHCNE_ASSOCCHANGED = 0x08000000
    [Win32.Shell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
}

if ($Remove) {
    Remove-Item -Path $progIdKey -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $extKey) {
        Remove-ItemProperty -Path $extKey -Name '(default)' -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path "$extKey\OpenWithProgids" -Name $progId -ErrorAction SilentlyContinue
    }
    Invoke-ShellChangeNotify
    Write-Host "Removed the Friedrich .md association. Reset the default app via Windows Settings if needed."
    return
}

$resolved = (Resolve-Path -LiteralPath $ExePath).Path
if ([System.IO.Path]::GetExtension($resolved).ToLowerInvariant() -ne '.exe') {
    throw "Not an .exe: $resolved"
}

# 1) ProgId with open command, friendly name and icon.
New-Item -Path "$progIdKey\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path $progIdKey -Name '(default)' -Value 'Markdown Document'
Set-ItemProperty -Path "$progIdKey\shell\open\command" -Name '(default)' -Value ("`"$resolved`" `"%1`"")
New-Item -Path "$progIdKey\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "$progIdKey\DefaultIcon" -Name '(default)' -Value ("`"$resolved`",0")

# 2) Associate .md with the ProgId and list it under "Open with".
New-Item -Path $extKey -Force | Out-Null
Set-ItemProperty -Path $extKey -Name '(default)' -Value $progId
New-Item -Path "$extKey\OpenWithProgids" -Force | Out-Null
Set-ItemProperty -Path "$extKey\OpenWithProgids" -Name $progId -Value ([byte[]]@()) -Type Binary

# 3) Tell Explorer associations changed.
Invoke-ShellChangeNotify

Write-Host "Registered .md -> $progId"
Write-Host ("command: " + (Get-ItemProperty "$progIdKey\shell\open\command").'(default)')
Write-Host ""
Write-Host "Final step (once): right-click a .md file -> Open with -> Choose another app"
Write-Host "-> select Friedrich -> tick 'Always use this app' -> OK."
