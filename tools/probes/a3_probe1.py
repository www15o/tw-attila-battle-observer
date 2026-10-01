#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_probe1.py — BCQ 命令 handler 家族形状统计 + QUIT/FORCE_END/FORCE_VICTORY 三链反汇编。
只读。输出到 stdout（便于 grep）。"""
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
import collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import a3_dis as A
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

OUTDIR = re_dir("attila_out")
TLO, THI = A.text_range()

# ---- 读 bcq_handlers.txt ----
H = {}
with open(os.path.join(OUTDIR, "bcq_handlers.txt"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        p = line.split("\t")
        H[p[0]] = (int(p[1], 16), int(p[2], 16))


def func_bytes(va, maxlen=0x600):
    """从 va 反汇编到 ret（近似函数体），返回指令列表。"""
    c = Cs(CS_ARCH_X86, CS_MODE_32)
    buf = A.read(va, maxlen)
    ins = []
    for i in c.disasm(buf, va):
        ins.append(i)
        if i.mnemonic == "ret" and len(ins) > 4:
            break
    return ins


def shape(va):
    """返回 handler 形状特征：调用的目标列表 + 门控模式。"""
    calls = [int(i.op_str.replace("0x", ""), 16) for i in func_bytes(va)
             if i.mnemonic == "call" and i.op_str.startswith("0x")]
    return calls


MODE = collections.Counter()
print("== handler 首指令模式统计 ==")
firsts = collections.Counter()
for name, (h, proto) in sorted(H.items()):
    b = A.read(h, 8)
    firsts[b[:3].hex()] += 1
for k, v in firsts.most_common(12):
    print("  %s : %d" % (k, v))

print("\n== 三个目标命令 ==")
for name in ("BCQ_FACTION_QUIT_BATTLE", "BCQ_FORCE_BATTLE_END", "BCQ_FORCE_BATTLE_VICTORY"):
    h, proto = H[name]
    print("\n--- %s handler=0x%08x proto=0x%08x ---" % (name, h, proto))
    for i in func_bytes(h, 0x400):
        tag = ""
        if i.mnemonic == "call" and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            nm = [n for n, (hh, pp) in H.items() if hh == t]
            tag = "   ; " + (",".join(nm) if nm else "callee")
        print("  0x%08x: %-7s %-32s%s" % (i.address, i.mnemonic, i.op_str, tag))

print("\n== 谁调用这三个 handler 的下游（callee 计数） ==")
for name in ("BCQ_FACTION_QUIT_BATTLE", "BCQ_FORCE_BATTLE_END", "BCQ_FORCE_BATTLE_VICTORY"):
    h, _ = H[name]
    print("%s handler=0x%08x calls=%s" % (name, h, ["0x%x" % x for x in shape(h)]))
