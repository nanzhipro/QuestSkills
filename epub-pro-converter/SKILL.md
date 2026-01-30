---
name: "epub-pro-converter"
description: "EPUB 高清转换专家。技术脚本生成出版级 PDF/MD，支持内置字体提取与高清排版重构。"
---

# EPUB Pro Converter

本技能是专为“出版级高清转换”打造的技术工具箱。它专注于从 EPUB 到 PDF 和 Markdown 的高质量物理转换，确保电子书在不同设备上都能获得最佳的视觉呈现。

## 核心能力

1. **出版级 PDF 重构 (Technical)**：应用 13pt 字号、1.5em 行高、2.5cm 边距等行业最佳实践。自动提取并子集化嵌入 EPUB 内置矢量字体，确保跨设备高清呈现。
2. **结构化 MD 提取 (Technical)**：精准还原电子书层级、图片引用及脚注，生成适用于 Obsidian/Logseq 等笔记系统的 Markdown 源文件。
3. **极致容错与安全**：采用 MD5 文件名哈希与路径隔离技术，完美处理超长路径及特殊字符，确保转换过程 100% 成功。

## 闭环工作流

1. **[技术转换]**：运行 `script/convert.py`。该阶段完成原始 EPUB 的解析、字体提取、PDF 渲染及 Markdown 同步。
2. **[质量自查]**：验证 PDF 页面完整性及 Markdown 图片引用的正确性。

## 目录结构

- `script/`: 核心转换脚本 `convert.py`。
- `reference/`: 出版排版规范 `typography_rules.md`。
- `tools/`: 依赖项定义 `requirements.txt`。

## 使用方法

运行脚本并按照提示输入 EPUB 路径：

```bash
python .trae/skills/epub-pro-converter/script/convert.py
```

或直接通过命令行参数传递：

```bash
python .trae/skills/epub-pro-converter/script/convert.py "path/to/book.epub"
```

## 适用场景

- 当用户要求“高质量”、“高清”、“专业排版”的 PDF 转换时。
- 当 EPUB 文件名包含特殊字符或路径极长时。
- 需要将电子书内容无损导入 Obsidian 等 Markdown 笔记工具时。
