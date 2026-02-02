# QuestSkills

QuestSkills 由 nanzhi 维护，目标是分享提供 100 个日常工具技能。
当前已覆盖「微信公众号文章抓取」、「小宇宙播客转写」、「YouTube 播客提取与可视化」、「专业书籍萃取」与「EPUB 高清转换」五类内容生产场景。

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
npx skills add nanzhipro/QuestSkills --skill youtube-podcast-extraction
npx skills add nanzhipro/QuestSkills --skill book-content-extractor
npx skills add nanzhipro/QuestSkills --skill epub-pro-converter
```

## 技能总览

| Skill                          | 主要用途                                                      | 典型输入       | 产出                                                                   | 子页面                                              |
| ------------------------------ | ------------------------------------------------------------- | -------------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| wechat-article-fetcher         | 将公众号文章转为结构化 Markdown，下载图片并可推送摘要到 flomo | 公众号文章链接 | 终端输出的 Markdown + 本地 images/                                     | [SKILL.md](wechat-article-fetcher/SKILL.md)         |
| xiaoyuzhou-podcast-transcriber | 下载并转写小宇宙播客单集，生成原文、结构化全文与精简摘要      | 小宇宙单集链接 | transcript_raw.txt / podcast_full_structured.md / podcast_optimized.md | [SKILL.md](xiaoyuzhou-podcast-transcriber/SKILL.md) |
| youtube-podcast-extraction     | 将 YouTube 播客提炼为字幕、分析与金句卡片                    | YouTube 链接   | transcript_en.txt / transcript_zh.md / pyramid_analysis_zh.md / quotes/ / publish_content.md | [SKILL.md](youtube-podcast-extraction/SKILL.md)     |
| book-content-extractor         | 深度萃取书籍 50% 核心内容，构建费曼讲解主线                   | 书籍全文 (MD)  | 核心萃取笔记 (Markdown)                                                | [SKILL.md](book-content-extractor/SKILL.md)         |
| epub-pro-converter             | EPUB 高清转换为出版级 PDF 或结构化 Markdown                   | EPUB 文件      | 高清 PDF / 结构化 Markdown                                             | [SKILL.md](epub-pro-converter/SKILL.md)             |
