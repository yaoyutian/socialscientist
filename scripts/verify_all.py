# -*- coding: utf-8 -*-
"""全库校验。用法：python scripts/verify_all.py"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SEC = ['背景与语境', '核心论点', '关键概念详解', '方法论', '主要内容',
       '学术接受与批评', '深远影响', '与其他著作的关系',
       '与现有思想家的交叉对照', '当代意义']

DIRS = ['marx', 'weber', 'foucault', 'bourdieu', 'hayek', 'durkheim',
        'bauman', 'habermas', 'said', 'hochschild', 'arendt']
AGG = {
    'marx': '卡尔·马克思-主要著作详述.md', 'weber': '马克斯·韦伯-主要著作详述.md',
    'foucault': '米歇尔·福柯-主要著作详述.md', 'bourdieu': '皮埃尔·布尔迪厄-主要著作详述.md',
    'hayek': '弗里德里希·哈耶克-主要著作详述.md', 'durkheim': '埃米尔·涂尔干-主要著作详述.md',
    'bauman': '齐格蒙特·鲍曼-主要著作详述.md', 'habermas': '尤尔根·哈贝马斯-主要著作详述.md',
    'said': '爱德华·萨义德-主要著作详述.md', 'hochschild': '阿丽·霍克希尔德-主要著作详述.md',
    'arendt': '汉娜·阿伦特-主要著作详述.md',
}

fails = []


def read(p):
    return io.open(p, encoding='utf-8').read()


def check(name, ok, detail=''):
    print('%-4s %s %s' % ('OK' if ok else 'FAIL', name, detail))
    if not ok:
        fails.append(name)


bad = []
for r, d, fs in os.walk('.'):
    if '.git' in r or 'archive' in r:
        continue
    for f in fs:
        if f.endswith('.md') and u'�' in read(os.path.join(r, f)):
            bad.append(os.path.join(r, f))
check('no-FFFD', not bad, str(bad))

# 标准节齐备且顺序正确；允许存在标准节之外的附加节（README 允许引言/结论/附录）
badsec = []
nchap = 0
for d in DIRS:
    for f in sorted(os.listdir(d)):
        if not re.match(r'^\d\d-.*\.md$', f):
            continue
        nchap += 1
        secs = re.findall(r'^## (.+)$', read(os.path.join(d, f)), re.M)
        pos, ok = -1, True
        for want in SEC:
            hit = [i for i, x in enumerate(secs) if x == want]
            if not hit:
                ok = False
                break
            if hit[0] <= pos:
                ok = False
                break
            pos = hit[0]
        if not ok:
            badsec.append('%s/%s' % (d, f))
check('chapter-10-sections', not badsec, '%d chapters; %s' % (nchap, badsec[:5]))

bad9 = []
for d in DIRS:
    for f in sorted(os.listdir(d)):
        if re.match(r'^\d\d-.*\.md$', f) and '## 与现有思想家的交叉对照' not in read(os.path.join(d, f)):
            bad9.append('%s/%s' % (d, f))
check('section9-literal', not bad9, str(bad9))

badagg = []
for d, agg in AGG.items():
    s = read(agg)
    anchors = re.findall(r'<a id="(ch\d\d)">', s)
    links = re.findall(r'\]\(#(ch\d\d)\)', s)
    chapters = sorted(f for f in os.listdir(d) if re.match(r'^\d\d-.*\.md$', f))
    if len(anchors) != len(chapters) or links != anchors:
        badagg.append('%s a=%d l=%d c=%d' % (agg, len(anchors), len(links), len(chapters)))
    for c in chapters:
        body = read(os.path.join(d, c)).strip().replace('](../', '](')
        if body not in s:
            badagg.append('%s missing %s' % (agg, c))
check('aggregates-toc-anchors', not badagg, str(badagg))

broken = []
for r, d, fs in os.walk('.'):
    if '.git' in r or 'archive' in r:
        continue
    for f in fs:
        if not f.endswith('.md'):
            continue
        p = os.path.join(r, f)
        for m in re.finditer(r'\]\(([^)#]+\.md)\)', read(p)):
            t = os.path.normpath(os.path.join(r, m.group(1)))
            if not os.path.exists(t):
                broken.append('%s -> %s' % (p, m.group(1)))
check('relative-links', not broken, str(broken[:5]))

badconf = []
for d in DIRS:
    for f in os.listdir(d):
        if f.endswith('.md') and re.search(r'【[^】]*·[^】]*】', read(os.path.join(d, f))):
            badconf.append('%s/%s' % (d, f))
check('thinker-no-confidence-marks', not badconf, str(badconf))

tot = 0
detail = []
for d in DIRS:
    n = 0
    for f in os.listdir(d):
        if f.endswith('.md'):
            n += len(re.findall(r'不是.{0,40}而是', read(os.path.join(d, f))))
    tot += n
    detail.append('%s:%d' % (d, n))
check('contrast-pattern-total', tot <= 640, 'total=%d (%s)' % (tot, ' '.join(detail)))

ai = [f for f in sorted(os.listdir('AI预测')) if f.endswith('.md') and f != 'AI预测-完整版.md']
nmark = sum(len(re.findall(r'【[^】]*·[^】]*】', read(os.path.join('AI预测', f)))) for f in ai)
check('ai-confidence-marks', nmark > 300, '%d marks / %d files' % (nmark, len(ai)))

nci = len(re.findall(r'^- ', read('概念索引.md'), re.M))
check('concept-index', nci > 600, '%d entries' % nci)

nterm = read('术语使用规范.md').count('\n### ')
check('term-spec', nterm >= 60, '%d entries' % nterm)

nointro = [d for d in DIRS if not os.path.exists(os.path.join(d, 'intro.md'))]
check('all-have-intro', not nointro, str(nointro))

print()
print('%d checks, %d failed' % (11, len(fails)))
sys.exit(1 if fails else 0)
