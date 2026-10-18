#!/usr/bin/env node
// 把 clean.py 产出的小区名 TSV 编成输入法查表(VFPD 格式,与 gen_domain_binary 同构,端上 DictBlob 读):
//   pinyin_residential_t9.bin    九宫格数字码(含多音字备选读音的码) → 词
// 26 键不另存全拼表:端上把全拼转成数字码查这张表,再核对读音(省一半包体)。
// 用法: node scripts/osm_residential/gen_binary.mjs residential_names.tsv OUT_DIR
// 数据 © OpenStreetMap contributors,ODbL 1.0。
import fs from 'node:fs';
import path from 'node:path';

const PER_KEY = 8;
const VERSION = 1;
const T9 = '22233344455566677778889999';
const digits = (py) => [...py].map((c) => T9[c.charCodeAt(0) - 97]).join('');

function writeBlob(outPath, map) {
  const enc = new TextEncoder();
  const entries = [...map.entries()].sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  const keyBufs = entries.map(([k]) => {
    if (!/^[a-z0-9]+$/.test(k)) { throw new Error(`键含非法字符: ${k}`); }
    return enc.encode(k);
  });
  const valBufs = entries.map(([, ws]) => enc.encode(ws.join('\x1f')));
  const count = entries.length;
  const keyOffTable = 32;
  const valOffTable = keyOffTable + (count + 1) * 4;
  const keyBlobStart = valOffTable + (count + 1) * 4;
  const keySize = keyBufs.reduce((s, b) => s + b.length, 0);
  const valBlobStart = keyBlobStart + keySize;
  const total = valBlobStart + valBufs.reduce((s, b) => s + b.length, 0);
  const out = new Uint8Array(total);
  const dv = new DataView(out.buffer);
  out.set(enc.encode('VFPD'), 0);
  dv.setUint32(4, VERSION, true);
  dv.setUint32(8, count, true);
  dv.setUint32(12, keyOffTable, true);
  dv.setUint32(16, valOffTable, true);
  dv.setUint32(20, keyBlobStart, true);
  dv.setUint32(24, valBlobStart, true);
  let ko = 0;
  let vo = 0;
  for (let i = 0; i < count; i++) {
    dv.setUint32(keyOffTable + i * 4, ko, true);
    dv.setUint32(valOffTable + i * 4, vo, true);
    out.set(keyBufs[i], keyBlobStart + ko);
    out.set(valBufs[i], valBlobStart + vo);
    ko += keyBufs[i].length;
    vo += valBufs[i].length;
  }
  dv.setUint32(keyOffTable + count * 4, ko, true);
  dv.setUint32(valOffTable + count * 4, vo, true);
  fs.writeFileSync(outPath, out);
  return { count, bytes: total };
}

const [src, outDir] = process.argv.slice(2);
if (!outDir) { throw new Error('usage: residential_names.tsv OUT_DIR'); }
const t9 = new Map();
const add = (map, key, word) => {
  let arr = map.get(key);
  if (arr === undefined) { arr = []; map.set(key, arr); }
  if (arr.length < PER_KEY && !arr.includes(word)) { arr.push(word); }
};
let words = 0;
for (const line of fs.readFileSync(src, 'utf8').trim().split('\n').slice(1)) {
  const [word, , py, alts] = line.split('\t');
  if (word.includes('\x1f')) { throw new Error('词内含 0x1F'); }
  words++;
  for (const key of [py, ...(alts ? alts.split(',') : [])]) {
    add(t9, digits(key), word);
  }
}
const b = writeBlob(path.join(outDir, 'pinyin_residential_t9.bin'), t9);
console.log(`words=${words} t9=${b.count}键/${(b.bytes / 1048576).toFixed(2)}MB`);
