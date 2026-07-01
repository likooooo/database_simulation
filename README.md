# simulation_database

光学仿真统一材料数据库，用于替换 `simulation_toykits/simulation_core/assets/database`。

各数据来源以 **git submodule** 形式集成，转换后的数据统一为 [refractiveindex.info](https://refractiveindex.info) 兼容 YAML（`tabulated nk`）。

## 子模块

| 子模块 | 说明 | 脚本 |
|--------|------|------|
| `og` | Oghma 原生材料 + 光谱 | `update_current_database.py` |
| `rii` | refractiveindex.info 官方数据 | `update_current_database.py` |
| `fs` | FreeSnell nk.rwb | `update_current_database.py` |
| `vl` | VirtualLab 材料 | `update_current_database.py` |
| `gf` | GranFilm SOPRA .nk | `update_current_database.py` |
| `of` | OpenFilters .mat | `update_current_database.py` |

## 安装

```bash
cd ~/repos/simulation_database
pip install -r requirements.txt
cp config.example.yaml config.yaml   # 按需修改路径
./setup_submodules.sh                # 子模块 git init 完成后注册 submodule
git submodule update --init --recursive
```

## 发布数据

将已转换的数据目录拷贝到外部路径（保留子模块目录结构）：

```bash
python database_release.py --dest ~/repos/simulation_toykits/simulation_core/assets/database
python database_release.py --dest /path/to/release --only oghma freesnell --clean
```

## 一键更新

```bash
python update_all.py
```

仅更新部分子模块：

```bash
python update_all.py --only oghma freesnell
```

## 单独运行

```bash
python og/update_current_database.py
python fs/update_current_database.py --scm /path/to/scm --rwb /path/to/nk.rwb
python gf/update_current_database.py
python of/update_current_database.py
python vl/update_current_database.py --csv-source /path/to/materials
python rii/update_current_database.py
```

各子模块脚本自包含，不依赖父仓库 `common/`；路径与选项由 CLI 或 `update_all.py` 传入。

## 输出格式

每个材料输出 `{name}.yml`（og / vl 按类别子目录；fs 为 `{symbol}.yml`）或 ri.info 既有布局：

```yaml
REFERENCES: |
COMMENTS: |
CONDITIONS: |
DATA:
  - type: tabulated nk
    data: |
        0.300 1.488 0.0
```

光谱数据（og）导出为 `{name}.yml`，`type: tabulated spectra`（波长 µm + 强度两列）。
