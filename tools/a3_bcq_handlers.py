#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_bcq_handlers.py — 从 bcq_table.txt 的注册 site 反推 BCQ 命令 handler（注册块 arg4 = .text 函数）。

注册块布局（每条 0x20B 等距，int3 填充；表里的 site = name 立即数槽）：
    68 <fn>                ; site-8 (imm @ site-7)   ← 本脚本要找的 handler
    6a <0|1>               ; site-3                  ← 命令 flag
    68 <name_va>           ; site-1 (imm @ site)
    68 <proto_global>      ; site+4 (imm @ site+5)
    e8 <registrar>         ; site+0xa
验证判据：fn ∈ .text；且函数体入口含 `cmp byte ptr [esi+4],0`（命令门控）与 FUN_102d4e* 参数解析。
只读，不写游戏文件。
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
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a3_dis as A

OUT = re_dir("attila_out")
TLO, THI = A.text_range()

rows = []
bad = []
with open(os.path.join(OUT, "bcq_table.txt"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 4:
            continue
        name, kind, site, proto = p[0], p[1], int(p[2], 16), int(p[3], 16)
        reg = int(p[4], 16) if len(p) > 4 and p[4].startswith("0x") else None
        arg4 = A.u32(site - 7)
        op1 = A.read(site - 8, 1)
        op2 = A.read(site - 3, 1)
        op3 = A.read(site + 4, 1)
        ok = (arg4 is not None and TLO <= arg4 < THI and op1 == b"\x68"
              and op2 == b"\x6a" and op3 == b"\x68")
        if not ok:
            bad.append((name, hex(site), hex(arg4 or 0)))
            continue
        rows.append((name, arg4, proto, site, reg))

with open(os.path.join(OUT, "bcq_handlers.txt"), "w", encoding="utf-8") as f:
    f.write("# BCQ name \t handler(arg4,.text) \t proto_global \t reg_site \t registrar\n")
    f.write("# 注册块: push arg4; push 0; push name; push proto; call registrar "
            "(arg4 语义待逐条验证：入口 `cmp byte[cmd+4],0` 门控 + FUN_102d4e* 参数解析)\n")
    for name, h, proto, site, reg in sorted(rows):
        f.write("%s\t0x%08x\t0x%08x\t0x%08x\t%s\n" %
                (name, h, proto, site, "0x%08x" % reg if reg else "-"))

print("total=%d ok=%d bad=%d" % (len(rows) + len(bad), len(rows), len(bad)))
print("handlers in .text:", all(TLO <= r[1] < THI for r in rows))
print("unique handlers:", len({r[1] for r in rows}))
for b in bad[:10]:
    print("BAD", b)
for want in ("BCQ_FACTION_QUIT_BATTLE", "BCQ_FORCE_BATTLE_END", "BCQ_FORCE_BATTLE_VICTORY",
             "BCQ_CREATE_AI_SCRIPT_CONTROLLER", "BCQ_APPLY_DAMAGE_TO_UNIT"):
    for r in rows:
        if r[0] == want:
            print("HIT", r[0], "handler=0x%x" % r[1], "proto=0x%x" % r[2])
