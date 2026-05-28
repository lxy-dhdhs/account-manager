#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号仓库管理系统
- 三个独立仓库：保时捷、热气球、比心兔兔
- 导入时选择目标仓库
- 删除、顺排（移入共享顺排仓库）
- 报幕窗口（当前/预备/顺排）
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import ctypes

DATA_FILE = "account_data.json"
WAREHOUSE_NAMES = ["保时捷仓库", "热气球仓库", "比心兔兔仓库"]
WAREHOUSE_KEYS  = ["porsche", "balloon", "bunny"]

# ── Color Palette ───────────────────────────────────────────
C = {
    'bg':        '#0d1117',
    'surface':   '#161b22',
    'raised':    '#1c2333',
    'border':    '#30363d',
    'text':      '#e6edf3',
    'muted':     '#8b949e',
    'faint':     '#484f58',
    'blue':      '#58a6ff',
    'blue_h':    '#79c0ff',
    'blue_d':    '#1f6feb',
    'red':       '#f85149',
    'red_h':     '#ff7b72',
    'green':     '#3fb950',
    'green_h':   '#56d364',
    'yellow':    '#d2991d',
    'yellow_h':  '#e2b340',
    'purple':    '#a371f7',
    'purple_h':  '#bc8cff',
    'orange':    '#f0883e',
    'pink':      '#f778ba',
    'selection': '#1f6feb',
}

# Warehouse accent colors
WH_COLORS = {
    'porsche': C['blue'],
    'balloon': C['orange'],
    'bunny':   C['pink'],
}

# ── Fonts ───────────────────────────────────────────────────
FONT_SM  = ('Microsoft YaHei UI', 9)
FONT     = ('Microsoft YaHei UI', 10)
FONT_B   = ('Microsoft YaHei UI', 10, 'bold')
FONT_H   = ('Microsoft YaHei UI', 12, 'bold')
FONT_T   = ('Microsoft YaHei UI', 18, 'bold')


class AccountManager:
    """数据层 —— 三个仓库 + 顺排仓库"""

    def __init__(self):
        self.warehouses = {k: [] for k in WAREHOUSE_KEYS}
        self.queue = []
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                wh = d.get('warehouses', {})
                for k in WAREHOUSE_KEYS:
                    self.warehouses[k] = wh.get(k, [])
                if 'warehouse' in d and d['warehouse']:
                    self.warehouses['porsche'].extend(d['warehouse'])
                raw_q = d.get('queue', [])
                self.queue = []
                for item in raw_q:
                    if isinstance(item, list) and len(item) >= 3:
                        self.queue.append([item[0], item[1], item[2]])
                    elif isinstance(item, list) and len(item) == 2:
                        self.queue.append([item[0], item[1], 0])
                    elif isinstance(item, str):
                        self.queue.append(['porsche', item, 0])
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({'warehouses': self.warehouses, 'queue': self.queue},
                      f, ensure_ascii=False, indent=2)

    def add_account(self, text, wh_key):
        """单个/批量添加（按分隔符拆分），返回 (added_count, dup_count, added_names)"""
        import re
        raw = re.split(r'[\s,，;；|/\\、]+', text.strip())
        names = [n for n in raw if n]
        if not names:
            return 0, 0, []
        added = []
        dup = 0
        wh = self.warehouses[wh_key]
        for name in names:
            if name in wh:
                dup += 1
            else:
                wh.append(name)
                added.append(name)
        if added:
            self.save()
        return len(added), dup, added

    def import_file(self, path, wh_key):
        with open(path, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        new = dup = 0
        wh = self.warehouses[wh_key]
        for acc in lines:
            if acc in wh:
                dup += 1
            else:
                wh.append(acc)
                new += 1
        if new:
            self.save()
        return new, dup

    def delete_many(self, wh_key, accounts):
        wh = self.warehouses[wh_key]
        removed = 0
        for a in accounts:
            if a in wh:
                wh.remove(a)
                removed += 1
        if removed:
            self.save()
        return removed

    def move_account(self, wh_key, from_idx, to_idx):
        """移动仓库中某个账号的位置"""
        wh = self.warehouses[wh_key]
        if 0 <= from_idx < len(wh) and 0 <= to_idx < len(wh):
            item = wh.pop(from_idx)
            wh.insert(to_idx, item)
            self.save()

    def pop_first(self, wh_key):
        """删除仓库第一个账号，返回账号名或None"""
        wh = self.warehouses[wh_key]
        if wh:
            acc = wh.pop(0)
            self.save()
            return acc
        return None

    def pop_first_queue(self):
        """顺排完成：直接删除第一个账号"""
        if self.queue:
            wh_key, name, idx = self.queue.pop(0)
            self.save()
            return name, wh_key
        return None, None

    def move_queue(self, from_idx, to_idx):
        """移动顺排仓库中某个账号的位置"""
        if 0 <= from_idx < len(self.queue) and 0 <= to_idx < len(self.queue):
            item = self.queue.pop(from_idx)
            self.queue.insert(to_idx, item)
            self.save()

    def queue_accounts(self, wh_key, accounts):
        wh = self.warehouses[wh_key]
        moved = 0
        for a in accounts:
            if a in wh:
                idx = wh.index(a)
                wh.remove(a)
                self.queue.append([wh_key, a, idx])
                moved += 1
        if moved:
            self.save()
        return moved

    def dequeue_many(self, items):
        """移除顺排账号并返回原仓库原位置"""
        returned = 0
        for item in items:
            if item in self.queue:
                self.queue.remove(item)
                wh_key, name, idx = item
                wh = self.warehouses[wh_key]
                wh.insert(min(idx, len(wh)), name)
                returned += 1
        if returned:
            self.save()
        return returned

    def clear_queue(self):
        n = len(self.queue)
        self.queue.clear()
        self.save()
        return n

    def announcement(self):
        """按优先级取：保时捷 → 热气球 → 比心兔兔，预备账号不足时顺延到下个仓库"""
        cur = None
        wh_label = None
        bak = []

        for k in WAREHOUSE_KEYS:
            wh = self.warehouses[k]
            if not wh:
                continue
            if cur is None:
                cur = wh[0]
                wh_label = WAREHOUSE_NAMES[WAREHOUSE_KEYS.index(k)]
                bak.extend(wh[1:])
            else:
                bak.extend(wh)

        bak = bak[:3]
        return cur, bak, [name for _, name, _ in self.queue], wh_label


# ═══════════════════════════════════════════════════════════════
#  UI Helpers
# ═══════════════════════════════════════════════════════════════

def _flat_btn(parent, text, font=FONT_B, fg=C['text'], bg=C['raised'],
              hover_bg=C['border'], command=None):
    btn = tk.Label(
        parent, text=text, font=font,
        fg=fg, bg=bg,
        padx=16, pady=6,
        cursor='hand2',
    )
    btn.configure(relief=tk.FLAT, borderwidth=0, highlightthickness=0)
    def on_enter(e): btn.configure(bg=hover_bg)
    def on_leave(e): btn.configure(bg=bg)
    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    btn.bind('<Button-1>', lambda e: command() if command else None)
    return btn


class AccountListbox(tk.Frame):
    """带滚动条 + 拖拽排序的账号列表"""

    def __init__(self, parent, height=12, on_move=None):
        super().__init__(parent, bg=C['surface'])
        self.on_move = on_move  # callback(from_idx, to_idx)
        self._drag_from = None

        self.listbox = tk.Listbox(
            self, bg=C['raised'], fg=C['text'],
            selectbackground=C['selection'], selectforeground='#ffffff',
            font=FONT, relief=tk.FLAT, borderwidth=0, highlightthickness=0,
            height=height, activestyle='none', exportselection=False,
            selectmode=tk.EXTENDED,
        )
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.listbox.yview,
            bg=C['surface'], troughcolor=C['surface'],
            activebackground=C['faint'], borderwidth=0, highlightthickness=0,
        )
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 拖拽排序
        self.listbox.bind('<Button-1>', self._on_press)
        self.listbox.bind('<B1-Motion>', self._on_drag)
        self.listbox.bind('<ButtonRelease-1>', self._on_release)

    def _on_press(self, event):
        idx = self.listbox.nearest(event.y)
        if idx >= 0:
            self._drag_from = idx

    def _on_drag(self, event):
        if self._drag_from is not None:
            cur = self.listbox.nearest(event.y)
            if cur != self._drag_from and cur >= 0:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(cur)

    def _on_release(self, event):
        if self._drag_from is not None and self.on_move:
            to_idx = self.listbox.nearest(event.y)
            if to_idx >= 0 and to_idx != self._drag_from:
                self.on_move(self._drag_from, to_idx)
        self._drag_from = None

    def clear(self):           self.listbox.delete(0, tk.END)
    def populate(self, items):
        self.clear()
        for it in items:
            self.listbox.insert(tk.END, it)
    def get_selected(self):
        return [self.listbox.get(i) for i in self.listbox.curselection()]
    def get_single_selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None
    def select_set(self, idx):
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
    def select_all(self):
        self.listbox.select_set(0, tk.END)
    def bind_event(self, seq, cb):
        self.listbox.bind(seq, cb)


class ImportDialog:
    """导入对话框 —— 选择文件和目标仓库"""

    def __init__(self, parent, manager):
        self.mgr = manager
        self.result = None  # (filepath, wh_key)

        self.dlg = tk.Toplevel(parent)
        self.dlg.title('导入账号')
        self.dlg.geometry('420x250')
        self.dlg.configure(bg=C['bg'])
        self.dlg.resizable(False, False)
        self.dlg.transient(parent)
        self.dlg.grab_set()
        self.dlg.protocol('WM_DELETE_WINDOW', self.dlg.destroy)

        self.dlg.update_idletasks()
        sw = self.dlg.winfo_screenwidth()
        sh = self.dlg.winfo_screenheight()
        self.dlg.geometry(f'+{(sw - 420) // 2}+{(sh - 250) // 2}')

        self._build()

    def _build(self):
        main = tk.Frame(self.dlg, bg=C['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        tk.Label(main, text='导入账号', font=FONT_H,
                 fg=C['text'], bg=C['bg']).pack(pady=(0, 16))

        # ── 文件选择 ──
        file_row = tk.Frame(main, bg=C['bg'])
        file_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(file_row, text='文件：', font=FONT,
                 fg=C['text'], bg=C['bg'], width=5, anchor=tk.W).pack(side=tk.LEFT)

        self.file_var = tk.StringVar()
        file_entry = tk.Entry(file_row, textvariable=self.file_var,
                              font=FONT, bg=C['raised'], fg=C['text'],
                              relief=tk.FLAT, borderwidth=0,
                              insertbackground=C['text'])
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 8))

        _flat_btn(file_row, '浏览', font=FONT_SM, fg=C['blue'],
                  bg=C['raised'], hover_bg=C['border'],
                  command=self._browse).pack(side=tk.RIGHT)

        # ── 仓库选择 ──
        wh_row = tk.Frame(main, bg=C['bg'])
        wh_row.pack(fill=tk.X, pady=(0, 14))

        tk.Label(wh_row, text='仓库：', font=FONT,
                 fg=C['text'], bg=C['bg'], width=5, anchor=tk.W).pack(side=tk.LEFT)

        self.wh_var = tk.StringVar(value=WAREHOUSE_NAMES[0])
        wh_combo = ttk.Combobox(wh_row, textvariable=self.wh_var,
                                values=WAREHOUSE_NAMES, state='readonly',
                                font=FONT)
        wh_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)

        # ── 确认 ──
        _flat_btn(main, '确认导入', fg=C['green'], bg=C['raised'],
                  hover_bg=C['border'], command=self._confirm).pack(fill=tk.X)

    def _browse(self):
        path = filedialog.askopenfilename(
            title='选择账号文件',
            filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')],
        )
        if path:
            self.file_var.set(path)

    def _confirm(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning('提示', '请选择要导入的文件', parent=self.dlg)
            return
        if not os.path.exists(path):
            messagebox.showerror('错误', '文件不存在', parent=self.dlg)
            return
        wh_name = self.wh_var.get()
        wh_key = WAREHOUSE_KEYS[WAREHOUSE_NAMES.index(wh_name)]
        self.result = (path, wh_key, wh_name)
        self.dlg.destroy()

    def get_result(self):
        if self.dlg.winfo_exists():
            self.dlg.wait_window()
        return self.result


class AddAccountDialog:
    """添加账号对话框 —— 三选一仓库"""

    def __init__(self, parent):
        self.result = None  # (name, wh_key, wh_name)

        self.dlg = tk.Toplevel(parent)
        self.dlg.title('添加账号')
        self.dlg.geometry('380x230')
        self.dlg.configure(bg=C['bg'])
        self.dlg.resizable(False, False)
        self.dlg.transient(parent)
        self.dlg.grab_set()
        self.dlg.protocol('WM_DELETE_WINDOW', self.dlg.destroy)

        self.dlg.update_idletasks()
        sw = self.dlg.winfo_screenwidth()
        sh = self.dlg.winfo_screenheight()
        self.dlg.geometry(f'+{(sw - 380) // 2}+{(sh - 230) // 2}')

        self._build()

    def _build(self):
        main = tk.Frame(self.dlg, bg=C['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        tk.Label(main, text='添加账号', font=FONT_H,
                 fg=C['text'], bg=C['bg']).pack(pady=(0, 12))

        # 账号名输入
        name_row = tk.Frame(main, bg=C['bg'])
        name_row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(name_row, text='账号：', font=FONT,
                 fg=C['text'], bg=C['bg'], width=5, anchor=tk.W).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(name_row, textvariable=self.name_var,
                              font=FONT, bg=C['raised'], fg=C['text'],
                              relief=tk.FLAT, borderwidth=0,
                              insertbackground=C['text'])
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        # 仓库三选一
        wh_row = tk.Frame(main, bg=C['bg'])
        wh_row.pack(fill=tk.X, pady=(0, 12))
        tk.Label(wh_row, text='仓库：', font=FONT,
                 fg=C['text'], bg=C['bg'], width=5, anchor=tk.W).pack(side=tk.LEFT)

        radio_frame = tk.Frame(wh_row, bg=C['bg'])
        radio_frame.pack(side=tk.LEFT)

        self.wh_var = tk.StringVar(value=WAREHOUSE_KEYS[0])
        wh_colors = {'porsche': C['blue'], 'balloon': C['orange'], 'bunny': C['pink']}
        for k, name in zip(WAREHOUSE_KEYS, WAREHOUSE_NAMES):
            rb = tk.Radiobutton(radio_frame, text=name, variable=self.wh_var, value=k,
                                font=FONT_SM, fg=wh_colors[k], bg=C['bg'],
                                selectcolor=C['raised'],
                                activebackground=C['bg'], activeforeground=wh_colors[k],
                                relief=tk.FLAT)
            rb.pack(side=tk.LEFT, padx=(0, 10))

        # 确认
        _flat_btn(main, '确认添加', fg=C['green'], bg=C['raised'],
                  hover_bg=C['border'], command=self._confirm).pack(fill=tk.X)

        name_entry.focus_set()
        name_entry.bind('<Return>', lambda e: self._confirm())

    def _confirm(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入账号名', parent=self.dlg)
            return
        wh_key = self.wh_var.get()
        wh_name = WAREHOUSE_NAMES[WAREHOUSE_KEYS.index(wh_key)]
        self.result = (name, wh_key, wh_name)
        self.dlg.destroy()

    def get_result(self):
        if self.dlg.winfo_exists():
            self.dlg.wait_window()
        return self.result


# ═══════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.mgr = AccountManager()
        self._ann_visible = True

        self.root = tk.Tk()
        self.root.title('账号仓库管理系统')
        self.root.geometry('960x760')
        self.root.configure(bg=C['bg'])
        self.root.minsize(760, 580)

        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f'+{(sw - 960) // 2}+{(sh - 640) // 2}')

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        self._build_ui()
        self._refresh_all()

        self.root.bind('<Control-o>', lambda e: self._import())
        self.root.bind('<Control-b>', lambda e: self._announce())
        self.root.bind('<Delete>', lambda e: self._delete_selected())

    # ── UI ──────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=C['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # ── 顶部栏 ──
        top = tk.Frame(outer, bg=C['surface'])
        top.pack(fill=tk.X, pady=(0, 14), ipady=10)

        tk.Label(top, text='账号仓库管理系统', font=FONT_T,
                 fg=C['text'], bg=C['surface']).pack(side=tk.LEFT, padx=16)

        btn_area = tk.Frame(top, bg=C['surface'])
        btn_area.pack(side=tk.RIGHT, padx=10)

        _flat_btn(btn_area, '添加账号', fg=C['blue'], bg=C['raised'],
                  hover_bg=C['border'], command=self._add_account).pack(
                      side=tk.LEFT, padx=(0, 8))

        _flat_btn(btn_area, '导入账号', fg=C['green'], bg=C['raised'],
                  hover_bg=C['border'], command=self._import).pack(
                      side=tk.LEFT, padx=(0, 8))

        _flat_btn(btn_area, '报  幕', fg=C['purple'], bg=C['raised'],
                  hover_bg=C['border'], command=self._announce).pack(
                      side=tk.LEFT, padx=(0, 8))

        _flat_btn(btn_area, '刷新报幕', fg=C['purple_h'], bg=C['raised'],
                  hover_bg=C['border'], command=self._refresh_announce).pack(side=tk.LEFT)

        # ── 主体：左侧三仓库选项卡 + 右侧顺排仓库 ──
        body = tk.Frame(outer, bg=C['bg'])
        body.pack(fill=tk.BOTH, expand=True)

        # 左栏: 选项卡
        left_panel = tk.Frame(body, bg=C['surface'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_warehouse_panel(left_panel)

        # 分隔线
        tk.Frame(body, bg=C['border'], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=10)

        # 右栏: 顺排仓库
        self._build_queue_panel(body)

        # ── 报幕面板（嵌入主窗口，绿幕背景用于 OBS 抠图）──
        self.ann_frame = tk.Frame(outer, bg='#00ff00', height=170)
        self.ann_frame.pack(fill=tk.X, pady=(12, 0))
        self.ann_frame.pack_propagate(False)

        self.ann_canvas = tk.Canvas(self.ann_frame, bg='#00ff00',
                                     highlightthickness=0, borderwidth=0)
        self.ann_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # ── 底部状态栏 ──
        footer = tk.Frame(outer, bg=C['surface'])
        footer.pack(fill=tk.X, pady=(12, 0), ipady=6)

        self.status_lbl = tk.Label(
            footer, text='就绪', font=FONT_SM,
            fg=C['muted'], bg=C['surface'], anchor=tk.W
        )
        self.status_lbl.pack(side=tk.LEFT, padx=14)

        tk.Label(footer, text='Ctrl+O 导入 | Delete 删除 | Ctrl+B 报幕',
                 font=FONT_SM, fg=C['faint'], bg=C['surface']).pack(
                     side=tk.RIGHT, padx=14)

    def _build_warehouse_panel(self, parent):
        # 每个仓库对应一个 tk.Frame 容器，包含列表和按钮
        self.wh_frames = {}   # key -> Frame
        self.wh_lists = {}    # key -> AccountListbox
        self.wh_counts = {}   # key -> count label
        self.wh_notebook = None  # ttk.Notebook (will be styled)
        self.wh_keys_map = {}  # tab_index -> wh_key

        # 用 ttk.Notebook 无法完美适配暗色主题，改用自定义标签栏
        self.tab_bar = tk.Frame(parent, bg=C['surface'])
        self.tab_bar.pack(fill=tk.X)

        self.tab_btns = {}
        self._active_tab = WAREHOUSE_KEYS[0]

        tab_names = {
            'porsche': '保时捷仓库',
            'balloon': '热气球仓库',
            'bunny':   '比心兔兔仓库',
        }

        for k in WAREHOUSE_KEYS:
            btn = tk.Label(
                self.tab_bar, text=tab_names[k], font=FONT_B,
                fg=C['muted'], bg=C['surface'],
                padx=24, pady=10, cursor='hand2',
            )
            btn.pack(side=tk.LEFT)
            btn.bind('<Button-1>', lambda e, key=k: self._switch_tab(key))
            btn.bind('<Enter>', lambda e, b=btn: b.configure(fg=C['text']))
            btn.bind('<Leave>', lambda e, b=btn, key=k:
                     b.configure(fg=C['text'] if self._active_tab == key else C['muted']))
            self.tab_btns[k] = btn

        # 标签下方的蓝色指示线
        self.tab_indicator = tk.Frame(self.tab_bar, bg=WH_COLORS[self._active_tab], height=2)
        self.tab_indicator.place(x=0, y=40, width=100)

        # 分隔线
        tk.Frame(parent, bg=C['border'], height=1).pack(fill=tk.X)

        # 内容区
        self.wh_content = tk.Frame(parent, bg=C['surface'])
        self.wh_content.pack(fill=tk.BOTH, expand=True)
        self.wh_content.grid_rowconfigure(0, weight=1)
        self.wh_content.grid_columnconfigure(0, weight=1)

        for k in WAREHOUSE_KEYS:
            frm = tk.Frame(self.wh_content, bg=C['surface'])
            frm.grid(row=0, column=0, sticky='nsew')  # 全部叠在同一格子

            # 计数标签
            count_lbl = tk.Label(frm, text='共 0 个账号', font=FONT_SM,
                                 fg=C['muted'], bg=C['surface'], anchor=tk.W)
            count_lbl.pack(fill=tk.X, padx=14, pady=(10, 4))
            self.wh_counts[k] = count_lbl

            # 列表
            lst = AccountListbox(frm, height=14,
                                 on_move=lambda fi, ti, key=k: self._move_account(key, fi, ti))
            lst.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))
            self.wh_lists[k] = lst

            # 右键菜单
            menu = tk.Menu(lst.listbox, tearoff=0, bg=C['raised'], fg=C['text'],
                           activebackground=C['selection'], activeforeground='#ffffff',
                           font=FONT_SM)
            menu.add_command(label='删除选中',
                             command=lambda key=k: self._delete_selected(key))
            menu.add_command(label='顺排选中',
                             command=lambda key=k: self._queue_selected(key))
            menu.add_separator()
            menu.add_command(label='全选',
                             command=lambda key=k: self.wh_lists[key].select_all())
            lst.bind_event('<Button-3>',
                           lambda e, m=menu: self._popup_menu(e, m))

            # 按钮
            btn_row = tk.Frame(frm, bg=C['surface'])
            btn_row.pack(fill=tk.X, padx=14, pady=(6, 14))

            _flat_btn(btn_row, '完  成', fg=C['green'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self._complete_first(key)).pack(
                          side=tk.LEFT, padx=(0, 8))

            _flat_btn(btn_row, '删  除', fg=C['red'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self._delete_selected(key)).pack(
                          side=tk.LEFT, padx=(0, 8))

            _flat_btn(btn_row, '顺  排', fg=C['yellow'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self._queue_selected(key)).pack(
                          side=tk.LEFT)

            _flat_btn(btn_row, '↑ 上移', fg=C['blue'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self._move_up(key)).pack(
                          side=tk.RIGHT, padx=(0, 4))

            _flat_btn(btn_row, '↓ 下移', fg=C['blue'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self._move_down(key)).pack(
                          side=tk.RIGHT, padx=(0, 8))

            _flat_btn(btn_row, '全  选', fg=C['muted'], bg=C['raised'],
                      hover_bg=C['border'],
                      command=lambda key=k: self.wh_lists[key].select_all()).pack(
                          side=tk.RIGHT)

            self.wh_frames[k] = frm

        # 初始显示第一个仓库
        self._switch_tab(WAREHOUSE_KEYS[0])

    def _switch_tab(self, key):
        self._active_tab = key
        for k in WAREHOUSE_KEYS:
            if k == key:
                self.wh_frames[k].tkraise()
                self.tab_btns[k].configure(fg=C['text'])
            else:
                self.tab_btns[k].configure(fg=C['muted'])

        # 移动指示线
        tab_names = ['保时捷仓库', '热气球仓库', '比心兔兔仓库']
        idx = WAREHOUSE_KEYS.index(key)
        # 粗略计算位置
        x_offset = sum(
            len(tab_names[i]) * 12 + 48 for i in range(idx)
        ) if idx > 0 else 0
        self.tab_indicator.place(
            x=x_offset if x_offset > 0 else 0,
            y=40, width=len(tab_names[idx]) * 12 + 48
        )
        self.tab_indicator.configure(bg=WH_COLORS[key])

    def _build_queue_panel(self, parent):
        panel = tk.Frame(parent, bg=C['surface'])
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 头部
        hdr = tk.Frame(panel, bg=C['surface'], height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=C['yellow'], width=3).pack(
            side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        tk.Label(hdr, text='顺排仓库', font=FONT_H,
                 fg=C['text'], bg=C['surface']).pack(side=tk.LEFT, pady=12)
        self.q_count_lbl = tk.Label(hdr, text='(0)', font=FONT_SM,
                                     fg=C['muted'], bg=C['surface'])
        self.q_count_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=12)

        tk.Frame(panel, bg=C['border'], height=1).pack(fill=tk.X)

        # 列表
        self.q_list = AccountListbox(panel, height=18,
                                     on_move=lambda fi, ti: self._move_queue(fi, ti))
        self.q_list.pack(fill=tk.BOTH, expand=True, padx=14, pady=(10, 8))

        # 右键
        q_menu = tk.Menu(self.q_list.listbox, tearoff=0, bg=C['raised'], fg=C['text'],
                         activebackground=C['selection'], activeforeground='#ffffff',
                         font=FONT_SM)
        q_menu.add_command(label='移出队列', command=self._dequeue_selected)
        q_menu.add_command(label='清空队列', command=self._clear_queue)
        self.q_list.bind_event('<Button-3>', lambda e: self._popup_menu(e, q_menu))

        # 按钮
        btn_row = tk.Frame(panel, bg=C['surface'])
        btn_row.pack(fill=tk.X, padx=14, pady=(6, 14))

        _flat_btn(btn_row, '顺排完成', fg=C['green'], bg=C['raised'],
                  hover_bg=C['border'],
                  command=self._complete_queue_first).pack(side=tk.LEFT, padx=(0, 8))

        _flat_btn(btn_row, '移出队列', fg=C['red'], bg=C['raised'],
                  hover_bg=C['border'],
                  command=self._dequeue_selected).pack(side=tk.LEFT)

        _flat_btn(btn_row, '↓ 下移', fg=C['blue'], bg=C['raised'],
                  hover_bg=C['border'],
                  command=self._move_queue_down).pack(side=tk.RIGHT, padx=(0, 4))

        _flat_btn(btn_row, '↑ 上移', fg=C['blue'], bg=C['raised'],
                  hover_bg=C['border'],
                  command=self._move_queue_up).pack(side=tk.RIGHT, padx=(0, 8))

        _flat_btn(btn_row, '清空队列', fg=C['muted'], bg=C['raised'],
                  hover_bg=C['border'],
                  command=self._clear_queue).pack(side=tk.RIGHT)

    # ── 数据刷新 ────────────────────────────────────────────

    def _refresh_all(self):
        for k in WAREHOUSE_KEYS:
            self.wh_lists[k].populate(self.mgr.warehouses[k])
            self.wh_counts[k].configure(
                text=f'共 {len(self.mgr.warehouses[k])} 个账号')
        self.q_list.populate([name for _, name, _ in self.mgr.queue])
        self.q_count_lbl.configure(text=f'({len(self.mgr.queue)})')
        self._draw_announce()

    def _status(self, msg):
        self.status_lbl.configure(text=msg)
        self.root.after(4000, lambda: self.status_lbl.configure(text='就绪'))

    # ── 操作 ────────────────────────────────────────────────

    def _add_account(self):
        dlg = AddAccountDialog(self.root)
        result = dlg.get_result()
        if not result:
            return
        name, wh_key, wh_name = result
        added, dup, names = self.mgr.add_account(name, wh_key)
        if added:
            self._refresh_all()
            self._switch_tab(wh_key)
            detail = '、'.join(names[:5])
            if len(names) > 5:
                detail += f'...等{len(names)}个'
            self._status(f'已添加 {added} 个到「{wh_name}」：{detail}' +
                         (f'，跳过重复 {dup} 个' if dup else ''))
        else:
            messagebox.showwarning('提示', '账号已存在或输入为空')

    def _import(self):
        dlg = ImportDialog(self.root, self.mgr)
        result = dlg.get_result()
        if not result:
            return
        path, wh_key, wh_name = result
        try:
            new, dup = self.mgr.import_file(path, wh_key)
            self._refresh_all()
            self._switch_tab(wh_key)
            self._status(f'导入到「{wh_name}」完成：新增 {new} 个，重复跳过 {dup} 个')
        except Exception as e:
            messagebox.showerror('导入失败', str(e))

    def _delete_selected(self, wh_key=None):
        if wh_key is None:
            wh_key = self._active_tab
        selected = self.wh_lists[wh_key].get_selected()
        if not selected:
            self._status('请先选择要删除的账号')
            return
        if not messagebox.askyesno('确认删除', f'确定要删除选中的 {len(selected)} 个账号吗？'):
            return
        n = self.mgr.delete_many(wh_key, selected)
        self._refresh_all()
        self._status(f'已删除 {n} 个账号')

    def _move_account(self, wh_key, from_idx, to_idx):
        self.mgr.move_account(wh_key, from_idx, to_idx)
        self._refresh_all()
        self.wh_lists[wh_key].select_set(to_idx)

    def _move_up(self, wh_key):
        idx = self.wh_lists[wh_key].get_single_selected_index()
        if idx is None:
            self._status('请先选中一个账号')
            return
        if idx == 0:
            return
        self.mgr.move_account(wh_key, idx, idx - 1)
        self._refresh_all()
        self.wh_lists[wh_key].select_set(idx - 1)

    def _move_down(self, wh_key):
        idx = self.wh_lists[wh_key].get_single_selected_index()
        if idx is None:
            self._status('请先选中一个账号')
            return
        wh = self.mgr.warehouses[wh_key]
        if idx >= len(wh) - 1:
            return
        self.mgr.move_account(wh_key, idx, idx + 1)
        self._refresh_all()
        self.wh_lists[wh_key].select_set(idx + 1)

    def _complete_first(self, wh_key=None):
        if wh_key is None:
            wh_key = self._active_tab
        acc = self.mgr.pop_first(wh_key)
        if acc:
            self._refresh_all()
            self._status(f'已完成「{acc}」（已从仓库移除）')
        else:
            self._status('仓库为空，无可完成账号')

    def _complete_queue_first(self):
        acc, wh_key = self.mgr.pop_first_queue()
        if acc:
            wh_name = WAREHOUSE_NAMES[WAREHOUSE_KEYS.index(wh_key)]
            self._refresh_all()
            self._status(f'顺排完成「{acc}」（已从顺排仓库删除）')
        else:
            self._status('顺排仓库为空')

    def _move_queue(self, from_idx, to_idx):
        self.mgr.move_queue(from_idx, to_idx)
        self._refresh_all()
        self.q_list.select_set(to_idx)

    def _move_queue_up(self):
        idx = self.q_list.get_single_selected_index()
        if idx is None:
            self._status('请先选中一个顺排账号')
            return
        if idx == 0:
            return
        self.mgr.move_queue(idx, idx - 1)
        self._refresh_all()
        self.q_list.select_set(idx - 1)

    def _move_queue_down(self):
        idx = self.q_list.get_single_selected_index()
        if idx is None:
            self._status('请先选中一个顺排账号')
            return
        if idx >= len(self.mgr.queue) - 1:
            return
        self.mgr.move_queue(idx, idx + 1)
        self._refresh_all()
        self.q_list.select_set(idx + 1)

    def _queue_selected(self, wh_key=None):
        if wh_key is None:
            wh_key = self._active_tab
        selected = self.wh_lists[wh_key].get_selected()
        if not selected:
            self._status('请先选择要顺排的账号')
            return
        n = self.mgr.queue_accounts(wh_key, selected)
        self._refresh_all()
        self._status(f'已将 {n} 个账号移入顺排仓库（先排在上）')

    def _dequeue_selected(self):
        indices = list(self.q_list.listbox.curselection())
        if not indices:
            self._status('请先在顺排仓库中选择要移除的账号')
            return
        items = [self.mgr.queue[i] for i in indices]
        n = self.mgr.dequeue_many(items)
        self._refresh_all()
        self._status(f'已移除 {n} 个账号并返回原仓库')

    def _clear_queue(self):
        if not self.mgr.queue:
            self._status('顺排仓库已为空')
            return
        if not messagebox.askyesno('确认清空', '确定要清空整个顺排仓库吗？'):
            return
        n = self.mgr.clear_queue()
        self._refresh_all()
        self._status(f'已清空顺排仓库（共移除 {n} 个账号）')

    def _announce(self):
        self._ann_visible = not self._ann_visible
        self.ann_frame.configure(height=170 if self._ann_visible else 0)
        self._status('报幕面板已显示' if self._ann_visible else '报幕面板已隐藏')

    def _refresh_announce(self):
        self._draw_announce()
        self._status('报幕已刷新')

    def _draw_announce(self):
        cur, bak, que, wh_label = self.mgr.announcement()

        self.ann_canvas.delete('all')
        FONT_A = ('Microsoft YaHei UI', 14, 'bold')
        YELLOW = '#ffff00'
        X = 12
        y = 10

        def draw_text(canvas, x, y, text, font, fill='#ffff00'):
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                canvas.create_text(x+dx, y+dy, text=text, font=font,
                                   fill='#000000', anchor='w')
            return canvas.create_text(x, y, text=text, font=font,
                                      fill=fill, anchor='w')

        # 当前账号
        cur_text = f'当前账号：{cur if cur else "无"}'
        draw_text(self.ann_canvas, X, y, cur_text, FONT_A, YELLOW)
        y += 38

        # 预备账号
        if bak:
            bak_text = f'预备账号：{"  |  ".join(bak)}'
        else:
            bak_text = '预备账号：—'
        draw_text(self.ann_canvas, X, y, bak_text, FONT_A, YELLOW)
        y += 38

        # 顺排账号
        if que:
            q_text = f'顺排账号：{"  |  ".join(que)}'
        else:
            q_text = '顺排账号：暂无'
        draw_text(self.ann_canvas, X, y, q_text, FONT_A, YELLOW)
        y += 38

        # 标题放最后
        draw_text(self.ann_canvas, X, y, '过号顺排，排队看主页', FONT_A, YELLOW)

    def _popup_menu(self, event, menu):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    App().run()
