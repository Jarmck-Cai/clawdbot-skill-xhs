# clawdbot-skill-xhs

[English](README.md) | 简体中文

一个 OpenClaw Skill：把小红书（Xiaohongshu / 小红书 / RED）的分享链接归档为清晰的 **笔记 + 媒体 + 元数据** 结构，并支持可选的 Gemini 视频理解分析。

> 备注：OpenClaw 之前曾使用过 **Clawdbot** 这一名称（以及更早期的 **moltbot** 等）。

## 功能特性

- 提取标题 / 描述 / 标签 / 评论（如果可获取）
- 下载视频与图片到本地
- 保存原始元数据 JSON，便于长期引用与复现
- 可选：Gemini 视频理解（摘要 / 要点 / 转写 / 视觉要点）
- 可移植：不硬编码路径；输出目录完全由环境变量配置

## 环境要求

- Python 3.9+（推荐 Python 3.10+）
- Playwright（Chromium）
- 用户提供：已登录的小红书 Cookie
- 可选：Gemini API Key（用于视频分析）

## 安装

```bash
pip install playwright requests google-generativeai
playwright install chromium
```

## 配置

**提示**：你可以创建一个名为 `.env` 的文件（建议放在 `skills/xhs/` 目录），写入以下变量，并在使用前运行 `source skills/xhs/.env`。

**工作目录**：以下命令默认在“能看到 `skills/xhs/` 的目录”执行（即 `ls skills/xhs` 能成功）。

### 1) 提供小红书 Cookie（必需）

```bash
export XHS_COOKIE="your_cookie_string_here"
```

### 2) 输出目录（可选）

默认输出到 `./xhs_captures/`。

```bash
export XHS_OUTPUT_DIR="./xhs_captures"
```

进阶（笔记与媒体分开存放）：

```bash
export XHS_NOTES_DIR="./xhs_captures/notes"
export XHS_MEDIA_DIR="./xhs_captures/media"
```

### 3) 启用视频分析（可选）

```bash
export GEMINI_API_KEY="your_gemini_api_key"
```

## 使用方法

### 提取（Extract）

```bash
python3 skills/xhs/scripts/xhs_bridge.py "https://www.xiaohongshu.com/discovery/item/..."
```

该命令会在当前工作目录写入 `xhs_last_run.json`。

### 归档（Archive）

```bash
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json
```

### 归档 + 视频分析（Gemini）

```bash
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json --analyze
# 或者更高质量
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json --analyze pro
```

## 安全 / 隐私

- 请不要提交 Cookie、API Key 或任何抓取到的媒体文件。
- 详见 `SECURITY.md`。

## 合规声明 / 免责声明

本项目主要用于**学习与研究**。它使用了非官方方式（例如浏览器自动化与用户自行提供 Cookie）来获取内容，且**与小红书/RED 官方无任何关联**。

使用本项目即表示你同意：
- **风险自担（at your own risk）**；
- 遵守小红书/RED 的服务条款与当地法律法规；
- 不要滥用（高频访问、规模化采集、对服务造成压力等）；
- 不要分享/提交任何敏感信息（Cookie、API Key、个人数据等）。

作者与贡献者**不提供任何担保**，也不对因误用导致的封号、限制访问或其他损失承担责任。

## 许可证

MIT（见 `LICENSE`）。
