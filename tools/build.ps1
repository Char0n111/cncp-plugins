<#
.SYNOPSIS
    打包 examples/ 下的插件，重算 sha256，重写 index.json。

.DESCRIPTION
    为什么必须有脚本而不是手写 index.json：
      · sha256 手抄必错，客户端校验不过就装不上；
      · 版本号改了忘记同步 url（文件名里带版本）就会 404；
      · 包里混进 __pycache__ 会让每次打包的哈希都不一样。

.PARAMETER BaseUrl
    索引里 url 的前缀。不给就写相对路径（客户端按 index.json 所在地址解析）；
    给了就写绝对地址，例如 https://raw.githubusercontent.com/you/cncp-plugins/main

.PARAMETER RepoRoot
    仓库根目录，默认是本脚本的上一级。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1 -BaseUrl https://raw.githubusercontent.com/you/cncp-plugins/main
#>
param(
    [string]$BaseUrl = '',
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }

$examplesDir = Join-Path $RepoRoot 'examples'
$packagesDir = Join-Path $RepoRoot 'packages'

if (-not (Test-Path -LiteralPath $examplesDir)) { throw "找不到 examples 目录：$examplesDir" }
if (-not (Test-Path -LiteralPath $packagesDir)) { New-Item -ItemType Directory -Path $packagesDir -Force | Out-Null }

# 没给 -BaseUrl 时，从 git remote 推一个绝对前缀；推不出来就保留相对路径。
if (-not $BaseUrl) {
    Push-Location $RepoRoot
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # git 在非仓库目录会往 stderr 喷 fatal，不该让构建中断
    try {
        $remote = (& git remote get-url origin 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -eq 0 -and $remote -and $remote -notmatch '^(fatal|error)') {
            # git@github.com:owner/repo.git  /  https://github.com/owner/repo.git
            $m = [regex]::Match($remote, 'github\.com[:/]+(?<owner>[^/]+)/(?<repo>[^/.]+)')
            if ($m.Success) {
                $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
                if (-not $branch -or $branch -eq 'HEAD') { $branch = 'main' }
                $BaseUrl = "https://raw.githubusercontent.com/$($m.Groups['owner'].Value)/$($m.Groups['repo'].Value)/$branch"
                Write-Host "从 git remote 推导出 BaseUrl：$BaseUrl"
            }
        }
    } finally {
        $ErrorActionPreference = $prevEap
        Pop-Location
    }
}

$entries = @()

foreach ($pluginDir in (Get-ChildItem -LiteralPath $examplesDir -Directory | Sort-Object Name)) {
    $manifestPath = Join-Path $pluginDir.FullName 'plugin.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        Write-Host "跳过（无 plugin.json）：$($pluginDir.Name)"
        continue
    }

    # 清单里允许 // 注释和尾逗号，先去掉再解析
    $raw = [IO.File]::ReadAllText($manifestPath, [Text.Encoding]::UTF8)
    $raw = [Text.RegularExpressions.Regex]::Replace($raw, '(?m)^\s*//.*$', '')
    $raw = [Text.RegularExpressions.Regex]::Replace($raw, ',(\s*[}\]])', '$1')
    $manifest = $raw | ConvertFrom-Json

    if ($manifest.id -notmatch '^[a-z0-9.-]{6,64}$') { throw "插件 id 不合法：$($manifest.id)" }
    if (-not $manifest.version) { throw "插件 $($manifest.id) 缺少 version" }

    $zipName = "$($manifest.id)-$($manifest.version).zip"
    $zipPath = Join-Path $packagesDir $zipName

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }

    # 在插件目录内打包，zip 里就是干净的相对路径。
    # 排除 __pycache__ / *.pyc：Python 字节码缓存是本机跑出来的，打进包里既没用又会让 sha256 每次都变。
    & tar.exe -a -c -f $zipPath --exclude=__pycache__ --exclude='*.pyc' -C $pluginDir.FullName .
    if ($LASTEXITCODE -ne 0) { throw "打包失败：$($manifest.id)" }

    $hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()

    $url = if ($BaseUrl) { ($BaseUrl.TrimEnd('/') + '/packages/' + $zipName) } else { "packages/$zipName" }

    $entries += [ordered]@{
        id           = $manifest.id
        name         = $manifest.name
        version      = $manifest.version
        description  = $manifest.description
        author       = $manifest.author
        homepage     = $manifest.homepage
        url          = $url
        sha256       = $hash
        capabilities = @($manifest.capabilities)
    }

    Write-Host ("已打包 {0,-34} {1,10:N0} 字节  sha256={2}" -f $zipName, (Get-Item $zipPath).Length, $hash.Substring(0, 12))
}

$index = [ordered]@{
    schemaVersion = 1
    name          = 'Cncp 官方插件仓库'
    updated       = (Get-Date -Format 'yyyy-MM-dd')
    plugins       = $entries
}

$indexPath = Join-Path $RepoRoot 'index.json'
$json = $index | ConvertTo-Json -Depth 6
[IO.File]::WriteAllText($indexPath, $json, (New-Object Text.UTF8Encoding($false)))

Write-Host ''
Write-Host "已写 index.json：$($entries.Count) 个插件"
