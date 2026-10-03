<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Smart Image Compressor (SIC)</title>
<meta name="description" content="A modern image compression tool built with PySide6 and Pillow." />
<style>
  :root {
    --bg: #1e1e2e;
    --bg-2: #252537;
    --border: #313244;
    --text: #cdd6f4;
    --muted: #9399b2;
    --accent: #89b4fa;
    --accent-2: #cba6f7;
    --green: #a6e3a1;
    --yellow: #f9e2af;
    --red: #f38ba8;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .container {
    max-width: 880px;
    margin: 0 auto;
    padding: 48px 24px 96px;
  }

  header.hero {
    text-align: center;
    padding: 32px 0 40px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
  }
  .logo {
    display: inline-block;
    background: linear-gradient(135deg, #89b4fa 0%, #cba6f7 100%);
    color: #11111b;
    font-weight: 800;
    font-size: 22px;
    padding: 10px 18px;
    border-radius: 14px;
    letter-spacing: 1px;
    margin-bottom: 20px;
  }
  h1 {
    font-size: 2.2rem;
    margin: 8px 0 12px;
    color: #f5f5ff;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  .subtitle {
    color: var(--muted);
    font-size: 1.05rem;
    margin: 0 0 24px;
  }
  .badges {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
  }
  .badge {
    display: inline-block;
    background: var(--bg-2);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 999px;
  }
  .badge.green  { color: var(--green);  border-color: #2f4436; }
  .badge.blue   { color: var(--accent); border-color: #2c3a55; }
  .badge.purple { color: var(--accent-2); border-color: #40304a; }

  h2 {
    font-size: 1.4rem;
    color: #f5f5ff;
    margin-top: 44px;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    font-weight: 700;
  }
  h3 {
    font-size: 1.08rem;
    color: #f5f5ff;
    margin-top: 26px;
    margin-bottom: 8px;
  }
  p { margin: 10px 0; }

  ul, ol { padding-left: 22px; margin: 10px 0; }
  li { margin: 6px 0; }

  code {
    background: #181825;
    color: #f5e0dc;
    padding: 2px 7px;
    border-radius: 6px;
    font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
    font-size: 0.88em;
    border: 1px solid var(--border);
  }
  pre {
    background: #181825;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    overflow-x: auto;
    line-height: 1.55;
    font-size: 0.88rem;
  }
  pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: #cdd6f4;
  }

  .features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px;
    margin: 16px 0;
  }
  .feature {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 0.95rem;
  }
  .feature .emoji { margin-right: 6px; }

  .callout {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 16px 0;
    color: var(--text);
  }
  .callout.tip { border-left-color: var(--green); }
  .callout.warn { border-left-color: var(--yellow); }

  .screenshot {
    width: 100%;
    border-radius: 12px;
    border: 1px solid var(--border);
    margin: 16px 0;
    display: block;
  }
  .screenshot-placeholder {
    background: var(--bg-2);
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 60px 20px;
    text-align: center;
    color: var(--muted);
    font-size: 0.9rem;
    margin: 16px 0;
  }

  footer {
    margin-top: 64px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--muted);
    font-size: 0.88rem;
  }

  @media (max-width: 600px) {
    h1 { font-size: 1.7rem; }
    .container { padding: 24px 16px 64px; }
    pre { font-size: 0.82rem; padding: 12px; }
  }
</style>
</head>
<body>
<div class="container">

  <header class="hero">
    <div class="logo">SIC</div>
    <h1>Smart Image Compressor</h1>
    <p class="subtitle">A modern, easy-to-use image compression tool built with PySide6 and Pillow.</p>
    <div class="badges">
      <span class="badge blue">version 1.0.0</span>
      <span class="badge green">python 3.9+</span>
      <span class="badge purple">license MIT</span>
      <span class="badge">PySide6</span>
      <span class="badge">Pillow</span>
    </div>
  </header>

  <section>
    <h2>Features</h2>
    <div class="features">
      <div class="feature"><span class="emoji">🎨</span> Clean, modern, dark-themed UI</div>
      <div class="feature"><span class="emoji">🖼️</span> Batch compression — single, multiple, or whole folders</div>
      <div class="feature"><span class="emoji">📁</span> Drag &amp; drop support</div>
      <div class="feature"><span class="emoji">🎯</span> Smart target-size algorithm</div>
      <div class="feature"><span class="emoji">🔀</span> Output format: Keep Original / JPEG / PNG / WebP</div>
      <div class="feature"><span class="emoji">📉</span> Optional maximum output size (in KB)</div>
      <div class="feature"><span class="emoji">📂</span> Custom or automatic output folder</div>
      <div class="feature"><span class="emoji">⚡</span> Multi-threaded — UI never freezes</div>
      <div class="feature"><span class="emoji">🛑</span> Cancel running jobs at any time</div>
      <div class="feature"><span class="emoji">🧠</span> Alpha-aware JPEG handling (no black artifacts)</div>
    </div>
  </section>

  <section>
    <h2>Screenshot</h2>
    <img class="screenshot" src="screenshots/preview.png" alt="Smart Image Compressor screenshot"
         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
    <div class="screenshot-placeholder" style="display:none;">
      Add your screenshot at <code>screenshots/preview.png</code>
    </div>
  </section>

  <section>
    <h2>Requirements</h2>
    <ul>
      <li>Python 3.9 or newer</li>
      <li>PySide6 &gt;= 6.6</li>
      <li>Pillow &gt;= 10.0</li>
    </ul>
  </section>

  <section>
    <h2>Installation</h2>
<pre><code>git clone https://github.com/ZvanTors/Smart-Image-Compressor.git
cd Smart-Image-Compressor
pip install -r requirements.txt</code></pre>
  </section>

  <section>
    <h2>Usage</h2>
<pre><code>python main.py</code></pre>
    <ol>
      <li>Click <strong>Add Images</strong> or <strong>Add Folder</strong> (or drag &amp; drop files/folders).</li>
      <li>Choose the output format and quality.</li>
      <li>(Optional) Enable <strong>Limit output size</strong> and set a target in KB.</li>
      <li>(Optional) Choose a custom output folder.</li>
      <li>Hit <strong>Compress</strong> — done!</li>
    </ol>
  </section>

  <section>
    <h2>How the &ldquo;max size&rdquo; mode works</h2>
    <p>When a target size is set, SIC:</p>
    <ol>
      <li>Tries the original quality.</li>
      <li>If too big, binary-searches JPEG/WebP quality (7 iterations).</li>
      <li>If still too big, progressively downscales the image and repeats.</li>
      <li>Guarantees the result is under the target size, unless physically impossible.</li>
    </ol>
    <div class="callout tip">
      <strong>Tip:</strong> For the smallest possible files without quality loss on photos,
      choose <em>WebP</em> — it typically beats JPEG by 25–35% at the same visual quality.
    </div>
  </section>

  <section>
    <h2>Building a Windows executable</h2>
<pre><code>pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed ^
  --name "SmartImageCompressor" main.py</code></pre>
    <p>The standalone executable will be created at <code>dist/SmartImageCompressor.exe</code>.</p>
  </section>

  <section>
    <h2>Project structure</h2>
<pre><code>Smart-Image-Compressor/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.html          # This page
├── LICENSE              # MIT License
├── .gitignore
└── screenshots/
    └── preview.png</code></pre>
  </section>

  <section>
    <h2>License</h2>
    <p>Released under the <a href="LICENSE">MIT License</a>.</p>
  </section>

  <footer>
    Made with ❤️ using PySide6 &amp; Pillow &nbsp;·&nbsp; © 2025 Your Name
  </footer>

</div>
</body>
</html>