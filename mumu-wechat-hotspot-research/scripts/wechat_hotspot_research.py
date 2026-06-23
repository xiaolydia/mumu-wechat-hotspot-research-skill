#!/usr/bin/env python3
"""抓取微信公众号文章搜索结果，完成评分并生成报告。"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://www.dajiala.com/fbmain/monitor/v3/kw_search"

SCENE_TERMS = [
    "实战",
    "实践",
    "落地",
    "案例",
    "复盘",
    "流程",
    "步骤",
    "教程",
    "手把手",
    "项目",
    "生产环境",
    "踩坑",
    "经验",
    "部署",
    "接入",
    "搭建",
]

NEW_TECH_TERMS = [
    "2026",
    "2025",
    "最新",
    "新版本",
    "发布",
    "升级",
    "API",
    "SDK",
    "MCP",
    "Agent",
    "智能体",
    "workflow",
    "工作流",
    "自动化",
    "插件",
    "工具调用",
    "上下文",
]

ASSET_TERMS = [
    "代码",
    "脚本",
    "模板",
    "清单",
    "SOP",
    "Prompt",
    "提示词",
    "开源",
    "GitHub",
    "配置",
    "命令",
    "参数",
    "可复制",
    "实操",
]

PROFILE_DEFAULTS = {
    "claude-agent-skills": {
        "kw": ["Agent Skill", "Claude Code Skill", "Codex Skill"],
        "any_kw": "Claude Codex MCP Agent 工作流 实战 教程",
        "ex_kw": "英语 游戏 招聘 教培 课程招生 职业技能",
        "topic": "Claude Agent Skills / Codex Skills 技术实践",
        "topic_keywords": "Claude Agent Skills,Claude Code Skill,Codex Skill,Agent Skill,MCP,subagent,workflow,Skill 开发,智能体工作流",
        "min_score": 70,
    }
}

SAMPLE_ARTICLES = [
    {
        "title": "我用 Claude Code Skill 搭了一条公众号素材自动化流水线",
        "url": "https://mp.weixin.qq.com/s/example-claude-skill-1",
        "short_link": "https://mp.weixin.qq.com/s/example-claude-skill-1",
        "content": "这是一篇虚拟样例。作者从真实内容生产场景出发，记录如何设计 Skill、调用 MCP、沉淀 SOP，并给出脚本配置、踩坑复盘和可复制 Prompt。",
        "avatar": "",
        "publish_time": int(time.time()) - 86400,
        "publish_time_str": "2026-06-22",
        "update_time": int(time.time()) - 86400,
        "update_time_str": "2026-06-22",
        "wx_name": "AI 内容工厂样例号",
        "wx_id": "sample_ai_factory",
        "ghid": "gh_sample_1",
        "read": 32100,
        "praise": 410,
        "looking": 97,
        "ip_wording": "上海",
        "classify": "科技",
        "is_original": 1,
        "item_show_type": 0,
        "has_notifier": 0,
    },
    {
        "title": "Agent Skill 到底是什么：从概念到第一个可运行 Skill",
        "url": "https://mp.weixin.qq.com/s/example-agent-skill-2",
        "short_link": "https://mp.weixin.qq.com/s/example-agent-skill-2",
        "content": "这是一篇虚拟样例。文章包含概念解释、文件结构、SKILL.md 写法、脚本资源设计和一个最小可用 Demo，适合开发者入门。",
        "avatar": "",
        "publish_time": int(time.time()) - 172800,
        "publish_time_str": "2026-06-21",
        "update_time": int(time.time()) - 172800,
        "update_time_str": "2026-06-21",
        "wx_name": "智能体实验室样例号",
        "wx_id": "sample_agent_lab",
        "ghid": "gh_sample_2",
        "read": 8800,
        "praise": 160,
        "looking": 42,
        "ip_wording": "北京",
        "classify": "科技",
        "is_original": 1,
        "item_show_type": 0,
        "has_notifier": 0,
    },
    {
        "title": "英语 skill 训练营：30 天提升职场表达",
        "url": "https://mp.weixin.qq.com/s/example-excluded-3",
        "short_link": "https://mp.weixin.qq.com/s/example-excluded-3",
        "content": "这是一篇虚拟样例。文章介绍英语学习技能课程和招生信息，和 Agent Skill 技术实践无关。",
        "avatar": "",
        "publish_time": int(time.time()) - 259200,
        "publish_time_str": "2026-06-20",
        "update_time": int(time.time()) - 259200,
        "update_time_str": "2026-06-20",
        "wx_name": "学习样例号",
        "wx_id": "sample_learning",
        "ghid": "gh_sample_3",
        "read": 56000,
        "praise": 300,
        "looking": 90,
        "ip_wording": "广东",
        "classify": "教育",
        "is_original": 0,
        "item_show_type": 0,
        "has_notifier": 0,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用大加拉关键词接口搜索微信公众号文章，并生成按分数排序的热点报告。",
        add_help=False,
        usage="%(prog)s [选项]",
    )
    options = parser.add_argument_group("选项")
    options.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
    options.add_argument("--profile", choices=sorted(PROFILE_DEFAULTS), help="使用内置搜索和评分配置。")
    options.add_argument("--kw", action="append", help="搜索关键词。需要多个关键词时重复传入这个参数。")
    options.add_argument("--any-kw", default="", help="文章需要包含这些词中的任意一个。")
    options.add_argument("--ex-kw", default="", help="文章不能包含这些词。")
    options.add_argument("--topic", default="", help="报告里展示的人类可读主题名称。")
    options.add_argument("--topic-keywords", default="", help="用于相关性评分的关键词，用逗号或空格分隔。")
    options.add_argument("--exclude-keywords", default="", help="用于排除弱相关结果的关键词，用逗号或空格分隔。")
    options.add_argument("--sort-type", type=int, default=1, choices=[1, 2], help="1=按阅读数排序，2=按时间排序。默认：1。")
    options.add_argument("--mode", type=int, default=3, choices=[1, 2, 3], help="1=搜标题，2=搜正文，3=搜标题和正文。")
    options.add_argument("--period", type=int, default=7, help="搜索最近多少天。请遵守接口对不同搜索模式的时间限制。")
    options.add_argument("--pages", type=int, default=1, help="每个关键词抓取多少页。每页最多返回 20 条付费结果。")
    options.add_argument("--max-results", type=int, default=30, help="去重后最多保留多少篇文章。")
    options.add_argument("--min-score", type=int, default=70, help="报告中展示文章的最低分。")
    options.add_argument("--output-dir", default="wechat-hotspot-output", help="运行产物保存目录。")
    options.add_argument("--api-key", default="", help="接口密钥。优先使用 DAJIALA_API_KEY 环境变量。")
    options.add_argument("--base-url", default=API_URL, help="覆盖默认接口地址。")
    options.add_argument("--interval", type=float, default=2.1, help="两次接口请求之间的等待秒数。接口文档提到 qps=1/2s。")
    options.add_argument("--timeout", type=float, default=20, help="HTTP 请求超时时间，单位秒。")
    options.add_argument("--dry-run", action="store_true", help="使用内置样例数据，不调用真实接口。")
    options.add_argument("--yes", action="store_true", help="确认执行预计成本较高的运行。")
    return parser.parse_args()


def apply_profile_defaults(args: argparse.Namespace) -> argparse.Namespace:
    if not args.profile:
        return args
    defaults = PROFILE_DEFAULTS[args.profile]
    for key, value in defaults.items():
        current = getattr(args, key.replace("-", "_"), None)
        if current in (None, "", []) or (key == "min_score" and current == 70):
            setattr(args, key.replace("-", "_"), value)
    return args


def split_terms(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        chunks = value
    else:
        chunks = [value]
    terms: list[str] = []
    for chunk in chunks:
        for term in re.split(r"[,，、;\n\t ]+", chunk or ""):
            term = term.strip()
            if term and term not in terms:
                terms.append(term)
    return terms


def strip_html(raw: Any) -> str:
    text = "" if raw is None else str(raw)
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def safe_slug(value: str, fallback: str = "report") -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.lower()).strip("-")
    return value[:60] or fallback


def timestamp_to_date(value: Any, fallback: str = "") -> str:
    if fallback:
        return str(fallback)
    try:
        ts = int(value)
        if ts > 10_000_000_000:
            ts = ts // 1000
        return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def request_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "wechat-hotspot-research/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_with_retries(url: str, payload: dict[str, Any], timeout: float, retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            result = request_json(url, payload, timeout)
            if result.get("message") == "Internal Server Error":
                raise RuntimeError("Internal Server Error")
            return result
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"接口请求重试 {retries} 次后仍失败：{last_error}")


def normalize_article(item: dict[str, Any], query: str) -> dict[str, Any]:
    content_text = strip_html(item.get("content", ""))
    title = strip_html(item.get("title", ""))
    url = str(item.get("url") or item.get("short_link") or "")
    return {
        "query": query,
        "title": title,
        "url": url,
        "short_link": item.get("short_link", ""),
        "content_text": content_text,
        "excerpt": content_text[:220],
        "avatar": item.get("avatar", ""),
        "publish_time": item.get("publish_time", ""),
        "publish_date": timestamp_to_date(item.get("publish_time"), item.get("publish_time_str", "")),
        "update_time": item.get("update_time", ""),
        "update_date": timestamp_to_date(item.get("update_time"), item.get("update_time_str", "")),
        "wx_name": item.get("wx_name", ""),
        "wx_id": item.get("wx_id", ""),
        "ghid": item.get("ghid", ""),
        "read": to_int(item.get("read")),
        "praise": to_int(item.get("praise")),
        "looking": to_int(item.get("looking")),
        "ip_wording": item.get("ip_wording", ""),
        "classify": item.get("classify", ""),
        "is_original": item.get("is_original", ""),
        "item_show_type": item.get("item_show_type", ""),
        "has_notifier": item.get("has_notifier", ""),
    }


def to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def deduplicate(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for article in articles:
        key = article.get("url") or f"{article.get('title')}|{article.get('wx_name')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


def count_matches(text: str, terms: list[str]) -> list[str]:
    text_lower = text.lower()
    matches = []
    for term in terms:
        if term.lower() in text_lower:
            matches.append(term)
    return matches


def scaled_score(matches: list[str], target_count: int, max_score: int) -> int:
    if not matches:
        return 0
    return min(max_score, round(max_score * min(1.0, len(set(matches)) / max(1, target_count))))


def popularity_score(read: int, praise: int, looking: int) -> int:
    read_score = 0
    if read >= 100_000:
        read_score = 5
    elif read >= 50_000:
        read_score = 4
    elif read >= 10_000:
        read_score = 3
    elif read >= 5_000:
        read_score = 2
    elif read >= 1_000:
        read_score = 1
    engagement = 0
    if read > 0:
        engagement = min(2, math.floor(((praise + looking * 2) / read) * 100))
    return min(5, read_score + engagement)


def score_article(
    article: dict[str, Any],
    topic_terms: list[str],
    exclude_terms: list[str],
) -> dict[str, Any]:
    title = article["title"]
    content = article["content_text"]
    full_text = f"{title} {content}"

    title_topic_matches = count_matches(title, topic_terms)
    content_topic_matches = count_matches(content, topic_terms)
    topic_weight = len(set(title_topic_matches)) * 2 + len(set(content_topic_matches))
    topic_target = max(3, math.ceil(len(topic_terms) * 0.55)) if topic_terms else 1
    topic_relevance = min(35, round(35 * min(1.0, topic_weight / topic_target))) if topic_terms else 20

    scene_matches = count_matches(full_text, SCENE_TERMS)
    new_matches = count_matches(full_text, NEW_TECH_TERMS)
    asset_matches = count_matches(full_text, ASSET_TERMS)
    excluded_matches = count_matches(full_text, exclude_terms)

    scene_score = scaled_score(scene_matches, 5, 25)
    new_score = scaled_score(new_matches, 5, 20)
    asset_score = scaled_score(asset_matches, 4, 15)
    heat_score = popularity_score(article["read"], article["praise"], article["looking"])

    score = topic_relevance + scene_score + new_score + asset_score + heat_score
    if excluded_matches:
        score = max(0, score - 30)

    reasons = []
    if title_topic_matches or content_topic_matches:
        reasons.append(f"主题命中：{', '.join((title_topic_matches + content_topic_matches)[:6])}")
    if scene_matches:
        reasons.append(f"落地信号：{', '.join(scene_matches[:5])}")
    if new_matches:
        reasons.append(f"技术实践信号：{', '.join(new_matches[:5])}")
    if asset_matches:
        reasons.append(f"可复用资产信号：{', '.join(asset_matches[:5])}")
    if heat_score:
        reasons.append(f"热度信号：阅读 {article['read']} / 点赞 {article['praise']} / 在看 {article['looking']}")
    if excluded_matches:
        reasons.append(f"排除词命中：{', '.join(excluded_matches[:5])}")

    result = dict(article)
    result["score"] = int(score)
    result["grade"] = grade(score)
    result["score_breakdown"] = {
        "topic_relevance": topic_relevance,
        "landing_scene": scene_score,
        "new_practice": new_score,
        "reusable_assets": asset_score,
        "popularity": heat_score,
        "excluded_penalty": -30 if excluded_matches else 0,
    }
    result["excluded"] = bool(excluded_matches)
    result["matched_terms"] = {
        "topic": sorted(set(title_topic_matches + content_topic_matches)),
        "scene": sorted(set(scene_matches)),
        "new_practice": sorted(set(new_matches)),
        "assets": sorted(set(asset_matches)),
        "excluded": sorted(set(excluded_matches)),
    }
    result["reasons"] = reasons or ["未发现明显主题/落地/技术实践信号"]
    return result


def grade(score: int) -> str:
    if score >= 85:
        return "S"
    if score >= 75:
        return "A"
    if score >= 65:
        return "B"
    return "C"


def collect_articles(args: argparse.Namespace, api_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_responses: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []

    if args.dry_run:
        response = {
            "code": 0,
            "msg": "样例运行",
            "cost_money": 0,
            "remain_money": None,
            "total": len(SAMPLE_ARTICLES),
            "total_page": 1,
            "page": 1,
            "data_number": len(SAMPLE_ARTICLES),
            "data": SAMPLE_ARTICLES,
        }
        raw_responses.append(response)
        normalized.extend(normalize_article(item, "样例运行") for item in SAMPLE_ARTICLES)
        return normalized, raw_responses

    for query in args.kw:
        for page in range(1, args.pages + 1):
            payload = {
                "kw": query,
                "sort_type": args.sort_type,
                "mode": args.mode,
                "period": args.period,
                "page": page,
                "key": api_key,
                "any_kw": args.any_kw,
                "ex_kw": args.ex_kw,
            }
            response = fetch_with_retries(args.base_url, payload, args.timeout)
            safe_response = dict(response)
            safe_response["request"] = {k: v for k, v in payload.items() if k != "key"}
            raw_responses.append(safe_response)

            if response.get("code") not in (0, "0", None) and response.get("msg"):
                print(f"警告：关键词={query!r} 页码={page} 返回 {response.get('code')}：{response.get('msg')}", file=sys.stderr)

            for item in response.get("data", []) or []:
                normalized.append(normalize_article(item, query))

            if page < args.pages:
                time.sleep(args.interval)

    return normalized, raw_responses


def build_markdown(meta: dict[str, Any], selected: list[dict[str, Any]], scored: list[dict[str, Any]]) -> str:
    lines = [
        f"# {meta['topic']} 公众号热点报告",
        "",
        f"- 生成时间：{meta['generated_at']}",
        f"- 查询关键词：{', '.join(meta['keywords'])}",
        f"- 抓取文章：{meta['article_count']} 篇，入选：{len(selected)} 篇，最低展示分：{meta['min_score']}",
        f"- 模式：{'内置样例' if meta['dry_run'] else '大加拉接口'}",
        "",
        "> 报告只展示摘要和短摘录，不复制全文。完整原文请打开对应链接阅读。",
        "",
        "## 入选文章",
        "",
    ]

    if not selected:
        lines.extend(["未发现达到阈值的文章。可以放宽关键词、降低最低分，或改用按时间排序。", ""])
    else:
        for index, article in enumerate(selected, 1):
            breakdown = article["score_breakdown"]
            lines.extend(
                [
                    f"### {index}. [{article['title']}]({article['url']})",
                    "",
                    f"- 等级/评分：{article['grade']} / {article['score']}",
                    f"- 公众号：{article['wx_name']} | 发布时间：{article['publish_date']} | 阅读：{article['read']} | 点赞：{article['praise']} | 在看：{article['looking']}",
                    f"- 分项：主题 {breakdown['topic_relevance']}，落地 {breakdown['landing_scene']}，技术实践 {breakdown['new_practice']}，资产 {breakdown['reusable_assets']}，热度 {breakdown['popularity']}",
                    f"- 入选理由：{'；'.join(article['reasons'][:4])}",
                    f"- 摘要摘录：{article['excerpt']}",
                    "",
                ]
            )

    lines.extend(["## 全量评分表", "", "| 分数 | 等级 | 标题 | 公众号 | 日期 | 排除 |", "|---:|:---:|---|---|---|:---:|"])
    for article in scored:
        title = article["title"].replace("|", "\\|")
        lines.append(
            f"| {article['score']} | {article['grade']} | [{title}]({article['url']}) | {article['wx_name']} | {article['publish_date']} | {'是' if article['excluded'] else '否'} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_html(meta: dict[str, Any], selected: list[dict[str, Any]], scored: list[dict[str, Any]]) -> str:
    cards = []
    for article in selected:
        breakdown = article["score_breakdown"]
        reason = "；".join(article["reasons"][:4])
        cards.append(
            f"""
            <article class="card grade-{html.escape(article['grade'].lower())}">
              <div class="card-top">
                <span class="grade">{html.escape(article['grade'])}</span>
                <span class="score">{article['score']}</span>
              </div>
              <h2><a href="{html.escape(article['url'])}" target="_blank" rel="noopener noreferrer">{html.escape(article['title'])}</a></h2>
              <p class="meta">{html.escape(str(article['wx_name']))} · {html.escape(str(article['publish_date']))} · 阅读 {article['read']} · 点赞 {article['praise']} · 在看 {article['looking']}</p>
              <p class="excerpt">{html.escape(article['excerpt'])}</p>
              <p class="reason">{html.escape(reason)}</p>
              <div class="bars">
                {bar('主题', breakdown['topic_relevance'], 35)}
                {bar('落地', breakdown['landing_scene'], 25)}
                {bar('技术', breakdown['new_practice'], 20)}
                {bar('资产', breakdown['reusable_assets'], 15)}
                {bar('热度', breakdown['popularity'], 5)}
              </div>
            </article>
            """
        )

    table_rows = []
    for article in scored:
        table_rows.append(
            f"""
            <tr>
              <td>{article['score']}</td>
              <td><span class="mini-grade">{html.escape(article['grade'])}</span></td>
              <td><a href="{html.escape(article['url'])}" target="_blank" rel="noopener noreferrer">{html.escape(article['title'])}</a></td>
              <td>{html.escape(str(article['wx_name']))}</td>
              <td>{html.escape(str(article['publish_date']))}</td>
              <td>{'是' if article['excluded'] else '否'}</td>
            </tr>
            """
        )

    empty = "<p class='empty'>未发现达到阈值的文章。可以放宽关键词、降低最低分，或改用按时间排序。</p>" if not selected else ""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(meta['topic'])} 公众号热点报告</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #161a1d;
      --muted: #667085;
      --line: #d9dee3;
      --paper: #f7f8f5;
      --panel: #ffffff;
      --green: #1f7a55;
      --blue: #2b67c6;
      --amber: #b7791f;
      --red: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.55;
    }}
    header {{
      padding: 40px 6vw 24px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }}
    main {{ padding: 28px 6vw 56px; }}
    h1 {{
      margin: 0 0 12px;
      font-size: clamp(28px, 4vw, 52px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .sub {{ max-width: 980px; color: var(--muted); font-size: 15px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-top: 26px;
      max-width: 980px;
    }}
    .stat {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .stat strong {{ display: block; font-size: 28px; line-height: 1.1; }}
    .stat span {{ color: var(--muted); font-size: 13px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      align-items: start;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-top: 5px solid var(--blue);
      border-radius: 8px;
      padding: 18px;
      min-height: 280px;
    }}
    .grade-s {{ border-top-color: var(--green); }}
    .grade-a {{ border-top-color: var(--blue); }}
    .grade-b {{ border-top-color: var(--amber); }}
    .grade-c {{ border-top-color: var(--red); }}
    .card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    .grade, .mini-grade {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: var(--ink);
      color: #fff;
      font-weight: 700;
    }}
    .mini-grade {{ width: 26px; height: 26px; font-size: 12px; }}
    .score {{ font-size: 34px; font-weight: 760; }}
    h2 {{ margin: 0 0 10px; font-size: 20px; line-height: 1.28; letter-spacing: 0; }}
    a {{ color: inherit; text-decoration-color: rgba(43, 103, 198, .45); text-underline-offset: 3px; }}
    .meta, .excerpt, .reason {{ margin: 10px 0; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .excerpt {{ font-size: 14px; }}
    .reason {{
      border-left: 3px solid var(--line);
      padding-left: 10px;
      color: #344054;
      font-size: 14px;
    }}
    .bars {{ margin-top: 14px; display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: 48px 1fr 36px; gap: 8px; align-items: center; font-size: 12px; color: var(--muted); }}
    .track {{ height: 8px; background: #eef1f4; border-radius: 999px; overflow: hidden; }}
    .fill {{ height: 100%; background: var(--blue); border-radius: 999px; }}
    section {{ margin-top: 34px; }}
    section h2 {{ font-size: 24px; }}
    .empty {{ background: #fff; border: 1px dashed var(--line); border-radius: 8px; padding: 18px; color: var(--muted); }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: #fff; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #f2f4f1; font-size: 13px; color: #475467; }}
    td:first-child {{ font-weight: 700; }}
    footer {{ color: var(--muted); font-size: 12px; padding: 0 6vw 32px; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(meta['topic'])}<br>公众号热点报告</h1>
    <p class="sub">关键词：{html.escape(', '.join(meta['keywords']))}。生成时间：{html.escape(meta['generated_at'])}。报告只展示摘要和短摘录，不复制全文。</p>
    <div class="stats">
      <div class="stat"><strong>{meta['article_count']}</strong><span>抓取文章</span></div>
      <div class="stat"><strong>{len(selected)}</strong><span>入选文章</span></div>
      <div class="stat"><strong>{meta['min_score']}+</strong><span>展示阈值</span></div>
      <div class="stat"><strong>{'样例' if meta['dry_run'] else '接口'}</strong><span>运行模式</span></div>
    </div>
  </header>
  <main>
    <section>
      <h2>入选文章</h2>
      {empty}
      <div class="grid">{''.join(cards)}</div>
    </section>
    <section>
      <h2>全量评分表</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>分数</th><th>等级</th><th>标题</th><th>公众号</th><th>日期</th><th>排除</th></tr></thead>
          <tbody>{''.join(table_rows)}</tbody>
        </table>
      </div>
    </section>
  </main>
  <footer>由公众号热点研究 Skill 生成。API Key 不会写入输出文件。</footer>
</body>
</html>
"""


def bar(label: str, value: int, total: int) -> str:
    width = 0 if total <= 0 else min(100, round(value / total * 100))
    return f"""<div class="bar"><span>{html.escape(label)}</span><div class="track"><div class="fill" style="width:{width}%"></div></div><span>{value}/{total}</span></div>"""


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = apply_profile_defaults(parse_args())
    if not args.kw:
        print("错误：请提供 --kw，或使用 --profile claude-agent-skills。", file=sys.stderr)
        return 2

    args.kw = args.kw[:]
    estimated_rows = len(args.kw) * args.pages * 20
    if estimated_rows > 60 and not args.yes:
        print(
            f"预计最多返回 {estimated_rows} 条付费结果，未提供 --yes，已停止运行。请降低 --pages/--kw，或确认后传入 --yes。",
            file=sys.stderr,
        )
        return 2

    api_key = args.api_key or os.getenv("DAJIALA_API_KEY", "")
    if not args.dry_run and not api_key:
        print("错误：请设置 DAJIALA_API_KEY，或传入 --api-key。也可以用 --dry-run 在不调用接口的情况下测试流程。", file=sys.stderr)
        return 2

    if args.api_key:
        print("警告：建议优先使用 DAJIALA_API_KEY 环境变量，避免 key 进入 shell 历史记录。", file=sys.stderr)

    topic_terms = split_terms(args.topic_keywords) or split_terms(args.kw + [args.any_kw])
    exclude_terms = split_terms(args.exclude_keywords) + split_terms(args.ex_kw)

    run_stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    topic = args.topic or " / ".join(args.kw)
    run_dir = Path(args.output_dir).expanduser().resolve() / f"{run_stamp}-{safe_slug(topic)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    articles, raw_responses = collect_articles(args, api_key)
    unique_articles = deduplicate(articles)[: args.max_results]
    scored = [score_article(article, topic_terms, exclude_terms) for article in unique_articles]
    scored.sort(key=lambda item: item["score"], reverse=True)
    selected = [
        item
        for item in scored
        if item["score"] >= args.min_score
        and not item["excluded"]
        and (item["score_breakdown"]["topic_relevance"] >= 12 or not topic_terms)
    ]

    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta = {
        "generated_at": generated_at,
        "topic": topic,
        "keywords": args.kw,
        "any_kw": args.any_kw,
        "ex_kw": args.ex_kw,
        "topic_keywords": topic_terms,
        "exclude_keywords": exclude_terms,
        "sort_type": args.sort_type,
        "mode": args.mode,
        "period": args.period,
        "pages": args.pages,
        "max_results": args.max_results,
        "min_score": args.min_score,
        "article_count": len(unique_articles),
        "selected_count": len(selected),
        "dry_run": args.dry_run,
        "cost_money": sum(float(item.get("cost_money") or 0) for item in raw_responses),
        "remain_money": next((item.get("remain_money") for item in reversed(raw_responses) if item.get("remain_money") is not None), None),
    }

    write_json(run_dir / "run_meta.json", meta)
    write_json(run_dir / "raw_responses.json", raw_responses)
    write_json(run_dir / "scored_articles.json", scored)
    write_json(run_dir / "selected_articles.json", selected)
    (run_dir / "report.md").write_text(build_markdown(meta, selected, scored), encoding="utf-8")
    (run_dir / "report.html").write_text(build_html(meta, selected, scored), encoding="utf-8")

    print(f"运行目录：{run_dir}")
    print(f"已评分文章数：{len(scored)}")
    print(f"入选文章数：{len(selected)}")
    print(f"Markdown 报告：{run_dir / 'report.md'}")
    print(f"HTML 报告：{run_dir / 'report.html'}")
    if not args.dry_run:
        print(f"接口返回扣费：{meta['cost_money']}")
        print(f"最后一次响应返回余额：{meta['remain_money']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
