---
name: expert-pack-release
description: 把 WorkBuddy 专家包（agent/plugin 型）发布到 GitHub 发布仓库（Agents）。当用户要求「把某专家上传/发布/更新到 GitHub」「上线专家包」「打 zip 供导入」「发布 vX.Y.Z 版本」时调用。产出：仓库内 `专家名/` 源码目录 + `专家名.zip` 打包版 + 顶层 README 章节 + git tag。
agent_created: true
---

# 专家包发布流水线（expert-pack-release）

把 `~/.workbuddy/plugins/marketplaces/my-experts/plugins/<name>/` 下的专家包，发布成 GitHub 仓库里的
「**源码目录 + 同名 zip**」双份形态，并打上版本 tag。

只管**发布**。专家的设计、内容改写在 `expert-manager`；本 Skill 不碰包内方法学。

## 关键路径（默认值，先核对再执行）

| 项 | 路径 |
|----|------|
| 专家包源（唯一真源） | `C:\Users\Silen\.workbuddy\plugins\marketplaces\my-experts\plugins\<name>\` |
| 仓库工作副本 | `C:\Users\Silen\Desktop\Zskill\Agents`（**勿用** `~/.workbuddy/tmp`，会被清理） |
| 远端 | `https://github.com/Silent-GitHub01/Agents.git`（分支 `main`） |

> cache 目录（`plugins/cache/...`）是编译产物，**永远不要改**。

## 六步流程

### 1. 核对源包
```bash
find "<源目录>" -type f | sort && cat "<源目录>/.codebuddy-plugin/plugin.json"
```
确认：`plugin.json` 的 `name` / `version` / `agents` / `avatar` 字段，以及 `avatars/expert.png` 存在。
**版本号以用户要求为准**（用户说 v0.1.0 就把 `plugin.json` 的 `version` 改成 `0.1.0`）。

### 2. 复制进仓库
```bash
cd "C:/Users/Silen/Desktop/Zskill/Agents" \
  && rm -rf <name> <name>.zip \
  && cp -r "<源目录>" ./<name>
```
`cp -r` 会带上 `.codebuddy-plugin/` 隐藏目录，务必 `find` 复查条数。

### 3. 改 README（两份保持一致）
- 源目录 `README.md` 若是脚手架模板（含 `[TODO: ...]`），**重写为正式版**：一句话定位、目录结构、
  能力清单、导入方式、示例提问、使用铁律、许可证。
- 改完 `cp` 同步到仓库副本（或两边都写）。
- 仓库顶层 `README.md` 补：标题/导语（若原来只描述单个专家）、目录树两行、文件说明表两行、独立专家章节。

### 4. 打 zip
本机**没有 `zip` 命令**，用脚本：
```bash
cd "C:/Users/Silen/Desktop/Zskill/Agents" \
  && "C:/Users/Silen/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
     "C:/Users/Silen/.workbuddy/skills/expert-pack-release/scripts/make_zip.py" <name>
```
zip **根必须是 `<name>/`**（脚本已保证），打完立刻列出条目核对数量与中文文件名。

### 5. 提交
```bash
git add -A && git status --short
git commit -m "feat: 上传<中文专家名>专家包 vX.Y.Z（源码 + 打包版）"
```
提交正文用 `-` 列表写清：源码目录 / agent md 内容要点 / 头像 / zip / README 改动。

### 6. tag + push + 验
```bash
git tag -a vX.Y.Z -m "<中文专家名>专家包 vX.Y.Z"
git pack-refs --all --prune          # 必须！见坑 2
git tag -l                            # 读得到才算成功
git push origin main refs/tags/vX.Y.Z
git ls-remote origin | head           # 远端验证（curl 无外网）
```
最后用 WebFetch 打开 `https://github.com/Silent-GitHub01/Agents/tree/main/<name>` 看渲染结果。

## 坑表（每一条都踩过）

| # | 现象 | 处理 |
|---|------|------|
| 1 | `.git/refs/` 下**新建**路径被静默回滚（`git fetch`/`update-ref` 返回 0 但不落盘，status 显示 `[gone]`） | 只写**已存在**的 ref 文件；需要写 origin/main 就手工向 `.git/packed-refs` **追加**一行（追加，不是覆盖 —— 见坑 7） |
| 2 | `git tag` 后 `.git/refs/tags/` 是**空**的（tag 被回滚） | `git tag -a` 后立刻 `git pack-refs --all --prune`，把 tag 固化进 `packed-refs`；用 `git tag -l` 验证 |
| 3 | 旧 zip 是废包（只含 agents/plugin/README/avatar，丢了 references） | 每次**重新打包**并 `zipfile.infolist()` 逐条核对文件数；专家包带 `references/` 时尤其要查 |
| 4 | 本机无 `zip` / 无 `gh` / `curl` 完全不通（连 api.github.com 都 000） | 打包用 python `zipfile`；远端验证用 `git ls-remote origin` 或 WebFetch 打开 GitHub 页面；**写操作走 python urllib + 本地代理（见坑 10）** |
| 10 | 需要**新建 GitHub 仓库**：gh 不存在、github connector 报 403（token 无建库权限）、curl 不通 | **python urllib + 本地代理 + git credential token** 调 `POST https://api.github.com/user/repos`。token 取法（不打印）：`printf 'protocol=https\nhost=github.com\n\n' | git credential fill` 取 `password=` 行，经环境变量传给 python；代理直接用 env `http_proxy`/`https_proxy`（本机为 `http://127.0.0.1:<端口>`）；请求头必须带 `User-Agent`。实测 201 成功（Agent-hanlinbianxiu） |
| 5 | 源包 README 是 `[TODO: ...]` 模板 | 发布前重写，源码版与仓库版内容一致，避免读者拿到模板 |
| 6 | `plugin.json` 版本与 tag 不一致 | 先定 tag 版本 → 回改 `plugin.json` 的 `version`（源 + 仓库两处）→ 再打包提交 |
| 7 | **覆盖式重写 `.git/packed-refs`**（`printf ... > .git/packed-refs`）会连带清掉 `refs/heads/main`、`refs/tags/<tag>` 及其 `^<peeled>` 行 → HEAD 解析失败，status 显示「No commits yet on main」+ 所有文件变 `A`（看着像仓库报废） | 改 packed-refs **只能追加或替换单行，绝不整体覆盖**。若已误覆盖，按 `# pack-refs with: ...` → `heads/main` → `remotes/origin/main` → `tags/<tag>` → `^<peeled sha>` 顺序重建；`git rev-parse HEAD`、`git tag -l`、`git log` 三者都能读才算修好（对象库未受损，一定能救回） |
| 8 | 工作副本被无关文件污染（如把校勘产物写进仓库目录），伴随仓库文件被删 | 先 `git status` 分清「未跟踪的杂文件」与「被删的 tracked 文件」：被删文件用 `git restore --worktree -- .` 从 index 恢复（`restore` 默认取 **index** 而非 HEAD，HEAD 坏掉也能救）；未跟踪杂文件**不要擅自删**，先 MD5 比对是否有正本、再让用户决定 |
| 9 | 用 python **文本模式**写 `.git/packed-refs`（`open(p,"w")`）→ Windows 下 `\n` 被转成 `\r\n`，git 报 `fatal: unexpected line in .git/packed-refs: <ref>?`，随后**所有** ref（HEAD/origin/main/tag）解析失败 | 必须用**二进制**模式读写：`d=open(p,"rb").read()` → 只 `replace` 目标那一行 → `open(p,"wb").write(d)`。文本模式下要么 `newline=""`、要么 `newline="\n"`。改完用 `git rev-parse HEAD`、`git rev-parse origin/main`、`git tag -l` 三验；若已写坏，`d.replace(b"\r\n",b"\n")` 可一键救回 |

## 后续维护：重新同步

```bash
cd C:/Users/Silen/Desktop/Zskill/Agents
git fetch origin --prune
git status -sb                # 期望 ## main...origin/main（无 ahead / [gone]）
```

- 若 `origin/main` 读不到（沙箱坑 1）：只更新 `.git/packed-refs` 里**那一行** `refs/remotes/origin/main`，
  **不要**触碰 `refs/heads/main` 与 `refs/tags/*` 行（覆盖会触发坑 7）。安全改法（二进制模式，防坑 9）：

  ```python
  p = r"C:\...\Agents\.git\packed-refs"
  d = open(p, "rb").read()
  d = d.replace(b"<旧 sha> refs/remotes/origin/main", b"<新 sha> refs/remotes/origin/main")
  open(p, "wb").write(d)
  ```
- 远端有新提交、而本地 HEAD 已是新 sha（另一会话已推）时，只需修引用，**不需要 pull**。
- 修完三方对齐验证：`git rev-parse HEAD` = `git rev-parse origin/main` = `git ls-remote origin refs/heads/main`。

## 新建独立专家仓库（一库一专家）

某专家要独立发版时（connector 403、无 gh、curl 不通的环境）：

1. **建空仓库**：`TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | grep '^password=' | cut -d= -f2-)`，然后 python（`GH_TOKEN=$TOKEN`）urllib 经本地代理调 `POST /user/repos`，body `{"name":"Agent-<名>","private":false,"auto_init":false}`，头带 `Authorization: Bearer` 与 `User-Agent`。
2. **本地**：`git init -q -b main` → 源目录内容**平铺为顶层**（不再套 `<name>/` 子目录）→ 复制/重打 zip → 重写 README（目录结构、能力、导入方式、**版本记录表**、实战成果外链）→ 设局部 user.name/email → commit。
3. **push 与引用**：`git remote add origin <url>` → `push -u origin main` → 若 `origin/main` 读不到，**新建 `.git/packed-refs`（二进制模式）**写 header + `refs/remotes/origin/main` 行（packed-refs 文件本身可新建，坑 1 的回滚只影响 `.git/refs/` 子目录）。
4. **tag**：`git tag -a vX.Y.Z -m "…首发"` → `git pack-refs --all --prune` → `git tag -l` 验证 → `git push origin vX.Y.Z` → WebFetch 验渲染。
5. **提示用户**：总库旧副本未删时与新库分叉，后续更新只走独立库，总库是否清理待用户定夺。

## 交付口径

发布完成的回复必须包含：仓库 URL、commit sha、tag 名、远端目录已验证（列出实际文件名/条数）、
以及任何版本号相关的提示（例如把 `plugin.json` 从 1.0.0 降到 0.1.0 时，说明这对「更新检测」可能有影响）。
