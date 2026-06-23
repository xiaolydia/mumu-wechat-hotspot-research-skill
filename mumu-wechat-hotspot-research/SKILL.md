---
name: mumu-wechat-hotspot-research
description: 木木课程专用公众号热点研究 Skill。通过大加拉关键词搜索接口抓取微信公众号文章，按主题相关度、落地价值、技术实践和热度打分，并生成 Markdown/HTML 热点报告。适用于公众号热点抓取、行业选题监控、竞品内容观察、AI 工具/Agent/课程/行业研究等任意主题的文章筛选与分享报告。
---

# 木木公众号热点研究

用这个 skill 把一个主题变成一份按分数排序的公众号文章热点报告。保持通用性：除非用户明确要求，不要把某个人的垂类、API Key、输出目录或评分阈值写死。

## 工作流

1. 明确主题和关键词。
   - 如果用户已经给出主题，自动推导 2-5 个搜索关键词和少量排除词。
   - 只有当主题过于模糊、无法形成关键词时才追问。
2. 检查接口凭证。
   - 优先从环境变量 `DAJIALA_API_KEY` 读取。
   - 不要把 API Key 写进 `SKILL.md`、生成报告、命令示例、Git 提交或聊天回复。
   - 如果没有 key，先用 `--dry-run` 跑内置样例，验证流程是否正常。
3. 运行抓取脚本。
   - 第一次优先用保守参数：`--pages 1`、`--max-results 30`、`--min-score 70`。
   - 付费接口运行前，如果页数或关键词较多，先估算最多会返回多少条。
4. 检查报告产物。
   - 用 `report.md` 快速检查文字版报告。
   - 用户要分享视觉报告时，用 `report.html`。
   - 下游自动化需要结构化数据时，用 `selected_articles.json`。
5. 如果主题很垂直，首轮运行后可调整 `--topic-keywords`、`--exclude-keywords` 和 `--min-score` 再跑一轮。

## 快速命令

先用内置的 Claude Agent Skills 样例测试流程：

```bash
python scripts/wechat_hotspot_research.py --profile claude-agent-skills --dry-run
```

真实抓取 Claude Agent Skills 相关文章：

```bash
export DAJIALA_API_KEY="你的真实key"
python scripts/wechat_hotspot_research.py \
  --profile claude-agent-skills \
  --pages 1 \
  --max-results 30 \
  --output-dir ./wechat-hotspot-output
```

抓取任意通用主题：

```bash
python scripts/wechat_hotspot_research.py \
  --kw "AI Agent" \
  --kw "MCP" \
  --any-kw "实战 案例 教程 工作流" \
  --ex-kw "招聘 英语 游戏" \
  --topic "AI Agent 技术实践" \
  --topic-keywords "AI Agent,MCP,工作流,智能体,工具调用" \
  --exclude-keywords "招聘,英语,游戏,招生" \
  --period 7 \
  --pages 1
```

## API Key 放在哪里

推荐放在终端环境变量里，不要放进 Skill 文件。

临时使用一次：在同一个终端窗口里先执行：

```bash
export DAJIALA_API_KEY="你的真实key"
```

然后再运行抓取命令。这个设置只在当前终端会话里有效。

长期自用：可以把下面这一行加到 `~/.zshrc`，以后每次打开终端都会自动加载：

```bash
export DAJIALA_API_KEY="你的真实key"
```

分享给别人时，不要分享自己的真实 key。对方应该用自己的 key 设置 `DAJIALA_API_KEY`。

## 脚本行为

主脚本是 `scripts/wechat_hotspot_research.py`。

每次运行会生成一个带时间戳的目录，里面包含：

- `run_meta.json`：运行参数、数量统计、接口返回的扣费和余额字段。
- `raw_responses.json`：原始接口响应，已移除 API Key。
- `scored_articles.json`：所有标准化并完成评分的文章。
- `selected_articles.json`：达到阈值且未被排除的文章。
- `report.md`：可读的 Markdown 报告。
- `report.html`：可直接分享的独立 HTML 报告。

## 评分规则

默认总分 100 分：

- 主题相关度：35 分
- 实际落地/场景信号：25 分
- 最新技术实践信号：20 分
- 可复用资产，如代码、提示词、模板、SOP：15 分
- 阅读、点赞、在看等热度：5 分

修改评分规则或解释评分口径前，先读 `references/scoring.md`。

## 接口参考

修改请求字段、排查接口错误、解释扣费和翻页逻辑时，先读 `references/dajiala_kw_search.md`。

重要约束：

- 接口每页最多返回 20 条，按返回条数扣费。
- `kw`、`any_kw`、`ex_kw` 在接口侧是“且”的关系，条件过严容易没有结果。
- 脚本会在翻页请求之间等待，因为接口文档提到 `qps=1/2s`。
- 预计返回超过 60 条的付费运行，需要显式加 `--yes`。

## 报告规则

- 不要在聊天或报告里复制全文。
- 展示标题、公众号、日期、数据指标、评分、入选理由、原文链接和短摘录即可。
- 接口内容属于第三方材料。报告用于筛选和辅助阅读，不用于转载。
- 如果报告要分享，优先使用 `report.html`，并保留原文链接。

## 常见问题

- 缺少 key：设置 `DAJIALA_API_KEY`，或用 `--dry-run` 测试。
- 没有结果：放宽 `--kw`，减少严格的 `--any-kw`，改用 `--sort-type 2`，或增大 `--period`。
- 无关结果太多：增加 `--exclude-keywords`，减少 `--pages`，或把 `--topic-keywords` 写得更具体。
- 接口报错：用同一条命令重试；脚本已经会对临时错误最多重试三次。
