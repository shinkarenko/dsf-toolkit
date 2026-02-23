# DSF Splitter

<p align="center">
  <strong>使用 CUE 表格进行位完美的 DSD 音频分割</strong><br>
  <sub>无损分割您的 DSF 文件 — 非常适合创建分轨专辑</sub>
</p>

<p align="center">
  <a href="#功能">功能</a> •
  <a href="#安装">安装</a> •
  <a href="#使用方法">使用方法</a> •
  <a href="#示例">示例</a> •
  <a href="#要求">要求</a>
</p>

---

## 为什么选择 DSF Splitter？

如果您曾经尝试分割 DSF（DSD Stream File）音频文件，您就知道其中的痛点 — 大多数工具要么：
- ❌ 先转换成 PCM（质量损失！）
- ❌ 在切割点产生可听见的杂音
- ❌ 完全不支持 DSD 格式
- ❌ 需要昂贵的专业软件

**DSF Splitter 通过真正的位精度解决这些问题**：
- 🔪 **直接在 DSD 域中切割** — 绝不转换为 PCM
- 🧬 **位级精确分割** — 使用智能位偏移处理非字节对齐的切割点
- 🎵 **100% 原始质量** — 每一位都被保留

您的音频与原始文件**完全相同** — 只是被分割成单独的文件。

## 功能

- ✅ **在 DSD 域中进行位完美切割** — 直接切割，绝不转换为 PCM
- ✅ **无质量损失** — 每一位都被保留，100% 原始音频
- ✅ **非字节对齐切割** — 使用位偏移正确处理任何分割点
- ✅ **多轨支持** — 一个命令分割整张专辑
- ✅ **保留元数据** — 保留曲目标题和演出者信息
- ✅ **简洁 CLI** — 无 GUI，无冗余
- ✅ **零依赖** — 纯 Python，无需外部库

## 安装

### 手动安装

```bash
git clone https://github.com/您的仓库/dsf-toolkit.git
cd dsf-toolkit
pip install .
```

### 便携版（无需安装）

```bash
python dsf_split.py 您的文件.cue
```

## 使用方法

```bash
dsf_split [-h] [-o 输出目录] [-f] [-v] cue文件
```

### 参数

| 参数 | 说明 |
|----------|-------------|
| `cue文件` | CUE 表格路径（必填） |
| `-o, --output` | 输出目录（默认：与 CUE 文件相同） |
| `-f, --force` | 覆盖现有文件 |
| `-v, --verbose` | 显示详细进度 |
| `-h, --help` | 显示帮助信息 |

## 示例

### 基本用法

分割专辑：

```bash
dsf_split "专辑.cue"
```

### 指定输出文件夹

```bash
dsf_split "专辑.cue" -o ./tracks
```

### 覆盖现有文件

```bash
dsf_split "专辑.cue" -f
```

### 详细模式

```bash
dsf_split "专辑.cue" -v
```

## 工作原理

DSF 文件使用 DSD（Direct Stream Digital）— 一种每采样 1 位的格式。与 PCM 音频不同，您不能简单地按字节边界切割。大多数工具失败是因为它们先转换成 PCM — **DSF Splitter 不会这样做**。

DSF Splitter **完全在 DSD 域中运行**，使用位偏移算法：
1. 读取原始 DSF 文件
2. 解交织多声道音频
3. 为每个曲目提取精确的**位范围**（不是采样，不是字节 — 是位！）
4. 重建正确格式化的 DSF 文件

结果？**位级相同**的曲目，无 PCM 转换，无重新编码，无质量损失。

## 要求

- Python 3.8+
- 无额外依赖

## 支持的格式

- **输入：** DSF（DSD Stream File），DSD64/128/256
- **声道：** 立体声、多声道
- **CUE 表格：** 标准格式，带 INDEX 01

## 故障排除

### "Not a valid DSF file"
确保您的文件具有 `.dsf` 扩展名，并且是有效的 DSD Stream File。

### "Only 1-bit DSD supported"
此工具仅支持 DSD（1位）格式，不支持 DST（DSD 压缩格式）。

### 文件无法分割
检查您的 CUE 表格是否为每个曲目包含 `INDEX 01`。

## 许可证

MIT 许可证 — 见 [LICENSE](LICENSE) 文件。

---

**作者：** 什金连科·维塔利（Shinkarenko Vitaly）  
**邮箱：** vitaly@shinkarenko.net

如果这个工具为您省了钱或帮助您享受音乐，请考虑支持开发！
