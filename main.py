# -*- coding: utf-8 -*-
"""
Smart Image Compressor (SIC)
A modern, easy-to-use image compression tool.
Built with PySide6 + Pillow.
"""

from __future__ import annotations

import io
import os
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from PIL import Image

from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot
from PySide6.QtGui import (
    QIcon, QColor, QFont, QPixmap, QPainter, QBrush, QPen,
    QLinearGradient, QGuiApplication
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QSpinBox, QCheckBox,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QMessageBox, QAbstractItemView, QSizePolicy
)


# ------------------------------------------------------------------ metadata
APP_NAME = "Smart Image Compressor"
APP_SHORT = "SIC"
APP_VERSION = "1.0.0"

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9.1
    RESAMPLE = Image.LANCZOS


# ------------------------------------------------------------------ helpers
def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    v = n / 1024.0
    for unit in ("KB", "MB", "GB", "TB"):
        if v < 1024:
            return f"{v:.1f} {unit}"
        v /= 1024.0
    return f"{v:.1f} PB"


def open_in_explorer(path: Path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def make_app_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0.0, QColor("#89b4fa"))
    grad.setColorAt(1.0, QColor("#cba6f7"))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 14, 14)
    p.setPen(QPen(QColor("#11111b"), 3))
    f = QFont("Segoe UI", 20, QFont.Bold)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "SIC")
    p.end()
    return QIcon(pm)


# ------------------------------------------------------------------ core logic
@dataclass
class Settings:
    fmt: str            # 'ORIGINAL' | 'JPEG' | 'PNG' | 'WEBP'
    quality: int        # 1..100 (ceiling when max_size_kb is set)
    max_size_kb: int    # 0 = no limit
    out_dir: Optional[Path]


@dataclass
class ImageJob:
    path: Path
    orig_size: int
    status: str = "Pending"
    new_size: int = 0
    out_path: Optional[Path] = None


def resolve_format(src: Path, fmt: str):
    if fmt == "ORIGINAL":
        ext = src.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            return "JPEG", ".jpg"
        if ext == ".png":
            return "PNG", ".png"
        if ext == ".webp":
            return "WEBP", ".webp"
        # fallback for bmp/tiff/gif -> jpeg
        return "JPEG", ".jpg"
    return {"JPEG": ("JPEG", ".jpg"),
            "PNG":  ("PNG",  ".png"),
            "WEBP": ("WEBP", ".webp")}[fmt]


def resolve_output_path(src: Path, out_dir: Optional[Path], ext: str) -> Path:
    folder = Path(out_dir) if out_dir else src.parent
    candidate = folder / f"{src.stem}_compressed{ext}"
    # Never overwrite the source file
    if candidate.resolve() == src.resolve():
        candidate = folder / f"{src.stem}_compressed_1{ext}"
    return candidate


def prepare_mode(img: Image.Image, fmt: str) -> Image.Image:
    """Ensure pixel mode is compatible with the target format."""
    if fmt == "JPEG":
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
    elif fmt == "WEBP":
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
    elif fmt == "PNG":
        if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
            img = img.convert("RGBA")
    return img


def encode(img: Image.Image, fmt: str, quality: int) -> bytes:
    buf = io.BytesIO()
    q = max(1, min(100, int(quality)))
    if fmt == "JPEG":
        img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    elif fmt == "WEBP":
        img.save(buf, "WEBP", quality=q, method=6)
    elif fmt == "PNG":
        # map quality -> compress_level (100 -> 0 fast/big, 1 -> 9 slow/small)
        cl = max(0, min(9, int((100 - q) / 11)))
        img.save(buf, "PNG", optimize=True, compress_level=cl)
    else:
        img.save(buf, fmt)
    return buf.getvalue()


def _best_under(img: Image.Image, fmt: str, quality_ceiling: int,
                max_bytes: int) -> Optional[bytes]:
    """Binary-search the quality so the file fits under max_bytes."""
    lo, hi = 10, max(10, quality_ceiling)
    best: Optional[bytes] = None
    while lo <= hi:
        mid = (lo + hi) // 2
        data = encode(img, fmt, mid)
        if len(data) <= max_bytes:
            best = data
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def encode_to_target(img: Image.Image, fmt: str, quality_ceiling: int,
                     max_bytes: int) -> bytes:
    # 1) Try at the user's chosen quality
    data = encode(img, fmt, quality_ceiling)
    if len(data) <= max_bytes:
        return data

    # 2) Binary-search quality on the original resolution
    data = _best_under(img, fmt, quality_ceiling, max_bytes)
    if data is not None:
        return data

    # 3) Progressively downscale and retry
    scale = 0.90
    work = img
    best: Optional[bytes] = None
    for _ in range(14):
        w = max(1, int(img.width * scale))
        h = max(1, int(img.height * scale))
        if w < 16 or h < 16:
            break
        work = img.resize((w, h), RESAMPLE)
        data = _best_under(work, fmt, quality_ceiling, max_bytes)
        if data is not None:
            return data
        scale *= 0.85

    # 4) Give up gracefully: smallest we can do
    return encode(work, fmt, 10)


def process_one(src: Path, s: Settings) -> int:
    pil_fmt, ext = resolve_format(src, s.fmt)
    out_path = resolve_output_path(src, s.out_dir, ext)

    img = Image.open(src)
    try:
        img.load()
    except Exception:
        # Fall back to first frame for multi-frame files
        img.seek(0)
    img = prepare_mode(img, pil_fmt)

    if s.max_size_kb and s.max_size_kb > 0:
        data = encode_to_target(img, pil_fmt, s.quality, s.max_size_kb * 1024)
    else:
        data = encode(img, pil_fmt, s.quality)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return len(data)


# ------------------------------------------------------------------ worker
class CompressWorker(QObject):
    progress = Signal(int, int, str)          # current, total, filename
    file_done = Signal(int, bool, int, str)   # index, ok, new_size, error
    finished = Signal(int, int)               # ok_count, fail_count

    def __init__(self, jobs: List[ImageJob], settings: Settings):
        super().__init__()
        self.jobs = jobs
        self.settings = settings
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    @Slot()
    def run(self) -> None:
        total = len(self.jobs)
        ok = 0
        fail = 0
        for i, job in enumerate(self.jobs):
            if self._cancel:
                break
            self.progress.emit(i, total, job.path.name)
            try:
                size = process_one(job.path, self.settings)
                ok += 1
                self.file_done.emit(i, True, size, "")
            except Exception as e:  # noqa: BLE001
                fail += 1
                self.file_done.emit(i, False, 0, str(e))
        self.progress.emit(total, total, "")
        self.finished.emit(ok, fail)


# ------------------------------------------------------------------ stylesheet
STYLE = """
* {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #cdd6f4;
}
#Central { background: #1e1e2e; }

#Header {
    background: #252537;
    border: 1px solid #313244;
    border-radius: 12px;
}
#Logo {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #89b4fa, stop:1 #cba6f7);
    color: #11111b;
    font-weight: 800;
    font-size: 14px;
    border-radius: 9px;
    padding: 6px 10px;
}
#Title { font-size: 16px; font-weight: 700; color: #f5f5ff; }
#Version {
    color: #9399b2;
    font-size: 11px;
    background: #313244;
    border-radius: 9px;
    padding: 3px 9px;
    font-weight: 600;
}
#Card {
    background: #252537;
    border: 1px solid #313244;
    border-radius: 12px;
}
#SectionLabel {
    color: #9399b2;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
#Hint { color: #6c7086; font-size: 11px; }
#Summary { color: #9399b2; font-size: 12px; }

QPushButton {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 7px 14px;
    color: #cdd6f4;
    font-weight: 600;
}
QPushButton:hover { background: #45475a; border-color: #585b70; }
QPushButton:pressed { background: #585b70; }
QPushButton:disabled { color: #6c7086; background: #252537; border-color: #313244; }

QPushButton#Primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #74c7ec);
    color: #11111b;
    border: none;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 800;
}
QPushButton#Primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a3c9ff, stop:1 #8ed6f7);
}
QPushButton#Primary:disabled { background: #313244; color: #6c7086; }

QPushButton#Danger {
    background: #3a2530;
    border: 1px solid #4a2f3a;
    color: #f38ba8;
}
QPushButton#Danger:hover { background: #4a2f3a; }

QTableWidget {
    background: transparent;
    border: none;
    gridline-color: transparent;
    selection-background-color: #313244;
    selection-color: #f5f5ff;
    outline: none;
}
QTableWidget::item { padding: 7px 8px; border-bottom: 1px solid #2a2a3d; }
QHeaderView::section {
    background: #252537;
    color: #9399b2;
    border: none;
    border-bottom: 1px solid #313244;
    padding: 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QComboBox {
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
}
QComboBox:hover { border-color: #585b70; }
QComboBox:focus { border-color: #89b4fa; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9399b2;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background: #252537;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
    selection-color: #f5f5ff;
    outline: none;
    padding: 4px;
}

QSlider::groove:horizontal {
    height: 4px; background: #313244; border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #74c7ec);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #cdd6f4; width: 14px; margin: -6px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #89b4fa; }
QSlider:disabled::sub-page:horizontal { background: #45475a; }
QSlider:disabled::handle:horizontal { background: #585b70; }

QSpinBox, QLineEdit {
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}
QSpinBox:focus, QLineEdit:focus { border-color: #89b4fa; }
QSpinBox:disabled, QLineEdit:disabled { color: #6c7086; background: #252537; }
QSpinBox::up-button, QSpinBox::down-button { width: 0; border: none; }

QCheckBox { spacing: 8px; color: #cdd6f4; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 5px;
    border: 1px solid #45475a;
    background: #1e1e2e;
}
QCheckBox::indicator:hover { border-color: #585b70; }
QCheckBox::indicator:checked {
    background: #89b4fa;
    border-color: #89b4fa;
}

QProgressBar {
    background: #313244;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #cba6f7);
    border-radius: 6px;
}

QScrollBar:vertical {
    background: transparent; width: 10px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


# ------------------------------------------------------------------ main window
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  •  v{APP_VERSION}")
        self.setWindowIcon(make_app_icon())
        self.resize(1180, 720)
        self.setMinimumSize(940, 580)
        self.setAcceptDrops(True)

        self.jobs: List[ImageJob] = []
        self.worker: Optional[CompressWorker] = None
        self.thread: Optional[QThread] = None

        self._build_ui()
        self.setStyleSheet(STYLE)
        self._update_summary()

    # ---------------------------------------------------------- UI building
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(self._build_left_panel(), 1)
        body.addWidget(self._build_right_panel(), 0)
        root.addLayout(body, 1)

        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        lay = QHBoxLayout(header)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        logo = QLabel(APP_SHORT)
        logo.setObjectName("Logo")
        title = QLabel(APP_NAME)
        title.setObjectName("Title")
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Version")

        lay.addWidget(logo)
        lay.addWidget(title)
        lay.addWidget(version)
        lay.addStretch(1)

        self.btn_add_files = QPushButton("＋  Add Images")
        self.btn_add_folder = QPushButton("📁  Add Folder")
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setObjectName("Danger")
        self.btn_clear = QPushButton("Clear")

        self.btn_add_files.clicked.connect(self._on_add_files)
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        self.btn_remove.clicked.connect(self._on_remove_selected)
        self.btn_clear.clicked.connect(self._on_clear)

        lay.addWidget(self.btn_add_files)
        lay.addWidget(self.btn_add_folder)
        lay.addWidget(self.btn_remove)
        lay.addWidget(self.btn_clear)
        return header

    def _build_left_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        top = QHBoxLayout()
        lbl = QLabel("IMAGES")
        lbl.setObjectName("SectionLabel")
        top.addWidget(lbl)
        top.addStretch(1)
        self.lbl_summary = QLabel("0 files")
        self.lbl_summary.setObjectName("Summary")
        top.addWidget(self.lbl_summary)
        lay.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["FILE", "ORIGINAL", "COMPRESSED", "STATUS"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setHighlightSections(False)

        lay.addWidget(self.table, 1)
        return card

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setFixedWidth(330)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(18)

        # ---- Output format
        f_lbl = QLabel("OUTPUT FORMAT")
        f_lbl.setObjectName("SectionLabel")
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["Keep Original", "JPEG", "PNG", "WebP"])
        self.cmb_format.currentIndexChanged.connect(self._on_format_changed)
        lay.addWidget(f_lbl)
        lay.addWidget(self.cmb_format)

        # ---- Quality
        q_row = QHBoxLayout()
        q_lbl = QLabel("QUALITY")
        q_lbl.setObjectName("SectionLabel")
        self.lbl_quality_val = QLabel("85")
        self.lbl_quality_val.setObjectName("Summary")
        q_row.addWidget(q_lbl)
        q_row.addStretch(1)
        q_row.addWidget(self.lbl_quality_val)
        lay.addLayout(q_row)

        self.slider_quality = QSlider(Qt.Horizontal)
        self.slider_quality.setRange(1, 100)
        self.slider_quality.setValue(85)
        self.slider_quality.valueChanged.connect(
            lambda v: self.lbl_quality_val.setText(str(v))
        )
        lay.addWidget(self.slider_quality)

        # ---- Max size
        self.chk_max = QCheckBox("Limit output size")
        self.chk_max.toggled.connect(self._on_max_toggled)
        lay.addWidget(self.chk_max)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(5, 200000)
        self.spin_max.setValue(500)
        self.spin_max.setSuffix("  KB")
        self.spin_max.setEnabled(False)
        row.addWidget(self.spin_max, 1)
        lay.addLayout(row)

        # ---- Output folder
        o_lbl = QLabel("OUTPUT FOLDER")
        o_lbl.setObjectName("SectionLabel")
        lay.addWidget(o_lbl)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.txt_out = QLineEdit()
        self.txt_out.setPlaceholderText("Same as source…")
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self._on_browse_out)
        row2.addWidget(self.txt_out, 1)
        row2.addWidget(btn_browse)
        lay.addLayout(row2)

        hint = QLabel("Leave empty to save next to each source image.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addStretch(1)

        # ---- Open folder shortcut
        self.btn_open_out = QPushButton("📂  Open Output Folder")
        self.btn_open_out.setEnabled(False)
        self.btn_open_out.clicked.connect(self._on_open_out)
        lay.addWidget(self.btn_open_out)

        # ---- Compress button
        self.btn_compress = QPushButton("⚡  Compress")
        self.btn_compress.setObjectName("Primary")
        self.btn_compress.clicked.connect(self._on_compress)
        lay.addWidget(self.btn_compress)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("Danger")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        lay.addWidget(self.btn_cancel)

        return panel

    def _build_footer(self) -> QWidget:
        f = QFrame()
        f.setObjectName("Card")
        lay = QHBoxLayout(f)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(14)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setObjectName("Summary")
        self.lbl_status.setMinimumWidth(180)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

        lay.addWidget(self.lbl_status)
        lay.addWidget(self.progress, 1)
        return f

    # ---------------------------------------------------------- table utils
    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.jobs))
        for row, job in enumerate(self.jobs):
            self._write_row(row, job)
        self._update_summary()

    def _update_row(self, row: int) -> None:
        if 0 <= row < len(self.jobs):
            self._write_row(row, self.jobs[row])
        self._update_summary()

    def _write_row(self, row: int, job: ImageJob) -> None:
        name_item = QTableWidgetItem(job.path.name)
        name_item.setToolTip(str(job.path))
        name_item.setData(Qt.UserRole, row)
        self.table.setItem(row, 0, name_item)

        orig_item = QTableWidgetItem(human_size(job.orig_size))
        orig_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 1, orig_item)

        if job.new_size and job.orig_size:
            pct = (1 - job.new_size / job.orig_size) * 100.0
            txt = f"{human_size(job.new_size)}   ({pct:+.0f}%)"
            color = "#a6e3a1" if pct >= 0 else "#f9e2af"
        else:
            txt = "—"
            color = "#6c7086"
        res_item = QTableWidgetItem(txt)
        res_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        res_item.setForeground(QColor(color))
        self.table.setItem(row, 2, res_item)

        st_item = QTableWidgetItem(job.status)
        st_item.setTextAlignment(Qt.AlignCenter)
        palette = {
            "Pending":  "#9399b2",
            "Working…": "#f9e2af",
            "Done":     "#a6e3a1",
            "Failed":   "#f38ba8",
            "Skipped":  "#9399b2",
        }
        st_item.setForeground(QColor(palette.get(job.status, "#cdd6f4")))
        self.table.setItem(row, 3, st_item)

    def _update_summary(self) -> None:
        n = len(self.jobs)
        total_orig = sum(j.orig_size for j in self.jobs)
        done = [j for j in self.jobs if j.status == "Done" and j.new_size]
        if done:
            total_new = sum(j.new_size for j in done)
            self.lbl_summary.setText(
                f"{n} file(s)   •   {human_size(total_orig)} → {human_size(total_new)}"
            )
        else:
            self.lbl_summary.setText(f"{n} file(s)   •   {human_size(total_orig)}")

    # ---------------------------------------------------------- file actions
    def _on_add_files(self) -> None:
        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", f"Images ({exts});;All Files (*)"
        )
        if paths:
            self._add_paths([Path(p) for p in paths])

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._add_paths([Path(folder)])

    def _add_paths(self, paths: List[Path]) -> None:
        existing = {j.path for j in self.jobs}
        added = 0
        for p in paths:
            if p.is_dir():
                try:
                    iterator = sorted(p.rglob("*"))
                except Exception:
                    continue
                for f in iterator:
                    if (f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
                            and f not in existing):
                        try:
                            size = f.stat().st_size
                        except OSError:
                            continue
                        self.jobs.append(ImageJob(path=f, orig_size=size))
                        existing.add(f)
                        added += 1
            elif p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                if p not in existing:
                    try:
                        size = p.stat().st_size
                    except OSError:
                        continue
                    self.jobs.append(ImageJob(path=p, orig_size=size))
                    existing.add(p)
                    added += 1

        self._refresh_table()
        self._set_status(f"Added {added} file(s).")

    def _on_remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()},
                      reverse=True)
        if not rows:
            return
        for r in rows:
            if 0 <= r < len(self.jobs):
                self.jobs.pop(r)
        self._refresh_table()

    def _on_clear(self) -> None:
        if not self.jobs:
            return
        if QMessageBox.question(self, "Clear list",
                                "Remove all files from the list?") == QMessageBox.Yes:
            self.jobs.clear()
            self._refresh_table()

    # ---------------------------------------------------------- settings
    def _on_format_changed(self) -> None:
        # Nothing required — the worker reads it at compress time.
        pass

    def _on_max_toggled(self, checked: bool) -> None:
        self.spin_max.setEnabled(checked)
        self.slider_quality.setEnabled(not checked)
        self.lbl_quality_val.setEnabled(not checked)
        if checked:
            self.lbl_quality_val.setText("Auto")

    def _on_browse_out(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.txt_out.setText(folder)
            self.btn_open_out.setEnabled(True)

    def _on_open_out(self) -> None:
        text = self.txt_out.text().strip()
        if text and Path(text).exists():
            open_in_explorer(Path(text))

    # ---------------------------------------------------------- compression
    def _collect_settings(self) -> Optional[Settings]:
        fmt_map = {0: "ORIGINAL", 1: "JPEG", 2: "PNG", 3: "WEBP"}
        fmt = fmt_map[self.cmb_format.currentIndex()]

        max_kb = self.spin_max.value() if self.chk_max.isChecked() else 0
        quality = 85 if self.chk_max.isChecked() else self.slider_quality.value()

        out_dir: Optional[Path] = None
        text = self.txt_out.text().strip()
        if text:
            out_dir = Path(text)
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, "Invalid output folder",
                    f"Cannot use the selected output folder:\n{e}"
                )
                return None
        return Settings(fmt=fmt, quality=quality,
                        max_size_kb=max_kb, out_dir=out_dir)

    def _on_compress(self) -> None:
        if self.thread is not None:
            return
        if not self.jobs:
            QMessageBox.information(self, APP_NAME,
                                    "Add some images first.")
            return

        settings = self._collect_settings()
        if settings is None:
            return

        for job in self.jobs:
            job.status = "Pending"
            job.new_size = 0
            job.out_path = None
        self._refresh_table()

        self.progress.setRange(0, len(self.jobs))
        self.progress.setValue(0)
        self.btn_open_out.setEnabled(bool(settings.out_dir))

        self.worker = CompressWorker(list(self.jobs), settings)
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._on_thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)

        self._set_busy(True)
        self._set_status("Compressing…")
        self.thread.start()

    def _on_cancel(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self._set_status("Cancelling…")

    def _set_busy(self, busy: bool) -> None:
        self.btn_compress.setEnabled(not busy)
        self.btn_cancel.setVisible(busy)
        self.btn_add_files.setEnabled(not busy)
        self.btn_add_folder.setEnabled(not busy)
        self.btn_remove.setEnabled(not busy)
        self.btn_clear.setEnabled(not busy)
        self.cmb_format.setEnabled(not busy)
        self.slider_quality.setEnabled(not busy and not self.chk_max.isChecked())
        self.chk_max.setEnabled(not busy)
        self.spin_max.setEnabled(not busy and self.chk_max.isChecked())
        self.txt_out.setEnabled(not busy)

    # ---------------------------------------------------------- worker slots
    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, name: str) -> None:
        self.progress.setValue(current)
        if name:
            self._set_status(f"({current + 1}/{total})  {name}")

    @Slot(int, bool, int, str)
    def _on_file_done(self, index: int, ok: bool, new_size: int, error: str) -> None:
        if index < 0 or index >= len(self.jobs):
            return
        job = self.jobs[index]
        if ok:
            job.status = "Done"
            job.new_size = new_size
        else:
            job.status = "Failed"
            job.new_size = 0
        self._update_row(index)

    @Slot(int, int)
    def _on_finished(self, ok: int, fail: int) -> None:
        self.progress.setValue(self.progress.maximum())
        if fail == 0:
            self._set_status(f"✔ Done — {ok} file(s) compressed.")
        else:
            self._set_status(f"Done — {ok} succeeded, {fail} failed.")

    @Slot()
    def _on_thread_finished(self) -> None:
        self.thread = None
        self.worker = None
        self._set_busy(False)
        self._update_summary()

    # ---------------------------------------------------------- misc
    def _set_status(self, text: str) -> None:
        self.lbl_status.setText(text)

    # --- drag & drop
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths: List[Path] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()

    # --- window close protection while busy
    def closeEvent(self, event) -> None:
        if self.thread is not None and self.worker is not None:
            res = QMessageBox.question(
                self, APP_NAME,
                "A compression is running. Cancel and quit?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                event.ignore()
                return
            self.worker.cancel()
            self.thread.quit()
            self.thread.wait(4000)
        event.accept()


# ------------------------------------------------------------------ entry point
def main() -> int:
    # In Qt6 / PySide6, high-DPI scaling and high-DPI pixmaps are always
    # enabled by default. The old Qt5 attributes
    # (AA_EnableHighDpiScaling / AA_UseHighDpiPixmaps) are deprecated and
    # would trigger DeprecationWarning, so they are intentionally omitted.

    # Optional: use a smoother rounding policy for fractional scale factors
    # (e.g. 125% or 150% on Windows). This call is fully supported and
    # does not emit any deprecation warning. Comment it out to keep the
    # default Qt rounding policy.
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_SHORT)

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())