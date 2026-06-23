# 大加拉关键词搜索接口

修改抓取脚本或排查接口问题时读取本文件。

## 接口地址

`POST https://www.dajiala.com/fbmain/monitor/v3/kw_search`

这个接口从大加拉数据库中搜索微信公众号文章，不保证和微信客户端实时搜索结果完全一致。

## 请求体

```json
{
  "kw": "AI Agent",
  "sort_type": 1,
  "mode": 3,
  "period": 7,
  "page": 1,
  "key": "从 DAJIALA_API_KEY 读取",
  "any_kw": "实战 案例",
  "ex_kw": "招聘 英语"
}
```

字段说明：

- `kw`：主关键词。接口要求 `kw`、`any_kw`、`ex_kw` 至少提交一个；本 skill 通常使用 `kw`。
- `any_kw`：文章需要满足其中任意一个词。
- `ex_kw`：文章不能包含这些词。
- `sort_type`：`1` 按阅读数排序，`2` 按时间排序。
- `mode`：`1` 搜标题，`2` 搜正文，`3` 搜标题和正文。
- `period`：搜索最近多少天。接口文档说明：标题搜索支持更长时间范围，正文搜索时间范围较短。
- `page`：页码。每页最多 20 条。
- `key`：接口密钥。始终从 `DAJIALA_API_KEY` 或密钥管理工具读取。

注意：接口会把 `kw`、`any_kw`、`ex_kw` 当成“且”的关系组合。三个条件都很严格时，可能没有结果。

## 脚本使用的响应字段

- `code`、`msg`
- `cost_money`、`remain_money`
- `total`、`total_page`、`page`、`data_number`
- `data[].title`
- `data[].url`、`data[].short_link`
- `data[].content`
- `data[].publish_time`、`data[].publish_time_str`
- `data[].wx_name`、`data[].wx_id`、`data[].ghid`
- `data[].read`、`data[].praise`、`data[].looking`
- `data[].classify`、`data[].is_original`

## 成本保护

接口按返回条数扣费。除非用户明确要求扩大范围，优先使用：

- `--pages 1`
- `--max-results 30`
- `--period 7`
- `--sort-type 1` 查热门，`--sort-type 2` 查最新

脚本会拒绝预计超过 60 条的付费运行，除非显式传入 `--yes`。

## 错误处理

- 临时网络错误重试 1-3 次。
- 遇到 `{"message":"Internal Server Error"}` 时重试。
- 没有返回数据时，放宽关键词或减少 `any_kw`/`ex_kw` 的限制。
- 不要打印或持久化 API Key。
