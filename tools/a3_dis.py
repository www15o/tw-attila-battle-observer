#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_dis.py — Attila 只读静态小工具：VA<->raw、反汇编、立即数/指针交叉引用。
用法：
  python a3_dis.py dis <VA> [n=40]              反汇编 n 条指令
  python a3_dis.py bytes <VA> [n=64]            hexdump
  python a3_dis.py xref <VA> [--sec .text]      扫描引用该 VA 的 4 字节槽（对齐+未对齐）
  python a3_dis.py callxref <VA>                扫描 E8 rel32 直接 call 到该 VA
  python a3_dis.py sections                      节表
只读：不写游戏文件。
"""
import struct
import sys

import os  # 解析器需要；若文件已 import os，重复无害
# 本仓库不附带任何游戏二进制。DLL 路径解析优先级：
#   ATTILA_DLL（完整文件路径）→ ATTILA_DIR（游戏根目录）→ Steam 安装位置自动探测
_DLL_NAME = "empire.retail.dll"
_GAME_SUBPATH = os.path.join("steamapps", "common", "Total War Attila")


def _steam_roots():
    """列出本机 Steam 库根目录（注册表 + libraryfolders.vdf）；非 Windows / 失败返回空表。"""
    roots = []
    try:
        import winreg
    except ImportError:
        return roots
    steam = None
    for hive, key, name in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                steam = winreg.QueryValueEx(k, name)[0]
                break
        except OSError:
            continue
    if not steam:
        return roots
    steam = os.path.normpath(steam)
    roots.append(steam)
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    try:
        with open(vdf, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.startswith('"path"'):
                    parts = line.split('"')
                    if len(parts) >= 4:
                        p = parts[3].replace(chr(92) * 2, chr(92))  # 反斜杠用 chr(92) 写，免去转义层数
                        if os.path.isdir(p):
                            roots.append(os.path.normpath(p))
    except OSError:
        pass
    return roots


def find_dll():
    """定位游戏引擎模块；找不到返回 None（保持模块可 import，不猜路径）。"""
    env = os.environ.get("ATTILA_DLL")
    if env and os.path.isfile(env):
        return env
    cands = []
    d = os.environ.get("ATTILA_DIR")
    if d:
        cands.append(os.path.join(d, _DLL_NAME))
    for root in _steam_roots():
        cands.append(os.path.join(root, _GAME_SUBPATH, _DLL_NAME))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def _repo_root():
    """从本文件向上找到含 tools/ 的目录（tools/ 与 tools/probes/ 都适用）。"""
    p = os.path.dirname(os.path.abspath(__file__))
    while os.path.dirname(p) != p:
        if os.path.isdir(os.path.join(p, "tools")):
            return p
        p = os.path.dirname(p)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def re_dir(sub):
    """逆向工作目录：环境变量可覆盖，默认仓库内 re/<sub>（不一定存在，工具自己建）。"""
    env = os.environ.get("ATTILA_RE_" + sub.upper())
    return env or os.path.join(_repo_root(), "re", sub)


BIN = find_dll()
if not BIN:
    raise RuntimeError(
        "未找到 empire.retail.dll：请设置 ATTILA_DLL（完整文件路径）或 "
        "ATTILA_DIR（游戏根目录）。本仓库不附带游戏文件。")
BASE = 0x10000000

_DATA = open(BIN, "rb").read()
_SECS = []


def parse_sections():
    e = struct.unpack_from("<I", _DATA, 0x3C)[0]
    nsec = struct.unpack_from("<H", e and 0 or 0, 0) if False else struct.unpack_from("<H", _DATA, e + 6)[0]
    optsz = struct.unpack_from("<H", _DATA, e + 20)[0]
    p = e + 24 + optsz
    out = []
    for _ in range(nsec):
        name = _DATA[p:p + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", _DATA, p + 8)
        out.append(dict(name=name, va=BASE + vaddr, vsize=vsize,
                        rawptr=rawptr, rawsize=rawsize,
                        lo=BASE + vaddr, hi=BASE + vaddr + max(vsize, rawsize)))
        p += 40
    return out


_SECS = parse_sections()


def sec_of(va):
    for s in _SECS:
        if s["lo"] <= va < s["lo"] + max(s["vsize"], s["rawsize"]):
            return s
    return None


def va2off(va):
    """VA -> file offset；未初始化（.bss 形态的 .data 尾部）返回 None，
    避免把后一节的 raw 字节当成该 VA 的内容。"""
    s = sec_of(va)
    if not s:
        return None
    d = va - s["lo"]
    if d >= s["rawsize"]:
        return None
    off = s["rawptr"] + d
    if off < 0 or off >= len(_DATA):
        return None
    return off


def off2va(off):
    for s in _SECS:
        if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
            return s["lo"] + (off - s["rawptr"])
    return None


def read(va, n):
    o = va2off(va)
    if o is None:
        return b""
    return _DATA[o:o + n]


def u32(va):
    b = read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def text_range():
    s = [x for x in _SECS if x["name"] == ".text"][0]
    return s["lo"], s["lo"] + s["vsize"]


def cs():
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    c = Cs(CS_ARCH_X86, CS_MODE_32)
    c.detail = True
    return c


def dis(va, n=40):
    c = cs()
    buf = read(va, n * 16)
    out = []
    for i in c.disasm(buf, va, count=n):
        out.append("0x%08x:  %-8s %-30s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return out


def xref(target, sections=(".text", ".rdata", ".data")):
    needle = struct.pack("<I", target)
    hits = []
    for s in _SECS:
        if s["name"] not in sections:
            continue
        blob = _DATA[s["rawptr"]:s["rawptr"] + s["rawsize"]]
        start = 0
        while True:
            i = blob.find(needle, start)
            if i < 0:
                break
            hits.append((s["lo"] + i, s["name"], (s["lo"] + i) % 4 == 0))
            start = i + 1
    return hits


def callxref(target):
    lo, hi = text_range()
    s = [x for x in _SECS if x["name"] == ".text"][0]
    blob = _DATA[s["rawptr"]:s["rawptr"] + s["vsize"]]
    base = s["lo"]
    hits = []
    start = 0
    while True:
        i = blob.find(b"\xe8", start)
        if i < 0:
            break
        if i + 5 <= len(blob):
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            if (base + i + 5 + rel) & 0xFFFFFFFF == target:
                hits.append(base + i)
        start = i + 1
    return hits


def callsites_in(va, size=None):
    """列出函数体内所有 E8 call 目标（用于链式跟踪）。"""
    if size is None:
        size = 0x400
    buf = read(va, size)
    c = cs()
    out = []
    for i in c.disasm(buf, va):
        if i.mnemonic == "call":
            out.append((i.address, i.op_str))
    return out


def main():
    a = sys.argv
    if a[1] == "sections":
        for s in _SECS:
            print("%-8s va=0x%08x vsize=0x%x raw=0x%x rawsize=0x%x" %
                  (s["name"], s["lo"], s["vsize"], s["rawptr"], s["rawsize"]))
    elif a[1] == "dis":
        for l in dis(int(a[2], 16), int(a[3]) if len(a) > 3 else 40):
            print(l)
    elif a[1] == "bytes":
        b = read(int(a[2], 16), int(a[3]) if len(a) > 3 else 64)
        print(b.hex(" "))
    elif a[1] == "xref":
        for va, sec, aligned in xref(int(a[2], 16)):
            print("0x%08x  %s  aligned=%s" % (va, sec, aligned))
    elif a[1] == "callxref":
        for va in callxref(int(a[2], 16)):
            print("0x%08x" % va)
    elif a[1] == "callsites":
        for va, op in callsites_in(int(a[2], 16), int(a[3]) if len(a) > 3 else None):
            print("0x%08x  call %s" % (va, op))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
