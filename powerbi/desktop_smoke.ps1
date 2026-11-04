# Run only on the disposable Windows CI desktop. Capture actual report rendering.
param([string]$Root = 'powerbi', [string]$Output = 'native-evidence')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes,System.Windows.Forms,System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class DistroFitWindow {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flag,uint x,uint y,uint data,UIntPtr extra);
}
'@
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = '--force-renderer-accessibility'
$exe = 'C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe'
$project = (Resolve-Path "$Root/DistroFit.pbip").Path
New-Item -ItemType Directory -Path $Output -Force | Out-Null
$workspaceRoot = Join-Path $env:LOCALAPPDATA 'Microsoft/Power BI Desktop/AnalysisServicesWorkspaces'
$beforePorts = @(Get-ChildItem $workspaceRoot -Filter msmdsrv.port.txt -Recurse -ErrorAction SilentlyContinue | ForEach-Object FullName)
$owned = Start-Process $exe -ArgumentList "`"$project`"" -PassThru
$ownedStarted = $owned.StartTime.ToUniversalTime().ToString('o')
$children = @()
function Get-Elements($window) {
 return $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
}
function Click-Element($element) {
 $r = $element.Current.BoundingRectangle
 if ($r.Width -le 0 -or $r.Height -le 0) { throw 'Cannot click invisible element' }
 [DistroFitWindow]::SetCursorPos([int]($r.X+$r.Width/2), [int]($r.Y+$r.Height/2)) | Out-Null
 [DistroFitWindow]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 [DistroFitWindow]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function Capture($name) {
 $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
 $bmp = New-Object System.Drawing.Bitmap $screen.Width,$screen.Height
 $graphics = [System.Drawing.Graphics]::FromImage($bmp)
 try {
  $graphics.CopyFromScreen($screen.Left,$screen.Top,0,0,$bmp.Size)
  $bmp.Save((Join-Path (Resolve-Path $Output) "$name.png"))
 } finally { $graphics.Dispose(); $bmp.Dispose() }
}
try {
 $deadline = (Get-Date).AddSeconds(120)
 $window = $null
 do {
  Start-Sleep -Seconds 2
  $owned.Refresh()
  if ($owned.HasExited) { throw "Desktop exited: $($owned.ExitCode)" }
  if ($owned.MainWindowHandle -ne 0) { $window = [System.Windows.Automation.AutomationElement]::FromHandle($owned.MainWindowHandle) }
 } while (-not $window -and (Get-Date) -lt $deadline)
 if (-not $window) { throw 'No Desktop window' }
 [DistroFitWindow]::SetForegroundWindow($owned.MainWindowHandle) | Out-Null
 Start-Sleep -Seconds 20
 Capture 'desktop-initial'
 $portDeadline = (Get-Date).AddSeconds(120)
 $portFile = $null
 do {
  $portFile = Get-ChildItem $workspaceRoot -Filter msmdsrv.port.txt -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notin $beforePorts } | Select-Object -First 1
  if (-not $portFile) { Start-Sleep -Seconds 2 }
 } while (-not $portFile -and (Get-Date) -lt $portDeadline)
 if (-not $portFile) { throw 'Desktop did not open a model. See desktop-initial.png' }
 $port = [System.IO.File]::ReadAllText($portFile.FullName, [System.Text.Encoding]::Unicode).Trim()
 Write-Host "Desktop-owned model port=$port, desktop PID=$($owned.Id), started=$ownedStarted"
 dotnet run --project "$Root/NativeCheck" -- $Root $port $Output
 if ($LASTEXITCODE) { throw 'Native model checks failed' }
 Start-Sleep -Seconds 5
 $elements = Get-Elements $window
 $names = @($elements | ForEach-Object { $_.Current.Name } | Where-Object { $_ } | Select-Object -Unique -First 600)
 $names | ConvertTo-Json | Set-Content "$Output/desktop-controls.json"
 # The report tab must be visible; schema validation is not a substitute for opening it.
 foreach ($page in @('Overview','Information criteria','Goodness of fit','Dataset detail')) {
  $elements = Get-Elements $window
  $tab = @($elements | Where-Object { $_.Current.Name -eq $page -and $_.Current.BoundingRectangle.Width -gt 0 }) | Select-Object -First 1
  if (-not $tab) { throw "Report page not exposed: $page. See desktop-controls.json and desktop-initial.png" }
  Click-Element $tab
  Start-Sleep -Seconds 5
  Capture ($page.ToLower().Replace(' ','-'))
 }
 @{status='PASS';pages=4;pid=$owned.Id;started=$ownedStarted} | ConvertTo-Json | Set-Content "$Output/desktop-open.json"
} finally {
 try { Capture 'desktop-final' } catch { Write-Warning "Final capture failed: $_" }
 # Record only descendants of the precise process launched above.
 $all = @(Get-CimInstance Win32_Process)
 $ids = @($owned.Id)
 do {
  $next = @($all | Where-Object { $_.ParentProcessId -in $ids -and $_.ProcessId -notin $ids })
  $ids += @($next | ForEach-Object { $_.ProcessId })
  $children += $next
 } while ($next.Count)
 $owned.Refresh()
 if (-not $owned.HasExited) {
  $owned.CloseMainWindow() | Out-Null
  if (-not $owned.WaitForExit(15000)) { $owned.Kill(); $owned.WaitForExit(10000) | Out-Null }
 }
 foreach ($child in $children) {
  $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($child.ProcessId)"
  if ($current -and $current.CreationDate -eq $child.CreationDate) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
   $childHandle = Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
   if ($childHandle) { $childHandle.WaitForExit(10000) | Out-Null; $childHandle.Dispose() }
  }
 }
 $remaining = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -in $ids })
 @{owner='DistroFit Desktop smoke';pid=$owned.Id;started=$ownedStarted;port=$port;remaining=$remaining.Count;cleanup='CloseMainWindow, wait, exact owned PID fallback; recorded descendant PIDs';descendants=@($children | Select-Object ProcessId,ParentProcessId,CreationDate,Name)} | ConvertTo-Json | Set-Content "$Output/desktop-cleanup.json"
 if ($remaining.Count) { throw 'Owned Desktop resources remain' }
 $owned.Dispose()
}
