#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_probe6.py — 索引侧：给定地址 → 所在函数 + 该函数引用的字符串 + 调用者。只读。
用法: python tools/probes/a3_probe6.py <addr_hex> [...]
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import a3_dis as A

db = sqlite3.connect(os.path.join(ROOT, "re", "index", "attila_index.sqlite"))
P = "attila"


def enclosing(va):
    best = None
    for addr, name, size in db.execute("select addr,name,size from functions where project=?", (P,)):
        a = int(addr, 16)
        if a <= va and (size or 0) > 0 and va < a + size:
            if best is None or a > best[0]:
                best = (a, name, size)
    return best


for x in sys.argv[1:]:
    va = int(x, 16)
    f = enclosing(va)
    print("=== 0x%x -> %s" % (va, f))
    if not f:
        continue
    a, name, size = f
    print("   strings:")
    for (sa, sv, sn) in db.execute(
            "select sr.str_addr, s.val, s.nref from str_refs sr left join strings s "
            "on s.addr=sr.str_addr and s.project=sr.project where sr.project=? and sr.fn=? limit 40",
            (P, "%x" % a)):
        print("      %s %r" % (sa, (sv or "")[:80]))
    print("   callers:")
    for (ca,) in db.execute("select caller from calls where project=? and callee=?", (P, "%x" % a)):
        print("      0x%s" % ca)
    print("   callees:")
    for row in db.execute("select callee from calls where project=? and caller=?", (P, "%x" % a)):
        print("      -> 0x%s" % row[0])
