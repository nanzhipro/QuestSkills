---
name: document-privacy-audit
description: 针对指定 PDF 或 Office 文档（.pdf/.docx/.xlsx/.pptx）进行全文解析、检索与深度理解，识别并汇总隐私/敏感信息（PII、金融、健康、账号凭据等），输出审计报告与风险提示。用于合规审查、数据脱敏准备、外发前检查或隐私扫描。
---

# Document Privacy Audit

## 概览
执行全文抽取与结构化检索，结合规则与语义判断定位隐私信息，输出带定位与风险等级的汇总报告。

## 工作流程

1. 明确范围与交付
- 确认文件路径与格式、语言、是否包含扫描页。
- 明确隐私范围（仅 PII，还是包含财务/健康/凭据）。
- 约定输出格式（Markdown 报告 + JSON 明细，或仅报告）。

2. 抽取全文并保留定位
- 优先使用 `scripts/extract_text.py` 输出 JSONL，保留页码/段落/单元格定位。
- PDF 如无文本层，提示使用 OCR（`ocrmypdf` 或 `tesseract`）后再抽取。

示例：
```bash
python scripts/extract_text.py --input /path/to/file.pdf --output /path/to/extracted.jsonl
python scripts/extract_text.py --input /path/to/file.docx --output /path/to/extracted.jsonl
```

3. 全文检索与结构化理解
- 对抽取结果做关键词检索（`rg` 或自定义脚本），保留命中位置。
- 归纳文档结构与主题，为隐私判断提供上下文（例如表格是名单/账单/病历）。

4. 识别隐私信息
- 使用 `scripts/pii_scan.py` 做规则扫描，生成候选清单。
- 结合上下文进行语义复核，剔除明显误报并补充漏报。
- 分类与分级请参考 `references/pii_catalog.md`。

示例：
```bash
python scripts/pii_scan.py --input /path/to/extracted.jsonl --output /path/to/pii_report.json
```

5. 汇总输出
- 输出审计摘要、发现明细、风险等级与建议。
- 所有示例必须脱敏展示，保留定位信息以便复核。

## 输出模板

```markdown
# 隐私审计报告
- 文件: <path>
- 扫描范围: <PII/财务/健康/凭据>
- 扫描时间: <YYYY-MM-DD>
- 结论: <低/中/高风险 + 1-2 句说明>

## 发现摘要
| 类别 | 数量 | 示例(脱敏) | 位置 |
| --- | --- | --- | --- |
| 邮箱 | 3 | a***@example.com | page:2, page:5 |
| 手机 | 2 | 13******45 | page:3 |

## 高风险项
- <类别 + 脱敏示例 + 位置 + 风险原因>

## 细项清单
- <类别> | <脱敏示例> | <位置> | <上下文简述>

## 建议
- <脱敏/删除/分级访问/加密存储等>
```

## 资源

### scripts/
- `extract_text.py`: 统一抽取 PDF/Office 文本并保留定位。
- `pii_scan.py`: 规则扫描隐私信息并生成 JSON 报告。

### references/
- `pii_catalog.md`: 隐私类别、风险等级与脱敏示例。
