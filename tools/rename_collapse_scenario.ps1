param(
    [string[]]$From = @("colapso1", "colpaso1"),
    [string]$To = "colapso2",
    [switch]$Apply,
    [switch]$Recurse
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$items = Get-ChildItem -LiteralPath $Root -File -Recurse:$Recurse | ForEach-Object {
    $file = $_
    foreach ($suffix in $From) {
        if ($file.BaseName.EndsWith($suffix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $prefix = $file.BaseName.Substring(0, $file.BaseName.Length - $suffix.Length)
            $newName = "$prefix$To$($file.Extension)"
            $newPath = Join-Path -Path $file.DirectoryName -ChildPath $newName

            [PSCustomObject]@{
                File    = $file
                OldName = $file.Name
                NewName = $newName
                NewPath = $newPath
                Source  = $suffix
            }
            break
        }
    }
}

if (-not $items) {
    Write-Host "No se encontraron archivos que terminen en: $($From -join ', ')"
    exit 0
}

$conflicts = $items | Where-Object { Test-Path -LiteralPath $_.NewPath }
if ($conflicts) {
    Write-Host "No se puede continuar porque estos nombres destino ya existen:"
    $conflicts | Select-Object OldName, NewName | Format-Table -AutoSize
    exit 1
}

if (-not $Apply) {
    Write-Host "Simulacion. Para aplicar los cambios ejecuta: .\renombrar_colapso.ps1 -Apply"
    $items | Select-Object OldName, NewName | Format-Table -AutoSize
    exit 0
}

foreach ($item in $items) {
    Rename-Item -LiteralPath $item.File.FullName -NewName $item.NewName
    Write-Host "Renombrado: $($item.OldName) -> $($item.NewName)"
}
