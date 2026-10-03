<h1 align="center">Smart Image Compressor</h1>

<p align="center">
  <strong>A modern, easy-to-use image compression tool built with PySide6 &amp; Pillow.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="license" />
  <img src="https://img.shields.io/badge/PySide6-6.6%2B-purple?style=for-the-badge&logo=qt&logoColor=white" alt="pyside6" />
  <img src="https://img.shields.io/badge/Pillow-10.0%2B-orange?style=for-the-badge" alt="pillow" />
</p>

<hr />

<h2>Screenshot</h2>

<p align="center">
  <img src="screenshots/preview.png" alt="Smart Image Compressor screenshot" width="820" />
</p>

<hr />

<h2>Features</h2>

<table>
  <thead>
    <tr>
      <th align="left">Feature</th>
      <th align="left">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🎨 <strong>Modern dark UI</strong></td>
      <td>Clean, minimal, easy on the eyes</td>
    </tr>
    <tr>
      <td>🖼️ <strong>Batch compression</strong></td>
      <td>Add single files, multiple files, or entire folders</td>
    </tr>
    <tr>
      <td>📁 <strong>Drag &amp; drop</strong></td>
      <td>Just drop files or folders onto the window</td>
    </tr>
    <tr>
      <td>🎯 <strong>Smart target size</strong></td>
      <td>Guaranteed output under a chosen max size (KB)</td>
    </tr>
    <tr>
      <td>🔀 <strong>Flexible formats</strong></td>
      <td>Keep Original / JPEG / PNG / WebP</td>
    </tr>
    <tr>
      <td>📉 <strong>Quality control</strong></td>
      <td>Manual quality slider or automatic tuning</td>
    </tr>
    <tr>
      <td>📂 <strong>Custom output</strong></td>
      <td>Save next to originals or to a chosen folder</td>
    </tr>
    <tr>
      <td>⚡ <strong>Non-blocking</strong></td>
      <td>Runs on a background thread — UI stays responsive</td>
    </tr>
    <tr>
      <td>🛑 <strong>Cancel anytime</strong></td>
      <td>Stop a running batch instantly</td>
    </tr>
    <tr>
      <td>🧠 <strong>Alpha-aware</strong></td>
      <td>RGBA images composited cleanly for JPEG (no black edges)</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Quick Start</h2>

<h3>1. Requirements</h3>

<ul>
  <li>Python <strong>3.9+</strong></li>
  <li><strong>PySide6</strong> &ge; 6.6</li>
  <li><strong>Pillow</strong> &ge; 10.0</li>
</ul>

<h3>2. Install</h3>

<pre><code>git clone https://github.com/ZvanTors/Smart-Image-Compressor.git
cd Smart-Image-Compressor
pip install -r requirements.txt</code></pre>

<h3>3. Run</h3>

<pre><code>python main.py</code></pre>

<hr />

<h2>How to Use</h2>

<ol>
  <li>Click <strong>Add Images</strong> or <strong>Add Folder</strong> — or just drag &amp; drop.</li>
  <li>Pick the <strong>output format</strong> (Keep Original / JPEG / PNG / WebP).</li>
  <li>Adjust the <strong>quality slider</strong> (ignored when "Limit output size" is on).</li>
  <li><em>(Optional)</em> Enable <strong>Limit output size</strong> and set a target in KB.</li>
  <li><em>(Optional)</em> Choose a custom <strong>output folder</strong>.</li>
  <li>Hit <strong>⚡ Compress</strong> — done.</li>
</ol>

<hr />

<h2>How "Max Size" Mode Works</h2>

<p>When a target size is set, SIC:</p>

<ol>
  <li>Encodes once at your chosen quality.</li>
  <li>If it's too big, <strong>binary-searches</strong> JPEG/WebP quality (7 iterations).</li>
  <li>If <em>still</em> too big, <strong>progressively downscales</strong> the image and retries.</li>
  <li>Keeps going until the file fits — or returns the smallest possible result.</li>
</ol>

<blockquote>
  <p>💡 <strong>Tip:</strong> For photos, <strong>WebP</strong> usually beats JPEG by 25–35% at the same visual quality.</p>
</blockquote>

<hr />

<h2>Build a Windows Executable</h2>

<pre><code>pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed ^
  --name "SmartImageCompressor" main.py</code></pre>

<p>The standalone executable lands at <code>dist/SmartImageCompressor.exe</code>.</p>

<hr />

<h2>Project Structure</h2>

<pre><code>Smart-Image-Compressor/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE              # MIT License
├── .gitignore
└── screenshots/
    └── preview.png</code></pre>

<hr />

<h2>Tech Stack</h2>

<ul>
  <li><a href="https://doc.qt.io/qtforpython/">PySide6</a> — Qt 6 bindings for Python (UI)</li>
  <li><a href="https://python-pillow.org/">Pillow</a> — image processing &amp; encoding</li>
</ul>

<hr />

<h2>License</h2>

<p>Released under the <strong>MIT License</strong> — see <a href="LICENSE">LICENSE</a>.</p>

<hr />

<p align="center">
  Made with ❤️ using <a href="https://doc.qt.io/qtforpython/">PySide6</a> &amp;
  <a href="https://python-pillow.org/">Pillow</a>
</p>