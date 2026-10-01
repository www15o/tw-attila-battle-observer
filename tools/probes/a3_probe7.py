#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_probe7.py — 读若干 VA 的 C 字符串 + 反汇编片段。只读。用法: a3_probe7.py <va> [...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import a3_dis as A

for x in sys.argv[1:]:
    va = int(x, 16)
    b = A.read(va, 96)
    s = b.split(b"\0")[0].decode("latin1", "replace")
    print("0x%08x  %r" % (va, s))
