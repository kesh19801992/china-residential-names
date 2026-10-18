#!/usr/bin/env python3
"""把 extract.py 的原始住宅区名清洗成输入法词条,并注音。

用法: python3 clean.py raw.tsv residential_names.tsv
输出 TSV 列: word  count  pinyin(主读音,无声调,ü 记作 v)  alt_pinyins(逗号分隔,多音字备选)
数据 © OpenStreetMap contributors,ODbL 1.0。

规则:
- 名字取 name,非中文时取 name:zh;繁体转简体;去括号注释;
- 带「·」「-」「—」的只取主名(碧云别墅·银杏苑 → 碧云别墅);
- 反复去掉末尾的分期/分区/楼栋后缀(一期、A区、3号楼、2栋、5幢、B座、7号院、东区;「北苑」等不去);
- 只留纯汉字、3~10 字;剔除泛称(小区、住宅区、宿舍……)和以泛称独立成名的条目;
- 同名合并计数,按出现次数降序、再按字典序。
"""
import re
import sys
import unicodedata
from collections import Counter
from itertools import product

import opencc
from pypinyin import Style, lazy_pinyin

T2S = opencc.OpenCC('t2s')
HAN = re.compile(r'^[一-鿿]+$')
NUM = '0-9０-９一二三四五六七八九十百〇零壹贰叁肆伍陆柒捌玖拾'
SUFFIX = re.compile(
    rf'(?:[{NUM}]+|[A-Za-z]+)(?:期|区|号楼|号院|楼|栋|幢|座|号|街坊|组团|组|标段|地块|批次)?$'
    r'|[东西南北中]区$'
)
# 只给这些常被读错的多音字生成备选读音(pypinyin 的生僻读音如 园→wan、万→mo 只会添乱)
POLY = {
    '长': ('chang', 'zhang'), '乐': ('le', 'yue'), '重': ('zhong', 'chong'), '行': ('xing', 'hang'),
    '朝': ('chao', 'zhao'), '曾': ('ceng', 'zeng'), '厦': ('xia', 'sha'), '都': ('du', 'dou'),
    '会': ('hui', 'kuai'), '单': ('dan', 'shan'), '藏': ('cang', 'zang'), '传': ('chuan', 'zhuan'),
    '调': ('diao', 'tiao'), '省': ('sheng', 'xing'), '盛': ('sheng', 'cheng'), '降': ('jiang', 'xiang'),
    '沈': ('shen', 'chen'), '解': ('jie', 'xie'), '曲': ('qu',), '宿': ('su', 'xiu'), '泊': ('bo', 'po'),
    '堡': ('bao', 'pu'), '洞': ('dong',), '蔚': ('wei', 'yu'), '尉': ('wei', 'yu'), '翟': ('zhai', 'di'),
}
# 去后缀时这些整词结尾不动(东区/西区 是后缀,但「新区」「社区」「园区」「小区」是名字的一部分)
KEEP_TAILS = ('新区', '社区', '园区', '小区', '景区', '城区', '校区', '厂区', '矿区', '林区', '街区',
              '花园区', '生活区', '住宅区', '居住区', '新村区', '家属区')
GENERIC = {
    '小区', '住宅区', '居民区', '居住区', '生活区', '家属院', '家属区', '宿舍', '宿舍区', '职工宿舍',
    '居民楼', '住宅楼', '住宅小区', '安置房', '安置小区', '安置区', '还建房', '回迁房', '商品房',
    '别墅区', '公寓', '新村', '社区', '村庄', '住宅', '民居', '楼盘', '工地', '新小区', '老小区',
    '学生公寓', '职工公寓', '教师公寓', '人才公寓', '员工宿舍', '学生宿舍', '教职工宿舍',
}
PAREN = re.compile(r'[（(【\[].*?[）)】\]]')
SPLIT = re.compile(r'[·•・\-—–_/／|｜,，、]')


def is_han(s):
    return bool(HAN.match(s))


def strip_suffix(s):
    for _ in range(4):
        if s.endswith(KEEP_TAILS):
            break
        t = SUFFIX.sub('', s)
        if t == s or len(t) < 2:
            break
        s = t
    return s


def normalize(name):
    s = unicodedata.normalize('NFKC', name).strip()
    s = T2S.convert(s)
    s = PAREN.sub('', s)
    s = SPLIT.split(s)[0]
    s = re.sub(r'\s+', '', s)
    return strip_suffix(s)


def readings(word):
    """主读音(pypinyin 按词组消歧)+ 常见多音字的备选,总数不超过 4。"""
    per = lazy_pinyin(word, style=Style.NORMAL, v_to_u=False)
    main = ''.join(per).replace('ü', 'v')
    choices = []
    for ch, py in zip(word, per):
        opts = [py] + [p for p in POLY.get(ch, ()) if p != py]
        choices.append(opts)
    alts = []
    if sum(1 for c in choices if len(c) > 1) <= 2:
        for combo in product(*choices):
            key = ''.join(combo).replace('ü', 'v')
            if key != main and key not in alts:
                alts.append(key)
            if len(alts) >= 3:
                break
    return main, alts


def main():
    src, dst = sys.argv[1], sys.argv[2]
    counts = Counter()
    rows = 0
    with open(src, encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 4:
                continue
            rows += 1
            name, zh = parts[2], parts[3]
            cand = name if re.search(r'[一-鿿]', name) else zh
            if not cand:
                continue
            w = normalize(cand)
            if not is_han(w) or not (3 <= len(w) <= 10) or w in GENERIC:
                continue
            counts[w] += 1
    words = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    with open(dst, 'w', encoding='utf-8') as out:
        out.write('word\tcount\tpinyin\talt_pinyins\n')
        for w, c in words:
            main_py, alts = readings(w)
            if not re.fullmatch(r'[a-z]+', main_py):
                continue
            out.write(f'{w}\t{c}\t{main_py}\t{",".join(alts)}\n')
    print(f'rows={rows} names={len(words)}', file=sys.stderr)


if __name__ == '__main__':
    main()
