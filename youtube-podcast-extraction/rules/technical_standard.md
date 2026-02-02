# YouTube 播客提取技术架构规范

## 1. 核心视觉标准 (Cinema Style Layout)

- **排布规则**：左对齐布局，英文金句（38px Italic）在上，中文翻译（28px Regular）在下。
- **视觉符号**：英文金句左侧必须带有 `5px` 宽的红色竖向装饰条。
- **蒙层设计**：底部 1/3 采用深色渐变蒙层 (`linear-gradient`)，确保文字可读性。
- **页脚规范**：左下角包含“红色药丸标签”+“视频标题”。

## 2. 技术架构标准 (Universal Pro Script)

- **脚本统一**：优先使用 `scripts/` 目录下的通用 Pro 脚本。
- **多任务支持**：支持通过命令行指定任意子目录进行处理。
- **智能识别**：自动检测视频、JSON 配置、时间戳格式，并根据目录名智能生成标签。
- **Base64 嵌入**：采用 Base64 编码将背景图嵌入 HTML 渲染流，解决路径加载冲突。

## 3. 流程可靠性标准 (Atomic Screenshot)

1. FFmpeg 提取原始帧（建议增加 `+0.5s` 偏移以避开转场黑屏）。
2. 保存为临时 JPG。
3. Playwright 渲染时，必须通过 `page.evaluate` 显式等待 Base64 背景图加载完成（`img.complete` 或 `img.onload`）。
4. 截取最终卡片并清理临时文件。

## 4. 关键脚本逻辑与文档回填

### A. 通用金句生成器 (`generate_quotes_pro.js`)

采用 Base64 渲染与电影感布局。

### B. 字幕重叠去重算法 (`clean_subs.py`)

针对 YouTube 自动字幕的增量单词特性，使用单词窗口滑动匹配。

### C. 分档提炼逻辑 (Tiered Extraction Logic)

- **短视频 (<10min)**：
  - 模式：结构化翻译。
  - 密度：80-100% 内容覆盖。
  - 金句：3-5 张。
- **中长视频 (10-30min)**：
  - 模式：高保真提炼。
  - 密度：约 60% 内容覆盖，保留关键论据。
  - 金句：6-10 张。
- **超长播客 (>30min)**：
  - 模式：章节化战略提炼。
  - 密度：约 40% 核心密度。
  - 金句：10-15 张。
- **衔接性**：各段之间需保持逻辑连贯，并使用 Markdown 二级/三级标题清晰界定。

### D. 文档回填规则 (Immediate Backfill)

- **即时性**：生成的金句图片 (`quote_n.jpg`) 必须紧跟在 Markdown 文档中对应的中英双语金句下方，严禁仅在文末做统一展示。
- **引用格式**：在 Markdown 中展示英文原文金句时，直接使用 `> ` 引用块。**严禁**带有 `**Quote:**` 或 `**译文：**` 等显式标签，保持文档简洁专业。
- **关联性**：金句图片必须与文字内容高度相关，确保图文互证。
- **整洁度**：回填后需删除文末冗余的“资产预览”章节。

## 5. 环境依赖与异常处理

- **环境检查**：`generate_quotes_pro.js` 会自动检测 `playwright-core`。若缺失，请手动执行：
  ```bash
  npm install playwright-core playwright && npx playwright install chromium
  ```
- **数据兼容性**：`quotes_list.json` 必须是数组格式或 `{ "quotes": [...] }` 包装格式。支持 `quote_en`/`quote_zh` 或 `en`/`zh` 字段。
- **鲁棒性处理**：渲染脚本已增加空值校验，防止因 JSON 字段缺失导致的 `undefined.replace` 崩溃。
