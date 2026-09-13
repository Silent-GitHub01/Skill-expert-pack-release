#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把专家包目录打成 zip，zip 根为 <name>/（供 WorkBuddy 导入专家包）。

用法：
    python make_zip.py <name> [--parent <dir>]

默认在 . 下找 <name>/ 并产出 ./<name>.zip。
中文文件名、空目录条目（含 .gitkeep）均保留，便于逐条核对。
"""
import argparse
import os
import sys
import zipfile


def make_zip(name: str, parent: str = ".") -> str:
    root = os.path.join(parent, name)
    if not os.path.isdir(root):
        sys.exit("目录不存在: %s" % os.path.abspath(root))

    out = os.path.join(parent, name + ".zip")
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dn, fn in os.walk(root):
            dn.sort()
            fn.sort()
            z.write(dp)  # 目录条目（arcname 会保留尾部 /）
            for f in fn:
                z.write(os.path.join(dp, f))
                count += 1

    size = os.path.getsize(out)
    print("written %s (%d bytes, %d files)" % (out, size, count))
    with zipfile.ZipFile(out) as z:
        for info in z.infolist():
            print("%10d  %s" % (info.file_size, info.filename))
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("name", help="专家包目录名，如 harmony-novel")
    p.add_argument("--parent", default=".", help="父目录，默认当前目录")
    a = p.parse_args()
    make_zip(a.name, a.parent)
