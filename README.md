# QuestSkills

QuestSkills 由 nanzhi 维护，目标是分享提供 100 个日常工具技能。
当前已覆盖「微信公众号文章抓取」与「小宇宙播客转写」两类内容生产场景。

## 导航

- [技能总览](#技能总览)
- [通过 npx skills 安装](#通过-npx-skills-安装)

## 通过 npx skills 安装

### 安装全部技能

```bash
npx skills add nanzhipro/QuestSkills
```

### 仅安装单个技能

```bash
npx skills add nanzhipro/QuestSkills --skill wechat-article-fetcher
npx skills add nanzhipro/QuestSkills --skill xiaoyuzhou-podcast-transcriber
```

## 技能总览

| Skill                          | 主要用途                                                      | 典型输入       | 产出                                                                   | 子页面                                              |
| ------------------------------ | ------------------------------------------------------------- | -------------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| wechat-article-fetcher         | 将公众号文章转为结构化 Markdown，下载图片并可推送摘要到 flomo | 公众号文章链接 | 终端输出的 Markdown + 本地 images/                                     | [SKILL.md](wechat-article-fetcher/SKILL.md)         |
| xiaoyuzhou-podcast-transcriber | 下载并转写小宇宙播客单集，生成原文、结构化全文与精简摘要      | 小宇宙单集链接 | transcript_raw.txt / podcast_full_structured.md / podcast_optimized.md | [SKILL.md](xiaoyuzhou-podcast-transcriber/SKILL.md) |
