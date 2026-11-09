#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建顶层合集与 AI预测 合并稿。

规则（与 README 第十节一致）：
  合集 = intro.md + 「## 目录」 + 各章
  各章前插入 HTML 锚点 <a id="chNN"></a>，供目录跳转
  章节内的相对链接在合并时去掉 `../` 前缀（合集位于仓库根目录）

用法：python scripts/build_aggregates.py
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THINKERS = [
    ('marx', '卡尔·马克思'),
    ('weber', '马克斯·韦伯'),
    ('foucault', '米歇尔·福柯'),
    ('bourdieu', '皮埃尔·布尔迪厄'),
    ('hayek', '弗里德里希·哈耶克'),
    ('durkheim', '埃米尔·涂尔干'),
    ('bauman', '齐格蒙特·鲍曼'),
    ('habermas', '尤尔根·哈贝马斯'),
    ('said', '爱德华·萨义德'),
    ('hochschild', '阿丽·霍克希尔德'),
    ('arendt', '汉娜·阿伦特'),
    ('schmitt', '卡尔·施米特'),
    ('mead', '乔治·米德'),
    ('goffman', '欧文·戈夫曼'),
    ('butler', '朱迪思·巴特勒'),
    ('beauvoir', '西蒙娜·德·波伏娃'),
    ('feixiaotong', '费孝通'),
    ('liangshuming', '梁漱溟'),
]

AI_FILES = [
    '01-主线-历史规律与AI定位.md',
    '02-人口维度.md',
    '03-劳动与工作维度.md',
    '04-组织结构维度.md',
    '05-知识与合法性维度.md',
]


def read(path):
    return io.open(path, encoding='utf-8').read()


def strip_suffix(title):
    """去掉标题末尾的“详细论述”，用于目录显示。"""
    return re.sub(r'详细论述\s*$', '', title).strip()


def build_thinker(directory, zh_name):
    intro = read(os.path.join(ROOT, directory, 'intro.md')).rstrip()
    chapters = sorted(
        f for f in os.listdir(os.path.join(ROOT, directory))
        if re.match(r'^\d\d-.*\.md$', f)
    )

    toc = ['## 目录', '', '> 点击章名跳转；也可使用编辑器的「文档大纲」。', '']
    body = []

    for i, name in enumerate(chapters, 1):
        content = read(os.path.join(ROOT, directory, name)).rstrip()
        first_line = content.split('\n', 1)[0]
        title = strip_suffix(first_line.lstrip('# ').strip())
        anchor = 'ch%02d' % i
        toc.append('- [第 %d 章　%s](#%s)' % (i, title, anchor))
        body.append('<a id="%s"></a>\n\n%s' % (anchor, content))

    # 目录放在标题与导语之后、正文之前：intro 的第 5 行是分隔线 `---`
    lines = intro.split('\n')
    if len(lines) < 5 or lines[4].strip() != '---':
        raise SystemExit(
            '%s/intro.md 第 5 行不是分隔线 `---`：'
            '目录插入位置的结构假设失效，请先修正 intro 结构' % directory)
    head = '\n'.join(lines[:5])
    rest = '\n'.join(lines[5:]).lstrip('\n')

    out = '\n\n'.join([head, '\n'.join(toc), rest, '---',
                       '\n\n---\n\n'.join(body)]) + '\n'
    out = out.replace('](../', '](')
    target = os.path.join(ROOT, zh_name + '-主要著作详述.md')
    io.open(target, 'w', encoding='utf-8', newline='').write(out)
    return len(chapters)


AI_HEADER = """# AI 与人类社会：基于社会理论的未来推演（完整版）

> 本文件是 [AI预测/](.) 目录五份专题文档的合并稿，供通读与检索使用；分章原稿仍保留在同目录，改动请直接改原稿。
>
> **置信度标注**采用两维体系（证据类型 · 确信度），规范见 [置信度规范](置信度规范.md)。
> **术语使用**见 [术语使用规范](../术语使用规范.md)。

## 目录

> 点击文档名跳转；也可使用编辑器的「文档大纲」。

"""


def build_ai():
    parts = []
    toc_lines = []
    for i, name in enumerate(AI_FILES, 1):
        content = read(os.path.join(ROOT, 'AI预测', name)).rstrip()
        title = content.split('\n', 1)[0].lstrip('# ').strip()
        anchor = 'ai%02d' % i
        toc_lines.append('- [%s](#%s)' % (title, anchor))
        parts.append('<a id="%s"></a>\n\n%s' % (anchor, content))
    out = AI_HEADER + '\n'.join(toc_lines) + '\n\n---\n\n' + '\n\n---\n\n'.join(parts) + '\n'
    io.open(os.path.join(ROOT, 'AI预测', 'AI预测-完整版.md'), 'w',
            encoding='utf-8', newline='').write(out)
    return len(AI_FILES)


def main():
    for d, zh in THINKERS:
        n = build_thinker(d, zh)
        print('%-10s %d 章' % (zh, n))
    print('AI预测 %d 份' % build_ai())


if __name__ == '__main__':
    main()
