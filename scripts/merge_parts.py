#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把写作任务产出的 part 文件合并为章节原稿。

写作任务受单次输出长度限制，被要求分 part 写入临时目录。
本脚本**按标准节切分后重组**，因此 part 的先后顺序不影响最终结构。

用法：
    python scripts/merge_parts.py [--force]
"""

import io
import os
import re
import sys

TMP = os.path.join(os.environ.get('TEMP', r'C:\Users\laoya\AppData\Local\Temp'), 'thinkers')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (目标目录, 目标文件名, [part 文件名...])
JOBS = [
    ('hochschild', '01-managed-heart.md',
     ['hochschild-01-a.md', 'hochschild-01-b.md', 'hochschild-01-c.md']),
    ('hochschild', '02-second-shift.md',
     ['hochschild-02-a.md', 'hochschild-02-b.md']),
    ('hochschild', '03-global-time-divide.md',
     ['hochschild-03-a.md', 'hochschild-03-b.md']),
    ('hochschild', '04-economics-of-empathy.md',
     ['hochschild-04-a.md', 'hochschild-04-b.md']),
    ('arendt', '01-origins-of-totalitarianism.md',
     ['arendt-01-a.md', 'arendt-01-b.md']),
    ('arendt', '02-human-condition.md',
     ['arendt-02-a.md', 'arendt-02-b.md']),
    ('arendt', '03-truth-and-the-political.md',
     ['arendt-03-a.md', 'arendt-03-b.md']),
    ('arendt', '04-responsibility-and-judgment.md',
     ['arendt-04-a.md', 'arendt-04-b.md']),
]

SECTIONS = [
    '背景与语境',
    '核心论点',
    '关键概念详解',
    '方法论',
    '主要内容',
    '学术接受与批评',
    '深远影响',
    '与其他著作的关系',
    '与现有思想家的交叉对照',
    '当代意义',
]

FORCE = '--force' in sys.argv
# 已合并且做过人工修订的目标文件，除非 --force 不再覆盖
SKIP_DONE = {
    'arendt/02-human-condition.md',
    'hochschild/01-managed-heart.md',
    'hochschild/02-second-shift.md',
}


def read(path):
    return io.open(path, encoding='utf-8').read()


def han_count(s):
    return len(re.findall(r'[一-鿿]', s))


def split_sections(text):
    """把整章切成 (标题行, 正文) 列表；第一段是 H1 标题与引言。"""
    parts = re.split(r'^(## .+)$', text, flags=re.M)
    head = parts[0].rstrip()
    secs = []
    for i in range(1, len(parts), 2):
        secs.append((parts[i].strip(), parts[i + 1].strip('\n')))
    return head, secs


def merge(directory, filename, part_files):
    key = '%s/%s' % (directory, filename)
    if key in SKIP_DONE and not FORCE:
        print('SKIP %s（已合并并经人工修订）' % key)
        return True

    chunks = []
    for p in part_files:
        path = os.path.join(TMP, p)
        if not os.path.exists(path):
            print('  MISSING %s' % p)
            return False
        chunks.append(read(path).strip('\n'))

    head, secs = split_sections('\n\n'.join(chunks))

    # 按标准节序重组；同一节出现在多个 part 时按出现顺序拼接
    order = {}
    for name, body in secs:
        title = name[3:].strip()
        order.setdefault(title, []).append(body)

    problems = []
    out = [head]
    for want in SECTIONS:
        if want not in order:
            problems.append('缺节: %s' % want)
            continue
        body = '\n\n'.join(order[want])
        out.append('## %s\n\n%s' % (want, body))
    extra = [t for t in order if t not in SECTIONS]
    if extra:
        problems.append('非标准节: %s' % ' | '.join(extra))

    text = '\n\n'.join(out).rstrip() + '\n'

    if '�' in text:
        problems.append('含 U+FFFD')
    n_han = han_count(text)
    if n_han < 18000:
        problems.append('汉字数不足: %d' % n_han)
    n_notbut = len(re.findall(r'不是.{0,40}而是', text))
    if n_notbut > 12:
        problems.append('「不是A而是B」过多: %d' % n_notbut)
    if re.search(r'【[^】]*·[^】]*】', text):
        problems.append('含置信度标记')

    out_dir = os.path.join(ROOT, directory)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    io.open(os.path.join(out_dir, filename), 'w',
            encoding='utf-8', newline='').write(text)

    status = 'OK  ' if not problems else 'WARN'
    print('%s %s/%s  汉字 %d  字节 %d' %
          (status, directory, filename, n_han, len(text.encode('utf-8'))))
    for p in problems:
        print('     ! %s' % p)
    return not problems


def main():
    ok = True
    for d, f, parts in JOBS:
        ok = merge(d, f, parts) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
