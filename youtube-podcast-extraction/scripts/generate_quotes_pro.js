/**
 * 🚀 通用金句生成专业脚本 (generate_quotes_pro.js)
 * 
 * 功能：
 * 1. 自动识别目录下的视频和金句列表。
 * 2. 从视频中截取金句瞬间并渲染为精美双语卡片。
 * 3. 支持命令行指定工作目录：node generate_quotes_pro.js [目录路径]
 * 
 * 依赖：node, playwright-core, ffmpeg
 */

let chromium;
try {
    const playwright = require('playwright-core');
    chromium = playwright.chromium;
} catch (e) {
    console.error(`\n❌ 缺失依赖: 'playwright-core' 未安装。`);
    console.log(`请运行以下命令进行安装：\nnpm install playwright-core playwright && npx playwright install chromium\n`);
    process.exit(1);
}

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// --- 通用配置处理 ---
const targetDir = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();
const QUOTES_DIR = path.join(targetDir, 'quotes');
const VIDEO_PATH = path.join(targetDir, 'video.mp4');
const QUOTES_JSON = path.join(targetDir, 'quotes_list.json');

// 自动检测标签（优先使用目录名，或自定义）
const dirName = path.basename(targetDir);
const defaultTag = dirName.includes('Lex_Fridman') ? 'Lex Fridman' : 'TEDxNashville';
const videoTitle = dirName.replace(/_/g, ' ');

// HTML/CSS 模板
const HTML_TEMPLATE = (bgImageUrl, quoteEn, quoteZh, tag, title, timestamp) => `
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0; padding: 0; width: 1280px; height: 720px;
            background: #000;
            font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
            overflow: hidden;
        }
        .card {
            position: relative; width: 1280px; height: 720px;
            display: flex; flex-direction: column; justify-content: flex-end;
        }
        .background {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background-image: url('${bgImageUrl}'); background-size: cover; background-position: center;
            z-index: 1;
            filter: brightness(0.6);
        }
        .overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.8) 100%);
            z-index: 2;
        }
        .content {
            position: relative; z-index: 3; padding: 0 80px 140px 80px;
            display: flex; flex-direction: column; align-items: flex-start;
        }
        .quote-en-box {
            display: flex; align-items: flex-start; margin-bottom: 20px;
        }
        .accent-bar {
            width: 5px; align-self: stretch; background: #ff4d4f; margin-right: 20px;
            box-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
        }
        .quote-en {
            font-size: 38px; font-weight: 700; line-height: 1.3; color: white;
            font-style: italic; text-shadow: 0 2px 10px rgba(0,0,0,0.8);
            max-width: 1000px;
        }
        .quote-zh {
            font-size: 28px; font-weight: 400; line-height: 1.5; color: white;
            padding-left: 25px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);
            max-width: 1000px;
        }
        .footer {
            position: absolute; bottom: 50px; left: 80px; z-index: 4;
            display: flex; align-items: center; gap: 15px;
            width: calc(100% - 160px);
        }
        .tag-pill {
            background: #ff4d4f; color: white; padding: 4px 10px; border-radius: 3px;
            font-weight: 800; font-size: 14px; text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .video-title {
            color: white; font-size: 16px; font-weight: 400; opacity: 0.9;
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="background"></div>
        <div class="overlay"></div>
        <div class="content">
            <div class="quote-en-box">
                <div class="accent-bar"></div>
                <div class="quote-en">${quoteEn}</div>
            </div>
            <div class="quote-zh">${quoteZh}</div>
        </div>
        <div class="footer">
            <span class="tag-pill">${tag}</span>
            <span class="video-title">${title}</span>
        </div>
    </div>
</body>
</html>
`;

function timeToSeconds(ts) {
    if (!ts) return 0;
    // 支持 HH:MM:SS.mmm 或 MM:SS.mmm 格式
    const [timePart, msPart] = ts.split('.');
    const parts = timePart.split(':');
    let h = 0, m = 0, s = 0;
    
    if (parts.length === 3) {
        h = parseInt(parts[0]);
        m = parseInt(parts[1]);
        s = parseInt(parts[2]);
    } else if (parts.length === 2) {
        m = parseInt(parts[0]);
        s = parseInt(parts[1]);
    }
    
    let totalSeconds = h * 3600 + m * 60 + s;
    if (msPart) {
        totalSeconds += parseFloat(`0.${msPart}`);
    }
    return totalSeconds;
}

async function run() {
    console.log(`🎬 启动通用金句生成引擎...`);
    console.log(`📂 工作目录: ${targetDir}`);

    if (!fs.existsSync(QUOTES_JSON)) {
        console.error(`❌ 错误: 在目录中找不到 quotes_list.json`);
        return;
    }
    if (!fs.existsSync(VIDEO_PATH)) {
        console.error(`❌ 错误: 在目录中找不到 video.mp4`);
        return;
    }

    let quotesData = JSON.parse(fs.readFileSync(QUOTES_JSON, 'utf8'));
    // 鲁棒性支持：支持对象包装或数组直接导出
    const quotes = Array.isArray(quotesData) ? quotesData : (quotesData.quotes || []);
    
    if (quotes.length === 0) {
        console.error(`❌ 错误: 金句列表为空，请检查 quotes_list.json 格式`);
        return;
    }

    if (!fs.existsSync(QUOTES_DIR)) {
        fs.mkdirSync(QUOTES_DIR, { recursive: true });
    }

    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 720 });

    for (let i = 0; i < quotes.length; i++) {
        const q = quotes[i];
        const id = q.id || `quote_${i + 1}`;
        const ts = q.time || q.timestamp || "00:00:00";
        const zh = q.quote_zh || q.zh || q.text_zh || "";
        const en = q.quote_en || q.en || q.text_en || "";

        const jpgPath = path.join(QUOTES_DIR, id.toString().includes('quote') ? `${id}.jpg` : `quote_${id}.jpg`);
        const tempPath = path.join(QUOTES_DIR, `temp_raw_${id}.jpg`);
        
        console.log(`📸 正在处理 [${id}] @ ${ts}...`);
        
        // 1. FFmpeg 截图
        const sec = timeToSeconds(ts); // 移除之前的 0.5s 偏移，精准匹配 JSON 中的时间点
        try {
            execSync(`ffmpeg -y -ss ${sec} -i "${VIDEO_PATH}" -vframes 1 -q:v 2 "${tempPath}"`, { stdio: 'ignore' });
        } catch (e) {
            console.warn(`⚠️ 截图失败: ${id}`);
            continue;
        }

        // 2. 渲染卡片
        const base64Image = fs.readFileSync(tempPath).toString('base64');
        const bgImageUrl = `data:image/jpeg;base64,${base64Image}`;
        
        // 增加对引号的转义处理，防止破坏 HTML/CSS 结构
        const escapeHtml = (str) => str.replace(/[&<>"']/g, (m) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;'
        }[m]));

        const html = HTML_TEMPLATE(
            bgImageUrl, 
            escapeHtml(en), 
            escapeHtml(zh), 
            defaultTag, 
            videoTitle,
            ts
        );
        
        await page.setContent(html);
        
        // 关键修正：确保背景图已加载完成再截图
        await page.evaluate(async () => {
            const bg = document.querySelector('.background');
            if (bg) {
                const style = window.getComputedStyle(bg);
                const url = style.backgroundImage.slice(4, -1).replace(/"/g, "");
                if (url.startsWith('data:')) {
                    const img = new Image();
                    img.src = url;
                    await new Promise(r => {
                        if (img.complete) r();
                        else img.onload = r;
                    });
                }
            }
        });
        
        await page.waitForTimeout(500); // 额外留一点渲染缓冲
        
        // 3. 保存
        await page.screenshot({ path: jpgPath, type: 'jpeg', quality: 95 });
        
        if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
        console.log(`✅ 已生成: ${path.basename(jpgPath)}`);
    }

    await browser.close();
    console.log(`\n✨ 任务完成！金句已保存在: ${QUOTES_DIR}`);
}

run().catch(console.error);
