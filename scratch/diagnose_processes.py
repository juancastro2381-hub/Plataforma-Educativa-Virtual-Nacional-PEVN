#!/usr/bin/env python3
import subprocess
import base64

ps_script = """
Get-Process python, pytest -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.Id
        ProcessName = $_.ProcessName
        StartTime = $_.StartTime
        CPU = $_.CPU
        WorkingSetMB = [math]::Round($_.WorkingSet64 / 1MB, 2)
        Threads = $_.Threads.Count
    }
} | Format-Table -AutoSize | Out-String -Width 4096
"""

encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("utf-8")
p = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], capture_output=True, text=True)
print(p.stdout)
