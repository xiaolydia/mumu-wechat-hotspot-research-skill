# 木木公众号热点研究 Skill

这是「AI 内容工厂」课程配套的 Codex Skill，用来通过大加拉公众号文章关键词搜索接口抓取热点文章，并生成按分数排序的 Markdown / HTML 报告。

本版本先写死为「公众号文章关键词搜索」接口，不包含视频号接口。

## 下载

直接下载 zip：

https://github.com/xiaolydia/mumu-wechat-hotspot-research-skill/raw/main/mumu-wechat-hotspot-research-skill.zip

## 安装

下载后，在终端进入 zip 所在目录，例如：

```zsh
cd ~/Downloads
```

解压到本地 skills 目录：

```zsh
mkdir -p ~/.agents/skills
unzip -o mumu-wechat-hotspot-research-skill.zip -d ~/.agents/skills
```

确认安装成功：

```zsh
ls ~/.agents/skills/mumu-wechat-hotspot-research/SKILL.md
```

然后重启 Codex，让新 Skill 生效。

## 配置 API Key

这个 Skill 需要大加拉 API Key。不要把 key 写进课程文档、GitHub、聊天记录或脚本里，推荐放到本机环境变量。

打开配置文件：

```zsh
nano ~/.zshrc
```

在文件最后加一行：

```zsh
export DAJIALA_API_KEY="你的大加拉key"
```

保存退出：

```text
control + O
回车
control + X
```

让配置立即生效：

```zsh
source ~/.zshrc
```

验证是否配置成功：

```zsh
echo ${DAJIALA_API_KEY:+已设置}
```

如果输出 `已设置`，就可以使用了。

## 使用方式

在 Codex 里可以这样说：

```text
使用 $mumu-wechat-hotspot-research 抓取 Codex 相关的 20 条公众号文章，并生成热点报告。
```

也可以换成自己的主题：

```text
使用 $mumu-wechat-hotspot-research 抓取 AI 内容工厂 相关的公众号热点文章，最近 30 天，最多 20 条。
```

## 输出文件

每次运行会生成一个带时间戳的目录，里面通常有：

- `report.md`：Markdown 版热点报告
- `report.html`：可分享的 HTML 报告
- `selected_articles.json`：入选文章结构化数据
- `scored_articles.json`：全部文章评分数据
- `run_meta.json`：运行参数、扣费和余额等信息

报告只保留标题、公众号、日期、数据指标、评分、短摘录和原文链接，不会复制全文，也不会保存 API Key。

## 注意事项

- 接口按返回条数扣费，第一次建议只抓 20 条以内。
- 如果没有结果，可以放宽关键词或把时间范围调大。
- 如果 key 不小心暴露，去大加拉后台重新生成一个新的。
- 本版本只支持公众号文章关键词搜索；视频号接口后续可以单独做新版本。
