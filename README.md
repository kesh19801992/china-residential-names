# china-residential-names

中国住宅区 / 小区名称列表，提取自 [OpenStreetMap](https://www.openstreetmap.org)，供「流声 AI 输入法」的小区名词层使用。

A list of named residential areas in China extracted from OpenStreetMap, used as the residential-name layer of the Liusheng AI input method.

## 数据

| 项 | 值 |
|---|---|
| 来源 | OpenStreetMap，Geofabrik 中国区快照 `china-261017.osm.pbf`（2026-10-17） |
| 快照 MD5 | `6c0d3991f818cca90694b997be03cae5` |
| 提取对象 | 带 `name`（或 `name:zh`）的 `landuse=residential` way / relation，共 173,341 个 |
| 清洗后条数 | 114857 |

`residential_names.tsv` 列：

- `word`：名称（简体）
- `count`：快照中同名住宅区的个数（用于同音排序）
- `pinyin`：主读音（无声调，ü 记作 v；pypinyin 按词组注音，**未逐条人工校对**）
- `alt_pinyins`：常见多音字（长/乐/重/行/厦……）的备选读音，逗号分隔

清洗规则见 `scripts/clean.py` 开头：繁转简、去括号注释、带「·」「-」只取主名、去掉末尾分期/分区/楼栋后缀（一期、A区、3号楼、东区……）、只留 3~10 个汉字、剔除「小区」「宿舍」等泛称、同名合并计数。

名称以 OSM 贡献者的标注为准，可能有错漏、重名或已不存在的楼盘；覆盖以城市为主，县城和乡镇较少。发现问题请直接到 OpenStreetMap 上修改。

## 复现

```bash
pip install osmium opencc pypinyin
python3 scripts/extract.py china-261017.osm.pbf raw.tsv
python3 scripts/clean.py raw.tsv residential_names.tsv
node scripts/gen_binary.mjs residential_names.tsv OUT_DIR   # 生成输入法使用的 pinyin_residential_t9.bin
```

`pinyin_residential_t9.bin` 是本列表的九宫格数字码索引（VFPD 格式：32 字节头 + 键偏移表 + 值偏移表 + 键区 + 值区，值以 0x1F 分隔），由上面最后一步从 `residential_names.tsv` 确定性生成，App 内打包的就是这份文件。

## 授权

- **数据**（`residential_names.tsv` 及由其生成的索引）：© OpenStreetMap contributors，按 [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/) 授权，全文见 `LICENSE`。版权说明：<https://www.openstreetmap.org/copyright>。
- **脚本**（`scripts/`）：MIT，见 `LICENSE-scripts`。

Contains information from OpenStreetMap, which is made available here under the Open Database License (ODbL).
