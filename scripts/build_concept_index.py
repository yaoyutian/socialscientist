#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为《概念索引.md》追加新思想家的概念段。

《概念索引.md》本身是**策展产物**（有的章被有意跳过，如马克思《关于费尔巴哈的提纲》），
因此本脚本不整体重生成，只为指定的新思想家生成章节段并追加到文件末尾。

收录标准（沿用 2026-11 策展后的口径）：
  - 标题带外文括注的，一律收录；
  - 或长度不超过 12 字、且不是「某某的意义／结构／背景」这类小节标题的，收录。
  被过滤掉的典型误收条目：「政变的意义」「传统的虚伪性」「英雄人物与群众的关系」。

用法：
    python scripts/build_concept_index.py --add hochschild arendt
    python scripts/build_concept_index.py --preview hochschild arendt
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THINKERS = [
    ('marx', '马克思'),
    ('weber', '韦伯'),
    ('foucault', '福柯'),
    ('bourdieu', '布尔迪厄'),
    ('hayek', '哈耶克'),
    ('durkheim', '涂尔干'),
    ('bauman', '鲍曼'),
    ('habermas', '哈贝马斯'),
    ('said', '萨义德'),
    ('hochschild', '霍克希尔德'),
    ('arendt', '阿伦特'),
]
NAMES = dict(THINKERS)

JUNK = re.compile(
    r'(^[一二三四五六七八九十]+[、.]'
    r'|^第[0-9一二三四五六七八九十]+[条章]'
    r'|的(意义|背景|结构|表现|作用|关系|定义|特征|内容|局限|问题|分析|讨论|比较|利用|虚伪性|历史|起源|演变|性质|形式|过程|逻辑|功能|地位|影响|机制|条件|原因|结果)$'
    r'|：|:)'
)

# 概念小节可能写成 `### 一、xxx` 或 `#### xxx`，两种都算
NUM_PREFIX = re.compile(r'^[一二三四五六七八九十]+、\s*')


def read(path):
    return io.open(path, encoding='utf-8').read()


def concepts_of(text):
    """取出「关键概念详解」一节下的所有小节标题（### 或 ####）。"""
    m = re.search(r'^## 关键概念详解', text, re.M)
    if not m:
        return []
    rest = text[m.end():]
    nxt = re.search(r'^## ', rest, re.M)
    if nxt:
        rest = rest[:nxt.start()]
    heads = re.findall(r'^#{3,4} (.+)$', rest, re.M)
    return [NUM_PREFIX.sub('', h).strip() for h in heads]


def keep(title):
    t = title.strip()
    if '（' in t:
        return True
    return len(t) <= 12 and not JUNK.search(t)


def section_for(directory, zh):
    d = os.path.join(ROOT, directory)
    if not os.path.isdir(d):
        return None, 0
    chapters = sorted(f for f in os.listdir(d) if re.match(r'^\d\d-.*\.md$', f))
    rows = []
    for name in chapters:
        text = read(os.path.join(d, name))
        title = text.split('\n', 1)[0].lstrip('# ').strip()
        picked = [c for c in concepts_of(text) if keep(c)]
        if not picked:
            continue
        rows.append((title, name, picked))
    n = sum(len(p) for _, _, p in rows)
    out = ['## %s（%d 条）\n' % (zh, n)]
    for title, name, picked in rows:
        out.append('### %s\n' % title)
        out.append('源文件：[%s/%s](%s/%s)\n' % (directory, name, directory, name))
        for p in picked:
            out.append('- %s' % p)
        out.append('')
    return '\n'.join(out).rstrip() + '\n', n


def main():
    args = sys.argv[1:]
    if '--add' not in args and '--preview' not in args:
        print(__doc__)
        return 1
    keys = [a for a in args[1:] if not a.startswith('--')]
    target = os.path.join(ROOT, '概念索引.md')
    cur = read(target)

    blocks = []
    total = 0
    for k in keys:
        if k not in NAMES:
            print('未知思想家: %s' % k)
            return 1
        sec, n = section_for(k, NAMES[k])
        if sec is None:
            print('目录不存在: %s' % k)
            return 1
        blocks.append(sec)
        total += n
        print('%-12s %d 条' % (NAMES[k], n))

    if '--preview' in args:
        print('\n'.join(blocks))
        return 0

    # 移除同名旧段（重跑时保持幂等）
    for k in keys:
        zh = NAMES[k]
        pat = re.compile(r'\n## %s（\d+ 条）\n.*?(?=\n## |\Z)' % re.escape(zh), re.S)
        cur = pat.sub('\n', cur)

    out = cur.rstrip() + '\n\n' + '\n'.join(blocks).rstrip() + '\n'
    # 表头的思想家计数同步
    count = len(re.findall(r'^## .+（\d+ 条）$', out, re.M))
    out = re.sub(r'^> 从.+?位思想家详述', '> 从%d位思想家详述' % count, out,
                 count=1, flags=re.M)
    io.open(target, 'w', encoding='utf-8', newline='').write(out)
    print('概念索引已更新：%d 位思想家，本次追加 %d 条' % (count, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
