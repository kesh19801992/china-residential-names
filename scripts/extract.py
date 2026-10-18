#!/usr/bin/env python3
"""从 OSM PBF 提取带名字的住宅区(landuse=residential 的 way/relation)。

用法: python3 extract.py china-YYMMDD.osm.pbf raw.tsv
输出 TSV 列: osm_type  osm_id  name  name:zh
数据 © OpenStreetMap contributors,ODbL 1.0。
"""
import sys
import osmium


class Handler(osmium.SimpleHandler):
    def __init__(self, out):
        super().__init__()
        self.out = out
        self.n = 0

    def _emit(self, kind, obj):
        tags = obj.tags
        if tags.get('landuse') != 'residential':
            return
        name = tags.get('name') or ''
        zh = tags.get('name:zh') or ''
        if not name and not zh:
            return
        clean = lambda s: s.replace('\t', ' ').replace('\n', ' ')
        self.out.write(f'{kind}\t{obj.id}\t{clean(name)}\t{clean(zh)}\n')
        self.n += 1

    def way(self, w):
        self._emit('way', w)

    def relation(self, r):
        self._emit('relation', r)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(dst, 'w', encoding='utf-8') as out:
        out.write('osm_type\tosm_id\tname\tname_zh\n')
        h = Handler(out)
        h.apply_file(src, locations=False)
    print(f'extracted {h.n} named residential areas', file=sys.stderr)


if __name__ == '__main__':
    main()
