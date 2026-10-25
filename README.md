# Cncp 官方插件仓库

Cncp 客户端的**官方**插件源。客户端「插件」页 →「市场」读的 `index.json` 就在这里，插件包（`.zip`）放在 `packages/`。

- 索引：[`index.json`](index.json)
- 插件包：`packages/<插件id>-<版本>.zip`
- 源码：`examples/<插件id>/`

> **本仓库不接受第三方上传。** 官方源只放官方自己维护的插件；想让别人也能装到你的插件，请提到第三方源 [cncp-Unofficial-Plugin](https://github.com/Char0n111/cncp-Unofficial-Plugin)（那边谁都能提 PR，走自动校验后合并）。

## 怎么装

客户端「插件」页 → 右上「市场」→ 源地址选 **官方源**（海外 / 有代理时最快）或 **官方镜像**（国内直连 raw 不通时用，走 ghproxy）→ 刷新 → 点「安装」。

也可以手动：在本仓库 `packages/` 下载 zip，客户端「插件」页点「＋ 导入插件（.zip 包）」选中即可。

> 客户端默认源就是这个 `index.json`；从源安装会强制校验 `sha256`，被改过的包直接拒装。

## 仓库结构

```
index.json                 # 客户端读的索引（schemaVersion 1）
packages/                  # 打好的插件包，文件名 = <id>-<version>.zip
examples/
  cn.example.actions/
    plugin.json            # 插件清单
    plugin.py              # 入口
  cn.example.hooks/
  cn.example.ping/
  cn.example.probe/
tools/build.ps1            # 打包 + 重算 sha256 + 重写 index.json
```

## 加一个新插件

```powershell
# 1) 在 examples/ 下新建目录，写 plugin.json 与入口文件（格式见插件编写说明）
# 2) 打包并重建索引
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1
# 3) 提交 examples/ packages/ index.json 三处变更
```

`tools/build.ps1` 会做三件容易出错的事：按 `id-version` 命名打包、算 `sha256`、把两者写进 `index.json`。**不要手改 `index.json` 里的 `sha256` 和 `url`** —— 手抄必错，而客户端校验不过就装不上。

## index.json 格式

```json
{
  "schemaVersion": 1,
  "name": "Cncp 官方插件仓库",
  "updated": "2026-10-25",
  "plugins": [
    {
      "id": "cn.example.actions",
      "name": "示例功能插件",
      "version": "1.0.0",
      "description": "演示怎么给客户端加自己的功能按钮",
      "author": "Cncp",
      "homepage": "https://clash.cupzz.cn/docs/plugins",
      "url": "packages/cn.example.actions-1.0.0.zip",
      "sha256": "55c5a9f0…",
      "capabilities": ["actions", "hooks", "tasks"]
    }
  ]
}
```

- `url` 为相对路径时，按 `index.json` 自身的地址解析成绝对地址；构建脚本传 `-BaseUrl` 可写成绝对地址。
- `sha256` 是 zip 的哈希（小写十六进制），客户端下载后必须校验。
- `schemaVersion` 目前是 `1`，加字段不会让老客户端失效，改这个数字才会。

## 社区插件

第三方插件不放这里。想收进客户端默认列表，提到聚合仓库（LSPosed 式的提交-审核-自动发布）：

- 聚合仓库：`cncp-plugin-repo`
- 提交方式：`modules/<插件id>/module.json` 提 PR，CI 校验后合并，站点与索引自动重建。

## 许可证

[MIT](LICENSE)。插件包里的代码各自继承其 `plugin.json` 里声明的作者与许可。
