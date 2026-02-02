---
name: youtube-podcast-extraction
description: 极客级 YouTube 播客提取与可视化方案。遵循电影感字幕视觉标准 (Cinema Style)，通过词窗重叠算法去重字幕，并利用 Playwright 渲染高质量金句卡片。适用于需要将长视频转化为高价值社交分享内容的场景。
---

# 工作流程 (Optimized SOP v2.0)

本 Skill 采用四阶段 SOP 流程，确保从原始视频到高阶可视化成果的自动化交付。

## 📍 阶段 1：数据准备 (Data Prep)

1. 使用 `yt-dlp` 获取视频标题并创建任务目录。
2. 下载英文 VTT 字幕，调用 `clean_subs.py` 执行单词窗口滑动去重，生成 `transcript_en.txt` 和 `timestamp_map.json`。3. 下载视频文件保存为 `video.mp4`。
   - **可靠性技巧**：优先使用 `-f 18` 或 `-f "best[height<=720][ext=mp4]"` 以确保极速下载且无需合并流程。

## 📍 阶段 2：深度分析 (Deep Analysis)

1. **多档处理策略**：根据视频长度自动调整提炼密度：
   - **短视频 (<10min)**：执行原文结构化翻译，保留完整逻辑骨架。
   - **中长视频 (10-30min)**：执行约 60% 的高保真核心提炼，平衡细节与效率。
   - **超长播客 (>30min)**：执行约 40% 的章节化深度提炼，聚焦战略级洞见。
2. 生成核心提炼文档 `transcript_zh.md`。
   - **金句规范**：关键金句部分需保留中英双语原文。
3. 执行金字塔原理分析，生成 `pyramid_analysis_zh.md`。
4. **关键任务**：从分析中提炼 5-7 个核心金句，确保英文部分与字幕原文逐字一致，存入 `quotes_list.json`。

## 📍 阶段 3：资产生成 (Asset Generation)

1. 调用 `generate_quotes_pro.js` 进行渲染。
2. **自动化逻辑**：FFmpeg 根据精准时间戳提取原始帧 -> Playwright 加载电影感 HTML 模板 -> Base64 嵌入背景图 -> **显式等待图像加载完成 (Wait for Load)** -> 渲染保存为 `quotes/quote_n.jpg`。
   - **技术细节**：在 FFmpeg 提取时增加 `+0.5s` 偏移以避开潜在的转场黑屏，并确保截图与字幕内容高度同步。

## 📍 阶段 4：成果交付 (Final Delivery)

1. 将生成的金句卡片引用回填至 `pyramid_analysis_zh.md` 和 `transcript_zh.md`。
2. 生成多平台发布文案 `publish_content.md`（含知乎、小红书、Twitter 适配版）。
3. 清理 VTT 等中间临时文件。

# 视觉标准 (Cinema Style)

- **设计规范**：严格遵循 `visual_standard.md` 定义的视觉准则。
- **排版要求**：左对齐布局，英文 (38px Italic) 在上，中文 (28px Regular) 在下，左侧配 5px 红色装饰条。
- **蒙层设计**：底部 1/3 深色渐变蒙层，页脚包含红色药丸标签 + 视频标题。

# 技术规范

- **去重逻辑**：必须使用词窗重叠算法，严禁简单的行去重。
- **渲染引擎**：严禁使用 ImageMagick 处理文字，必须通过 Playwright 流程渲染以保证字体质感。
- **定位精度**：使用专门的时间戳查找脚本精准定位金句位置。
- **输出约束**：所有输出文件（.md, .html, .txt）严禁使用 Emoji，确保专业度。

# 产出清单

- `transcript_en.txt` / `timestamp_map.json` (清洗后的文本与映射)
- `transcript_zh.md` (中英对照深度翻译)
- `pyramid_analysis_zh.md` (含金句卡片嵌入的深度分析)
- `quotes/` (包含最终美化图及 index.md)
- `publish_content.md` (多平台分发文案)

# 参考资料

- 架构规范详见 [technical_standard.md](file:///Users/cyberserval/TEDxNashville/.trae/skills/youtube-podcast-extraction/rules/technical_standard.md)
- 视觉规范详见 [visual_standard.md](file:///Users/cyberserval/TEDxNashville/.trae/skills/youtube-podcast-extraction/rules/visual_standard.md)
- 执行指南详见 [sop_standard.md](file:///Users/cyberserval/TEDxNashville/.trae/skills/youtube-podcast-extraction/rules/sop_standard.md)
