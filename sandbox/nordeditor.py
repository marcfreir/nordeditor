#!/usr/bin/env python3
"""
NordEditor — A clean PyQt5 text editor
Features: Multiple tabs, syntax highlighting, line numbers,
          find & replace, and proper UTF-8 clipboard handling.

Requirements:
    pip install PyQt5
    # or on Ubuntu/Debian:
    # sudo apt install python3-pyqt5
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPlainTextEdit, QTextEdit, QAction, QFileDialog, QMessageBox,
    QToolBar, QLabel, QLineEdit, QPushButton, QDialog, QCheckBox,
    QStatusBar, QFrame, QSizePolicy, QShortcut
)
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QTextFormat, QSyntaxHighlighter,
    QTextCharFormat, QFontMetrics, QPalette, QKeySequence, QIcon,
    QTextCursor, QClipboard, QTextDocument
)
from PyQt5.QtCore import (
    Qt, QRect, QSize, QRegExp, QTimer, pyqtSignal
)
from PyQt5.QtCore import QMimeData

from PyQt5.QtWidgets import QComboBox


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
DARK_BG        = "#1e1f2b"
PANEL_BG       = "#16171f"
EDITOR_BG      = "#1e1f2b"
LINE_NUM_BG    = "#16171f"
LINE_NUM_FG    = "#4a4f6a"
LINE_CUR_BG    = "#252638"
TEXT_FG        = "#cdd6f4"
ACCENT         = "#89b4fa"
ACCENT2        = "#cba6f7"
GREEN          = "#a6e3a1"
YELLOW         = "#f9e2af"
RED            = "#f38ba8"
TEAL           = "#94e2d5"
ORANGE         = "#fab387"
COMMENT_FG     = "#585b70"
TAB_BG         = "#16171f"
TAB_SEL        = "#1e1f2b"
BORDER         = "#313244"
FIND_BG        = "#252638"


# ─────────────────────────────────────────────
#  SYNTAX HIGHLIGHTER
# ─────────────────────────────────────────────
class SyntaxHighlighter(QSyntaxHighlighter):
    """Multi-language syntax highlighter (Python, JS, HTML, CSS, JSON, Bash)."""

    # RULES_BY_EXT = {
    #     "py": "python",
    #     "pyw": "python",
    #     "js": "javascript",
    #     "ts": "javascript",
    #     "html": "html",
    #     "htm": "html",
    #     "css": "css",
    #     "json": "json",
    #     "sh": "bash",
    #     "bash": "bash",
    # }

    RULES_BY_EXT = {
        "py": "python",   "pyw": "python",
        "js": "javascript", "ts": "javascript",
        "jsx": "javascript", "tsx": "javascript",
        "html": "html",   "htm": "html",
        "css": "css",     "scss": "css",  "sass": "css",
        "json": "json",   "jsonc": "json",
        "sh": "bash",     "bash": "bash",  "zsh": "bash",
        # plain text variants \u2014 no highlighting
        "txt": "plain",   "md": "plain",  "rst": "plain",
        "toml": "plain",  "yaml": "plain", "yml": "plain",
        "ini": "plain",   "log": "plain",  "csv": "plain",
    }

    def __init__(self, document, language="python"):
        super().__init__(document)
        self.language = language
        self._rules = []
        self._build_rules()

    def _fmt(self, color, bold=False, italic=False):
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(700)
        if italic:
            f.setFontItalic(True)
        return f

    def _build_rules(self):
        self._rules = []
        self._ml_start = None
        self._ml_end = None
        self._ml_fmt = None

        kw = self._fmt(ACCENT2, bold=True)
        builtin = self._fmt(ACCENT)
        string_fmt = self._fmt(GREEN)
        comment = self._fmt(COMMENT_FG, italic=True)
        number = self._fmt(ORANGE)
        decorator = self._fmt(YELLOW)
        func_fmt = self._fmt(TEAL, bold=True)

        if self.language == "python":
            keywords = [
                "False","None","True","and","as","assert","async","await",
                "break","class","continue","def","del","elif","else","except",
                "finally","for","from","global","if","import","in","is",
                "lambda","nonlocal","not","or","pass","raise","return",
                "try","while","with","yield"
            ]
            builtins = [
                "abs","all","any","bin","bool","bytes","callable","chr",
                "dict","dir","divmod","enumerate","eval","exec","filter",
                "float","format","frozenset","getattr","globals","hasattr",
                "hash","help","hex","id","input","int","isinstance",
                "issubclass","iter","len","list","locals","map","max",
                "min","next","object","oct","open","ord","pow","print",
                "property","range","repr","reversed","round","set","setattr",
                "slice","sorted","staticmethod","str","sum","super","tuple",
                "type","vars","zip"
            ]
            for kw_ in keywords:
                self._rules.append((QRegExp(r'\b' + kw_ + r'\b'), kw))
            for b in builtins:
                self._rules.append((QRegExp(r'\b' + b + r'\b'), builtin))
            # Decorators
            self._rules.append((QRegExp(r'@\w+'), decorator))
            # Function definitions
            self._rules.append((QRegExp(r'\bdef\s+(\w+)'), func_fmt))
            self._rules.append((QRegExp(r'\bclass\s+(\w+)'), self._fmt(YELLOW, bold=True)))
            # Strings
            self._rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_fmt))
            self._rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_fmt))
            # Numbers
            self._rules.append((QRegExp(r'\b[0-9]+\.?[0-9]*\b'), number))
            # Comments
            self._rules.append((QRegExp(r'#[^\n]*'), comment))
            # Multi-line strings
            self._ml_start = QRegExp(r'"""')
            self._ml_end   = QRegExp(r'"""')
            self._ml_fmt   = string_fmt

        elif self.language == "javascript":
            keywords = [
                "break","case","catch","class","const","continue","debugger",
                "default","delete","do","else","export","extends","finally",
                "for","function","if","import","in","instanceof","let","new",
                "return","static","super","switch","this","throw","try",
                "typeof","var","void","while","with","yield","async","await",
                "of","from","=>","null","undefined","true","false"
            ]
            for kw_ in keywords:
                self._rules.append((QRegExp(r'\b' + kw_ + r'\b'), kw))
            self._rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_fmt))
            self._rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_fmt))
            self._rules.append((QRegExp(r'`[^`\\]*(\\.[^`\\]*)*`'), string_fmt))
            self._rules.append((QRegExp(r'\b[0-9]+\.?[0-9]*\b'), number))
            self._rules.append((QRegExp(r'//[^\n]*'), comment))
            self._ml_start = QRegExp(r'/\*')
            self._ml_end   = QRegExp(r'\*/')
            self._ml_fmt   = comment

        elif self.language == "html":
            tag_fmt = self._fmt(RED)
            attr_fmt = self._fmt(YELLOW)
            val_fmt = self._fmt(GREEN)
            self._rules.append((QRegExp(r'<[!?/]?\w+'), tag_fmt))
            self._rules.append((QRegExp(r'\w+(?=\s*=)'), attr_fmt))
            self._rules.append((QRegExp(r'"[^"]*"'), val_fmt))
            self._rules.append((QRegExp(r"'[^']*'"), val_fmt))
            self._rules.append((QRegExp(r'/>|>'), tag_fmt))
            self._ml_start = QRegExp(r'<!--')
            self._ml_end   = QRegExp(r'-->')
            self._ml_fmt   = comment

        elif self.language == "css":
            prop_fmt = self._fmt(ACCENT)
            val_fmt  = self._fmt(GREEN)
            sel_fmt  = self._fmt(YELLOW, bold=True)
            self._rules.append((QRegExp(r'[.#]?\w[\w-]*\s*(?=\{)'), sel_fmt))
            self._rules.append((QRegExp(r'[\w-]+(?=\s*:)'), prop_fmt))
            self._rules.append((QRegExp(r':\s*[^;{]+'), val_fmt))
            self._rules.append((QRegExp(r'"[^"]*"'), self._fmt(GREEN)))
            self._ml_start = QRegExp(r'/\*')
            self._ml_end   = QRegExp(r'\*/')
            self._ml_fmt   = comment

        elif self.language == "json":
            key_fmt = self._fmt(ACCENT)
            val_str = self._fmt(GREEN)
            val_num = self._fmt(ORANGE)
            kw_fmt  = self._fmt(ACCENT2, bold=True)
            self._rules.append((QRegExp(r'"[^"]*"\s*(?=:)'), key_fmt))
            self._rules.append((QRegExp(r':\s*"[^"]*"'), val_str))
            self._rules.append((QRegExp(r'\b(true|false|null)\b'), kw_fmt))
            self._rules.append((QRegExp(r':\s*-?[0-9]+\.?[0-9]*'), val_num))

        elif self.language == "bash":
            keywords = [
                "if","then","else","elif","fi","for","while","do","done",
                "case","esac","function","return","exit","in","select","until",
                "echo","export","local","source","alias","unset","set"
            ]
            for kw_ in keywords:
                self._rules.append((QRegExp(r'\b' + kw_ + r'\b'), kw))
            self._rules.append((QRegExp(r'\$\w+'), self._fmt(TEAL)))
            self._rules.append((QRegExp(r'\$\{[^}]*\}'), self._fmt(TEAL)))
            self._rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_fmt))
            self._rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_fmt))
            self._rules.append((QRegExp(r'\b[0-9]+\b'), number))
            self._rules.append((QRegExp(r'#[^\n]*'), comment))

    def set_language(self, language):
        self.language = language
        self._build_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            idx = pattern.indexIn(text)
            while idx >= 0:
                length = pattern.matchedLength()
                self.setFormat(idx, length, fmt)
                idx = pattern.indexIn(text, idx + length)

        # Multi-line comment/string support
        if self._ml_start and self._ml_end and self._ml_fmt:
            self.setCurrentBlockState(0)
            start = 0
            if self.previousBlockState() != 1:
                start = self._ml_start.indexIn(text)

            while start >= 0:
                end = self._ml_end.indexIn(text, start)
                if end == -1:
                    self.setCurrentBlockState(1)
                    length = len(text) - start
                else:
                    length = end - start + self._ml_end.matchedLength()
                self.setFormat(start, length, self._ml_fmt)
                start = self._ml_start.indexIn(text, start + length)


# ─────────────────────────────────────────────
#  LINE NUMBER AREA
# ─────────────────────────────────────────────
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


# ─────────────────────────────────────────────
#  CODE EDITOR (single pane)
# ─────────────────────────────────────────────
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath = None
        self._language = "plain"

        self._setup_appearance()

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_width(0)
        self._highlight_current_line()

        self.highlighter = SyntaxHighlighter(self.document(), "plain")

    def _setup_appearance(self):
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.Monospace)
        if not font.exactMatch():
            font = QFont("Fira Code", 11)
        if not font.exactMatch():
            font = QFont("Monospace", 11)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopWidth(QFontMetrics(font).horizontalAdvance(' ') * 4)

        palette = self.palette()
        palette.setColor(QPalette.Base, QColor(EDITOR_BG))
        palette.setColor(QPalette.Text, QColor(TEXT_FG))
        palette.setColor(QPalette.Highlight, QColor(ACCENT).darker(150))
        palette.setColor(QPalette.HighlightedText, QColor(TEXT_FG))
        self.setPalette(palette)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDITOR_BG};
                color: {TEXT_FG};
                border: none;
                selection-background-color: #3d59a1;
            }}
        """)

    # ── clipboard: always use UTF-8 plain text ──
    def insertFromMimeData(self, source):
        """Override to ensure pasted text is always clean UTF-8 plain text."""
        if source.hasText():
            text = source.text()  # Qt returns QString (already Unicode)
            cursor = self.textCursor()
            cursor.insertText(text)
        else:
            super().insertFromMimeData(source)

    def copy(self):
        """Override copy to put ONLY clean UTF-8 plain text on clipboard — no HTML."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Qt uses U+2029 (PARAGRAPH SEPARATOR) for line breaks internally
            text = cursor.selectedText().replace('\u2029', '\n')
            mime = QMimeData()
            mime.setText(text)  # plain text only — no HTML added
            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime, QClipboard.Clipboard)
            # Also set SELECTION clipboard (Linux middle-click paste)
            mime2 = QMimeData()
            mime2.setText(text)
            clipboard.setMimeData(mime2, QClipboard.Selection)

    # def copy(self):
    #     cursor = self.textCursor()
    #     if cursor.hasSelection():
    #         # Convert internal paragraph separators to newlines
    #         text = cursor.selectedText().replace('\u2029', '\n')
    #         clipboard = QApplication.clipboard()
    #         clipboard.setText(text, QClipboard.Clipboard)
    #         clipboard.setText(text, QClipboard.Selection)   # for middle‑click paste on Linux

    def cut(self):
        self.copy()
        self.textCursor().removeSelectedText()

    def keyPressEvent(self, event):
        # Tab → 4 spaces
        if event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            return
        super().keyPressEvent(event)

    # ── line numbers ──
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 16 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_number_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(LINE_NUM_BG))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if block_num == current_line:
                    painter.setPen(QColor(ACCENT))
                else:
                    painter.setPen(QColor(LINE_NUM_FG))
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignRight, str(block_num + 1)
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1

    def _highlight_current_line(self):
        selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(LINE_CUR_BG))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)
        self.setExtraSelections(selections)

    # ── file helpers ──
    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, path):
        self._filepath = path
        ext = os.path.splitext(path)[1].lstrip('.').lower() if path else ""
        lang = SyntaxHighlighter.RULES_BY_EXT.get(ext, "plain")
        self._language = lang
        self.highlighter.set_language(lang)

    def load_file(self, path):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            self.setPlainText(f.read())
        self.filepath = path
        self.document().setModified(False)

    def save_file(self, path=None):
        target = path or self._filepath
        if not target:
            return False
        with open(target, 'w', encoding='utf-8') as f:
            f.write(self.toPlainText())
        self.filepath = target
        self.document().setModified(False)
        return True


# ─────────────────────────────────────────────
#  FIND & REPLACE BAR
# ─────────────────────────────────────────────
class FindBar(QFrame):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("findBar")
        self.setStyleSheet(f"""
            #findBar {{
                background: {FIND_BG};
                border-top: 1px solid {BORDER};
            }}
            QLineEdit {{
                background: {EDITOR_BG};
                color: {TEXT_FG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 3px 8px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
            QPushButton {{
                background: {PANEL_BG};
                color: {TEXT_FG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 3px 10px;
                min-width: 28px;
            }}
            QPushButton:hover {{ background: {BORDER}; color: {ACCENT}; }}
            QCheckBox {{ color: {LINE_NUM_FG}; }}
            QLabel {{ color: {LINE_NUM_FG}; font-size: 12px; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find…")
        self.find_input.setMinimumWidth(180)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace…")
        self.replace_input.setMinimumWidth(180)

        self.case_cb = QCheckBox("Aa")
        self.case_cb.setToolTip("Case sensitive")

        self.prev_btn = QPushButton("▲")
        self.next_btn = QPushButton("▼")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("All")
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(f"QPushButton {{ color: {RED}; border: none; background: transparent; }} QPushButton:hover {{ color: white; }}")

        self.match_label = QLabel("")

        for w in [QLabel("Find:"), self.find_input, self.prev_btn, self.next_btn,
                  self.case_cb, QLabel("Replace:"), self.replace_input,
                  self.replace_btn, self.replace_all_btn, self.match_label]:
            layout.addWidget(w)
        layout.addStretch()
        layout.addWidget(close_btn)

        self.prev_btn.clicked.connect(lambda: self._search(forward=False))
        self.next_btn.clicked.connect(lambda: self._search(forward=True))
        self.replace_btn.clicked.connect(self._replace_one)
        self.replace_all_btn.clicked.connect(self._replace_all)
        close_btn.clicked.connect(self._close)
        self.find_input.textChanged.connect(lambda: self._search(forward=True, from_top=True))
        self.find_input.returnPressed.connect(lambda: self._search(forward=True))

        self._editor = None

    def set_editor(self, editor):
        self._editor = editor

    def _flags(self):
        flags = QTextDocument.FindFlags()
        if self.case_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        return flags

    def _search(self, forward=True, from_top=False):
        if not self._editor:
            return
        needle = self.find_input.text()
        if not needle:
            self.match_label.setText("")
            return
        flags = self._flags()
        if not forward:
            flags |= QTextDocument.FindBackward
        cursor = self._editor.textCursor()
        if from_top:
            cursor.movePosition(QTextCursor.Start)
            self._editor.setTextCursor(cursor)
        found = self._editor.find(needle, flags)
        if not found:
            # wrap
            cursor = self._editor.textCursor()
            if forward:
                cursor.movePosition(QTextCursor.Start)
            else:
                cursor.movePosition(QTextCursor.End)
            self._editor.setTextCursor(cursor)
            self._editor.find(needle, flags)
        # count matches
        doc = self._editor.document()
        tmp = doc.find(needle, 0, self._flags())
        count = 0
        while not tmp.isNull():
            count += 1
            tmp = doc.find(needle, tmp, self._flags())
        self.match_label.setText(f"{count} match{'es' if count != 1 else ''}" if count else "No matches")
        self.match_label.setStyleSheet(f"color: {RED};" if not count else f"color: {GREEN};")

    def _replace_one(self):
        if not self._editor:
            return
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self._search(forward=True)

    def _replace_all(self):
        if not self._editor:
            return
        needle = self.find_input.text()
        replacement = self.replace_input.text()
        if not needle:
            return
        content = self._editor.toPlainText()
        flags = Qt.CaseSensitive if self.case_cb.isChecked() else Qt.CaseInsensitive
        new_content = content.replace(needle, replacement) if self.case_cb.isChecked() \
            else self._case_insensitive_replace(content, needle, replacement)
        count = content.lower().count(needle.lower()) if not self.case_cb.isChecked() \
            else content.count(needle)
        self._editor.setPlainText(new_content)
        self.match_label.setText(f"Replaced {count}")
        self.match_label.setStyleSheet(f"color: {YELLOW};")

    def _case_insensitive_replace(self, text, needle, replacement):
        import re
        return re.sub(re.escape(needle), replacement, text, flags=re.IGNORECASE)

    def _close(self):
        self.hide()
        self.closed.emit()
        if self._editor:
            self._editor.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._close()
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  TAB WIDGET WRAPPER
# ─────────────────────────────────────────────
class EditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = CodeEditor()
        self.find_bar = FindBar()
        self.find_bar.hide()
        self.find_bar.set_editor(self.editor)

        layout.addWidget(self.editor)
        layout.addWidget(self.find_bar)

    def show_find(self):
        self.find_bar.show()
        self.find_bar.find_input.setFocus()
        self.find_bar.find_input.selectAll()


# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NordEditor")
        self.resize(1100, 720)
        self._unsaved_count = 0
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()
        self.new_tab()  # open with one blank tab

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

    def _setup_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._add_action(file_menu, "New",          self.new_tab,       "Ctrl+N")
        self._add_action(file_menu, "Open…",        self.open_file,     "Ctrl+O")
        file_menu.addSeparator()
        self._add_action(file_menu, "Save",         self.save_file,     "Ctrl+S")
        self._add_action(file_menu, "Save As…",     self.save_file_as,  "Ctrl+Shift+S")
        file_menu.addSeparator()
        self._add_action(file_menu, "Close Tab",    self._close_current_tab, "Ctrl+W")
        self._add_action(file_menu, "Quit",         self.close,         "Ctrl+Q")

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "Undo",         lambda: self._cur_editor().undo(), "Ctrl+Z")
        self._add_action(edit_menu, "Redo",         lambda: self._cur_editor().redo(), "Ctrl+Y")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Cut",          lambda: self._cur_editor().cut(),  "Ctrl+X")
        self._add_action(edit_menu, "Copy",         lambda: self._cur_editor().copy(), "Ctrl+C")
        self._add_action(edit_menu, "Paste",        lambda: self._cur_editor().paste(), "Ctrl+V")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Select All",   lambda: self._cur_editor().selectAll(), "Ctrl+A")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Find & Replace", self.show_find,   "Ctrl+H")
        self._add_action(edit_menu, "Find",         self.show_find,     "Ctrl+F")

        # View
        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "Increase Font", self._font_bigger,  "Ctrl+=")
        self._add_action(view_menu, "Decrease Font", self._font_smaller, "Ctrl+-")

    def _add_action(self, menu, label, slot, shortcut=None):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def _setup_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        for label, slot, tip in [
            ("New",    self.new_tab,    "New file (Ctrl+N)"),
            ("Open",   self.open_file,  "Open file (Ctrl+O)"),
            ("Save",   self.save_file,  "Save (Ctrl+S)"),
            ("Find",   self.show_find,  "Find & Replace (Ctrl+F)"),
        ]:
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        tb.addSeparator()
        self._lang_label = QLabel("  plain  ")

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["plain", "python", "javascript", "html", "css", "json", "bash"])
        self._lang_combo.setToolTip("Syntax highlighting language")
        self._lang_combo.currentTextChanged.connect(self._change_language)
        tb.addWidget(self._lang_combo)

        tb.addWidget(self._lang_label)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._pos_label = QLabel("Ln 1, Col 1")
        self._enc_label = QLabel("UTF-8")
        self.status.addPermanentWidget(self._enc_label)
        self.status.addPermanentWidget(self._pos_label)

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {DARK_BG}; color: {TEXT_FG}; }}
            QMenuBar {{
                background: {PANEL_BG};
                color: {TEXT_FG};
                border-bottom: 1px solid {BORDER};
            }}
            QMenuBar::item:selected {{ background: {BORDER}; }}
            QMenu {{
                background: {PANEL_BG};
                color: {TEXT_FG};
                border: 1px solid {BORDER};
            }}
            QMenu::item:selected {{ background: {ACCENT}; color: {DARK_BG}; }}
            QToolBar {{
                background: {PANEL_BG};
                border-bottom: 1px solid {BORDER};
                spacing: 4px;
                padding: 2px 6px;
            }}
            QPushButton {{
                background: {PANEL_BG};
                color: {TEXT_FG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 3px 12px;
            }}
            QPushButton:hover {{ background: {BORDER}; color: {ACCENT}; }}
            QTabWidget::pane {{ border: none; background: {DARK_BG}; }}
            QTabBar::tab {{
                background: {TAB_BG};
                color: {LINE_NUM_FG};
                border: none;
                border-right: 1px solid {BORDER};
                padding: 5px 16px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background: {TAB_SEL};
                color: {TEXT_FG};
                border-bottom: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover {{ color: {TEXT_FG}; }}
            QStatusBar {{
                background: {PANEL_BG};
                color: {LINE_NUM_FG};
                border-top: 1px solid {BORDER};
                font-size: 11px;
            }}
            QLabel {{ color: {LINE_NUM_FG}; }}
        """)

    # ── tab helpers ──
    def new_tab(self, filepath=None):
        tab = EditorTab()
        tab.editor.cursorPositionChanged.connect(self._update_pos)
        tab.editor.document().modificationChanged.connect(
            lambda mod: self._update_tab_title(tab, mod)
        )
        if filepath:
            tab.editor.load_file(filepath)
            title = os.path.basename(filepath)
        else:
            self._unsaved_count += 1
            title = f"untitled-{self._unsaved_count}"
        self.tabs.addTab(tab, title)
        self.tabs.setCurrentWidget(tab)
        tab.editor.setFocus()
        return tab

    def _cur_tab(self):
        return self.tabs.currentWidget()

    def _cur_editor(self):
        tab = self._cur_tab()
        return tab.editor if tab else None

    def _update_tab_title(self, tab, modified):
        idx = self.tabs.indexOf(tab)
        if idx < 0:
            return
        title = self.tabs.tabText(idx).rstrip(" ●")
        self.tabs.setTabText(idx, title + (" ●" if modified else ""))

    # def _on_tab_changed(self, _):
    #     self._update_pos()
    #     editor = self._cur_editor()
    #     if editor:
    #         lang = editor._language
    #         self._lang_label.setText(f"  {lang}  ")

    def _on_tab_changed(self, _):
        self._update_pos()
        editor = self._cur_editor()
        if editor:
            lang = editor._language
            self._lang_label.setText(f"  {lang}  ")
            self._lang_combo.blockSignals(True)
            self._lang_combo.setCurrentText(lang)
            self._lang_combo.blockSignals(False)

    def _update_pos(self):
        editor = self._cur_editor()
        if editor:
            cur = editor.textCursor()
            self._pos_label.setText(f"Ln {cur.blockNumber()+1}, Col {cur.columnNumber()+1}")

    # ── file operations ──
    def open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open File", "",
            "All Files (*);;Python (*.py *.pyw);;JavaScript (*.js *.ts *.jsx *.tsx);;"
            "HTML (*.html *.htm);;CSS (*.css *.scss *.sass);;JSON (*.json *.jsonc);;"
            "Bash (*.sh *.bash);;Text (*.txt *.md *.rst *.csv *.log *.ini *.toml *.yaml *.yml)"
        )
        for path in paths:
            self.new_tab(path)

    def save_file(self):
        editor = self._cur_editor()
        if not editor:
            return
        if editor.filepath:
            editor.save_file()
            self.status.showMessage(f"Saved {editor.filepath}", 3000)
        else:
            self.save_file_as()

    def save_file_as(self):
        editor = self._cur_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "All Files (*)")
        if path:
            editor.save_file(path)
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
            lang = editor._language
            self._lang_label.setText(f"  {lang}  ")
            self.status.showMessage(f"Saved {path}", 3000)

    def _close_tab(self, index):
        tab = self.tabs.widget(index)
        if tab and tab.editor.document().isModified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "This file has unsaved changes. Close anyway?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.new_tab()

    def _close_current_tab(self):
        self._close_tab(self.tabs.currentIndex())

    def show_find(self):
        tab = self._cur_tab()
        if tab:
            tab.show_find()

    def _font_bigger(self):
        e = self._cur_editor()
        if e:
            f = e.font()
            f.setPointSize(f.pointSize() + 1)
            e.setFont(f)

    def _font_smaller(self):
        e = self._cur_editor()
        if e:
            f = e.font()
            f.setPointSize(max(6, f.pointSize() - 1))
            e.setFont(f)

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.editor.document().isModified():
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    "Some files have unsaved changes. Quit anyway?",
                    QMessageBox.SaveAll | QMessageBox.Discard | QMessageBox.Cancel
                )
                if reply == QMessageBox.SaveAll:
                    for j in range(self.tabs.count()):
                        t = self.tabs.widget(j)
                        if t and t.editor.document().isModified():
                            self.tabs.setCurrentIndex(j)
                            self.save_file()
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                break
        event.accept()

    def _change_language(self, lang):
        editor = self._cur_editor()
        if editor:
            editor._language = lang
            editor.highlighter.set_language(lang)
            self._lang_label.setText(f"  {lang}  ")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     app.setApplicationName("NordEditor")
#     app.setOrganizationName("NordEditor")

#     # Force UTF-8 locale
#     import locale
#     try:
#         locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
#     except Exception:
#         pass

#     win = MainWindow()

#     # Open files passed as CLI arguments
#     for arg in sys.argv[1:]:
#         if os.path.isfile(arg):
#             win.new_tab(arg)

#     win.show()
#     sys.exit(app.exec_())



def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NordEditor")
    app.setOrganizationName("NordEditor")

    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except Exception:
        pass

    win = MainWindow()

    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            win.new_tab(arg)

    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()