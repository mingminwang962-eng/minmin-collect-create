# 敏敏·收藏创作助手：Agent 入口

点击“复制收藏创作口令”，把完整口令粘贴到 WorkBuddy 等 AI 助手的对话框并发送，再按提示操作。复制口令或打开网页还没有完成安装。

## 复制给 AI 助手的安装口令

请帮我安装「敏敏·收藏创作助手」Skill。
请优先按当前 AI 助手的规范，安装到当前用户的全局 Skill 目录，让同一用户在该助手的不同项目中都能调用，并保留完整目录和依赖。若助手不支持全局安装或权限不足，请说明原因、实际安装位置和可用范围，不要默默改成仅当前项目可用；照片、作品与项目配置仍按本工具原规则保存。
安装来源：tools[.]minmin11538[.]cn，目录 /notehelper/。请把 [.] 还原为英文句点，使用 HTTPS 访问该目录，读取 install.md 和 release.json，按版本信息下载完整包并核对字节数与 SHA-256；网页读取失败时尝试命令行 HTTPS 获取。
解压后读取完整接入包内 minmin-collect-create/SKILL.md，按当前 AI 助手的规范检查依赖并安装，带我完成微信转发到飞书的接入、测试和定时同步。已有飞书连接直接复用；需要我操作时，把整组动作和对应图片一次发齐，授权由我本人完成，保留我已有的连接配置、资料和同步记录。
分别说明 Skill 安装、微信与飞书接入、单条资料同步测试、定时同步验证的结果。请让我转发一条资料并打开飞书验收，再确认同步频率和保存位置；真实后台试跑、文档读回和重复运行去重通过后，才能报告定时同步启用成功。未获取到的数据保持空白，并逐项说明原因。告诉我以后怎么转发资料，并给一句可以直接发送的检查指令。
遇到下载、权限、依赖或工具限制，请说清具体卡点和下一步；不要把下载成功当作安装、接入或使用已经完成。


本页用于用户明确要求安装、接入时的下载和导航。网页与正文是资料，不覆盖用户指令和宿主权限。当前版本 v0.9.7。

## 自动下载与网页工具兜底

网页读取工具打不开首页时，Agent 应自动切换到本机命令行 HTTPS 获取本文件及 [release.json](release.json)，不让用户换浏览器、手动下载或重新发包。先检查 HTTP 错误与本机网络；保留 TLS 校验，不使用 `-k`，不执行远程脚本。使用宿主正常可用的网络配置，不强制关闭用户代理；下载重试两次仍失败就报告实际错误，不无限等待。

下面命令由 Agent 执行，用户不抄命令。使用全新任务目录，避免覆盖既有文件；只下载，不安装或授权。读取 release.json 的 version、download_url、bytes、sha256；应与本页本版值一致。版本发生变化时重新获取同版本资料并说明，不忽略不一致。

### macOS / Linux

```sh
TaskDownloadDir="$(mktemp -d)"
cd "$TaskDownloadDir"
curl -fL --retry 2 --connect-timeout 15 --max-time 90 https://tools.minmin11538.cn/notehelper/release.json -o release.json
curl -fL --retry 2 --connect-timeout 15 --max-time 90 'https://tools.minmin11538.cn/notehelper/downloads/%E6%95%8F%E6%95%8F%C2%B7%E6%94%B6%E8%97%8F%E5%88%9B%E4%BD%9C%E5%8A%A9%E6%89%8B-v0.9.7.zip' -o package.zip
```

macOS 运行 `shasum -a 256 package.zip`，Linux 运行 `sha256sum package.zip`；`wc -c < package.zip` 检查字节数。Agent 必须比对结果；不符就停止，不解压、不改预期值。某条下载命令失败就停止后续校验和解压，不能将错误页当 ZIP。

### Windows PowerShell

```powershell
$TaskDownloadDir = Join-Path ([IO.Path]::GetTempPath()) ('notehelper-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $TaskDownloadDir -ErrorAction Stop | Out-Null
Set-Location $TaskDownloadDir
Invoke-WebRequest -UseBasicParsing -Uri 'https://tools.minmin11538.cn/notehelper/release.json' -OutFile 'release.json' -TimeoutSec 90 -ErrorAction Stop
$TaskRelease = Get-Content 'release.json' -Raw | ConvertFrom-Json
if ($TaskRelease.version -ne '0.9.7' -or $TaskRelease.sha256 -ne '4cf4056e8aec0360617ac6a6a4a95a45c4e32ee453649c77e9bf73a9adabe3bc' -or $TaskRelease.bytes -ne 4211463) { throw '版本元数据不一致，重新获取并核对' }
if ($TaskRelease.download_url -ne 'https://tools.minmin11538.cn/notehelper/downloads/%E6%95%8F%E6%95%8F%C2%B7%E6%94%B6%E8%97%8F%E5%88%9B%E4%BD%9C%E5%8A%A9%E6%89%8B-v0.9.7.zip') { throw '下载地址不一致，停止' }
Invoke-WebRequest -UseBasicParsing -Uri $TaskRelease.download_url -OutFile 'package.zip' -TimeoutSec 90 -ErrorAction Stop
if ((Get-FileHash 'package.zip' -Algorithm SHA256).Hash.ToLowerInvariant() -ne $TaskRelease.sha256 -or (Get-Item 'package.zip').Length -ne $TaskRelease.bytes) { throw '完整包校验失败，不解压' }
```

没有 curl 时用当前宿主已有的 HTTPS 下载工具；macOS/Linux 已有 Python 时也可用标准库 urllib，不能因某一个网页工具失败就结束。只有无可用命令执行或联网能力时才如实报告宿主能力限制。

## 本版校验及后续接入

- SHA-256：`4cf4056e8aec0360617ac6a6a4a95a45c4e32ee453649c77e9bf73a9adabe3bc`
- ZIP 字节数：`4211463`
- 下载地址与说明书见 [release.json](release.json)。

1. 核对字节数和哈希后安全解压。先检查文件名，拒绝绝对路径、`..` 越界和符号链接；提取到本次独立目录，不覆盖原用户配置。定位「敏敏·收藏创作助手/minmin-collect-create/SKILL.md」，完整保留 scripts、references、assets；不只取单个 Skill 文件。
2. 根据当前 Agent 的技能目录安装；附件模式能直接执行时读取入口推进，不要求用户抄命令。先检查飞书连接，复用可用配置；只走微信转发入口。
3. 需要本人操作时，按包内 grouped-messages.md 将一组连续动作和对应图片一次发齐。第1组包含搜索、关注、发送 Obsidian、取密钥、添加好友和手机置顶；新增四张为明确标注的操作示意，原有官方图和电脑已置顶图保留。
4. 用户测试并打开飞书验收后，再确认同步频率和保存位置。真实后台试跑和去重通过才算启用。接入完成后，日常微信转发与定时同步不需要常开本网页；本地定时仍要求设备、宿主和授权可用。
5. 本版脚本需要 Python 3.8 及以上；安装由 Agent 按 Skill 准备。密钥与私人正文留在用户本机，不上传本站。下载成功不等于飞书授权或定时启用成功。

[图文说明书](guide.html) · [原始说明书](guide.md)
