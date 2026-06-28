# simulation_database

光学仿真统一材料数据库，用于替换 `simulation_toykits/simulation_core/assets/database`。

各数据来源以 **git submodule** 形式集成，转换后的数据统一为 [refractiveindex.info](https://refractiveindex.info) 兼容 YAML（`tabulated nk`）。

## 子模块

| 子模块 | 说明 | 脚本 |
|--------|------|------|
| `og` | Oghma 原生材料 + 光谱 | `export.py` |
| `rii` | refractiveindex.info 官方数据 | `sync.py` |
| `fs` | FreeSnell nk.rwb | `export.py` |
| `vl` | VirtualLab 材料 | `export.py` |

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
python og/export.py --source /path/to/assets/database
python fs/export.py
python vl/export.py --csv-source /path/to/virtuallab_materials/materials
python rii/sync.py
```

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

## 共享库

`common/` 提供 CSV 读取、波长并集 cubic 插值、α→k 转换、YAML 写出及警告日志。
