# 木木公众号热点研究 Skill

这是「AI 内容工厂」课程配套的 Codex Skill，用来把一个内容主题转化为结构化的公众号热点研究报告。它通过大加拉公众号文章关键词搜索接口抓取相关文章，自动完成文章去重、正文清洗、主题相关度判断、落地价值评分、技术实践信号识别和传播热度评估，并生成可分享的 Markdown / HTML 报告。

这个 Skill 适合内容创作者、课程研发者、运营人员和研究型写作者使用：当你想知道某个主题最近有哪些公众号文章值得关注、哪些文章真正有案例和方法、哪些文章只是泛泛而谈时，可以让 Codex 使用这个 Skill 自动抓取相关文章，并按统一标准筛选、评分和排序。

## 它能帮你做什么

- 追踪某个公众号选题方向的近期热点文章。
- 研究一个行业、工具、技术或方法论在公众号里的讨论情况。
- 为公众号、小红书、课程、直播或社群内容寻找可拆解的案例。
- 观察竞品账号或同领域创作者正在写什么。
- 从大量搜索结果里筛出真正有实践价值的文章。
- 把高分文章沉淀进自己的选题库、案例库和素材库。
- 为「AI 内容工厂」式的选题生产线提供上游信息源。

典型主题包括 AI Agent、MCP、Claude Code、Codex Skill、自动化工作流、个人 IP、公众号写作、内容生产、知识库搭建、AI 工具测评、行业观察、商业案例和课程选题等。

## 下载

推荐下载这个文件：

https://github.com/xiaolydia/mumu-wechat-hotspot-research-skill/raw/main/wechat-hotspot-research-skill.zip

为了兼容旧文件名，仓库里也保留同内容的下载包：

https://github.com/xiaolydia/mumu-wechat-hotspot-research-skill/raw/main/mumu-wechat-hotspot-research-skill.zip

## 安装

下载后，在终端进入 zip 所在目录，例如：

```zsh
cd ~/Downloads
```

解压到本地 skills 目录：

```zsh
mkdir -p ~/.agents/skills
unzip -o wechat-hotspot-research-skill.zip -d ~/.agents/skills
```

确认安装成功：

```zsh
ls ~/.agents/skills/wechat-hotspot-research/SKILL.md
```

然后重启 Codex，让新 Skill 生效。

## 配置 API Key

这个 Skill 需要大加拉 API Key。不要把 key 写进课程文档、GitHub、聊天记录或脚本里，推荐放到本机环境变量。

临时使用一次：

```zsh
export DAJIALA_API_KEY="你的大加拉key"
```

长期自用：可以把这一行加到 `~/.zshrc`，以后每次打开终端都会自动加载。

验证是否配置成功：

```zsh
echo ${DAJIALA_API_KEY:+已设置}
```

如果输出 `已设置`，就可以使用了。

## 使用方式

在 Codex 里可以这样说：

```text
使用 $wechat-hotspot-research 抓取 AI Agent 工作流相关的公众号热点文章，并生成按分数排序的报告。
```

也可以换成自己的主题：

```text
使用 $wechat-hotspot-research 抓取 AI 内容工厂相关的公众号热点文章，最近 7 天，最多 30 条。
```

## 输出文件

每次运行会生成一个带时间戳的目录，里面通常有：

- `report.html`：可直接打开和分享的可视化热点报告。
- `report.md`：适合复制到 Obsidian、飞书文档或 GitHub 的 Markdown 报告。
- `selected_articles.json`：达到评分阈值的入选文章，适合继续进入选题库或自动化流程。
- `scored_articles.json`：所有抓取结果的完整评分表。
- `raw_responses.json`：接口原始响应，已移除 API Key。
- `run_meta.json`：本次运行的参数、抓取数量、入选数量、扣费字段和生成时间。

报告只展示标题、公众号、日期、数据指标、评分、入选理由、原文链接和短摘录，不复制全文，也不会保存 API Key。

## 评分逻辑

默认总分 100 分：

- 主题相关度：35 分。
- 实际落地价值：25 分。
- 技术实践信号：20 分。
- 可复用资产：15 分。
- 传播热度：5 分。

评分的目的不是绝对判断文章好坏，而是帮助内容研究时快速排序：优先看那些和主题强相关、同时有真实场景和可复用方法的文章。

## 注意事项

- 接口按返回条数扣费，第一次建议使用保守参数运行。
- 如果没有结果，可以放宽关键词、减少限制词或扩大时间范围。
- 如果结果太泛，可以增加排除词，或把主题关键词写得更具体。
- 如果 key 不小心暴露，请及时去大加拉后台重新生成。