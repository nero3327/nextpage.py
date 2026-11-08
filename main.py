"""Nextpage：沿“下一章”等关键词链接自动翻页抓取，tkinter GUI 显示正文。

参考 thirdparty/get.php 的逻辑，用纯 Python 标准库实现。
启动：python main.py（或双击 release/start.bat）
"""

import gzip
import queue
import re
import ssl
import threading
import tkinter as tk
import zlib
from datetime import datetime
from html import unescape
from pathlib import Path
from tkinter import scrolledtext, ttk
from urllib.parse import urljoin
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
)

RE_ANCHOR = re.compile(r"<a\b[^>]*>.*?</a\s*>", re.I | re.S)
RE_HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
RE_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)
RE_BREAK = re.compile(r"<br\s*/?>|</(?:p|div|h[1-6]|li|tr|table)\s*>", re.I)
RE_TAG = re.compile(r"<[^>]+>")


def fetch_page(url, encoding, timeout=30):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    })
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        data = resp.read()
        content_encoding = resp.headers.get("Content-Encoding", "")
    if "gzip" in content_encoding:
        data = gzip.decompress(data)
    elif "deflate" in content_encoding:
        try:
            data = zlib.decompress(data)
        except zlib.error:
            data = zlib.decompress(data, -zlib.MAX_WBITS)
    return data.decode(encoding, errors="replace")


def find_next_url(html, base_url, keyword):
    found = None
    for m in RE_ANCHOR.finditer(html):
        anchor = m.group(0)
        if keyword in anchor:
            href = RE_HREF.search(anchor)
            if href:
                found = urljoin(base_url, unescape(href.group(1).strip()))
    return found


def html_to_text(html):
    text = RE_BLOCK.sub("", html)
    text = RE_BREAK.sub("\n", text)
    text = RE_TAG.sub("", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def crawl(url, pages, keyword, encoding, out, stop):
    visited = set()
    for i in range(1, pages + 1):
        if stop.is_set():
            out.put(("done", "已手动停止"))
            return
        try:
            html = fetch_page(url, encoding)
        except Exception as exc:
            out.put(("error", f"第 {i} 页抓取失败：{exc}"))
            return
        out.put(("page", (i, url, html_to_text(html))))
        nxt = find_next_url(html, url, keyword)
        if not nxt:
            out.put(("done", f"共 {i} 页，未找到含「{keyword}」的链接"))
            return
        if nxt == url or nxt in visited:
            out.put(("done", f"共 {i} 页，下一页链接重复（{nxt}），停止"))
            return
        visited.add(url)
        out.put(("next", (i, nxt)))
        url = nxt
    out.put(("done", f"已完成全部 {pages} 页"))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nextpage — 自动翻页阅读")
        self.geometry("860x640")
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)

    def _build_widgets(self):
        form = ttk.Frame(self, padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="URL：").grid(row=0, column=0, sticky="w")
        self.url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.url_var).grid(
            row=0, column=1, columnspan=6, sticky="ew", pady=(0, 6))

        ttk.Label(form, text="页数：").grid(row=1, column=0, sticky="w")
        self.pages_var = tk.IntVar(value=15)
        ttk.Spinbox(form, from_=1, to=999, textvariable=self.pages_var,
                    width=6).grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="关键词：").grid(row=1, column=2, sticky="w", padx=(12, 0))
        self.keyword_var = tk.StringVar(value="下一章")
        ttk.Entry(form, textvariable=self.keyword_var, width=12).grid(
            row=1, column=3, sticky="w")
        ttk.Label(form, text="编码：").grid(row=1, column=4, sticky="w", padx=(12, 0))
        self.encoding_var = tk.StringVar(value="GBK")
        ttk.Combobox(form, textvariable=self.encoding_var,
                     values=["GBK", "UTF-8"], width=8,
                     state="readonly").grid(row=1, column=5, sticky="w")

        self.start_btn = ttk.Button(form, text="开始", command=self.start)
        self.start_btn.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.save_btn = ttk.Button(form, text="保存到本地", command=self.save_to_local)
        self.save_btn.grid(row=2, column=2, columnspan=2, sticky="w", pady=(8, 0), padx=(12, 0))
        self.stop_btn = ttk.Button(form, text="停止", command=self.stop, state="disabled")
        self.stop_btn.grid(row=2, column=4, columnspan=3, sticky="w", pady=(8, 0), padx=(12, 0))
        form.columnconfigure(1, weight=1)

        self.text = scrolledtext.ScrolledText(
            self, wrap="word", state="disabled", font=("Microsoft YaHei", 10))
        self.text.pack(fill="both", expand=True, padx=10)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 4)).pack(fill="x")

    def start(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_var.set("请输入 URL")
            return
        if "://" not in url:
            url = "http://" + url
        try:
            pages = int(self.pages_var.get())
        except tk.TclError:
            pages = 15
        keyword = self.keyword_var.get().strip() or "下一章"
        encoding = self.encoding_var.get()

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("抓取中…")
        threading.Thread(
            target=crawl,
            args=(url, pages, keyword, encoding, self.queue, self.stop_event),
            daemon=True,
        ).start()

    def stop(self):
        self.stop_event.set()
        self.status_var.set("正在停止…")

    def save_to_local(self):
        content = self.text.get("1.0", "end-1c")
        if not content.strip():
            self.status_var.set("没有可保存的内容")
            return
        name = datetime.now().strftime("%m%d-%H%M") + ".txt"
        path = Path(__file__).resolve().parent / name
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            self.status_var.set(f"保存失败：{exc}")
            return
        self.status_var.set(f"已保存：{path}")

    def _poll(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "page":
                    i, url, body = payload
                    self._append(f"\n===== 第 {i} 页  {url} =====\n\n{body}\n")
                    self.status_var.set(f"已抓取第 {i} 页")
                elif kind == "next":
                    i, url = payload
                    self._append(f"\n[第 {i} 页完成] 下一页：{url}\n")
                elif kind == "error":
                    self._append(f"\n[错误] {payload}\n")
                    self._finish(payload)
                elif kind == "done":
                    self._append(f"\n[{payload}]\n")
                    self._finish(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _append(self, text):
        self.text.configure(state="normal")
        self.text.insert("end", text)
        self.text.see("end")
        self.text.configure(state="disabled")

    def _finish(self, msg):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_var.set(msg)

    def _on_close(self):
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()