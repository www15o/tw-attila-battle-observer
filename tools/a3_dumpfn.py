#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_dumpfn.py — 反汇编指定函数到结束 ret（含 call 目标注释），用于人工读链。
用法: python tools/a3_dumpfn.py 0x1012d000 [0x...] ...   (输出 stdout)
"""
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


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a3_dis as A
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

OUTDIR = re_dir("attila_out")
TLO, THI = A.text_range()
NAMES = {}
for pref in ("bcq", "ccq", "bncq"):
    fn = os.path.join(OUTDIR, pref + "_handlers.txt") if pref == "bcq" else os.path.join(OUTDIR, pref + "_table.txt")
    if not os.path.exists(fn):
        continue
    for line in open(fn, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip().split("\t")
        try:
            a = int(p[2 if pref == "bcq" else 3], 16)
        except Exception:
            continue
        NAMES.setdefault(a, []).append(p[0])


def dump(va, maxlen=0x900):
    c = Cs(CS_ARCH_X86, CS_MODE_32)
    buf = A.read(va, maxlen)
    print("===== FUN_0x%08x =====" % va)
    for i in c.disasm(buf, va):
        tag = ""
        if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x"):
            try:
                t = int(i.op_str, 16)
            except ValueError:
                t = 0
            nm = NAMES.get(t, [])
            tag = "    ; " + (",".join(nm) if nm else ("FUN_0x%08x" % t if TLO <= t < THI else "data?" ))
        print("  0x%08x: %-26s %-8s %-34s%s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, tag))
        if i.mnemonic == "ret" and i.address != va:
            break


if __name__ == "__main__":
    for a in sys.argv[1:]:
        dump(int(a, 16))
