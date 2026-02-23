# DSF Splitter

<p align="center">
  <strong>Bit-perfect DSD audio splitter using CUE sheets</strong><br>
  <sub>Split your DSF files without losing quality — perfect for creating track-separated albums</sub>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#examples">Examples</a> •
  <a href="#requirements">Requirements</a>
</p>

---

## Why DSF Splitter?

If you've ever tried to split a DSF (DSD Stream File) audio file, you know the pain — most tools either:
- ❌ Convert to PCM first (quality loss!)
- ❌ Introduce audible artifacts at cut points
- ❌ Don't support DSD format at all
- ❌ Require expensive professional software

**DSF Splitter solves this** with true **bit-perfect** precision:
- 🔪 **Cuts directly in DSD domain** — no PCM conversion, ever
- 🧬 **Bit-accurate splitting** — uses intelligent bit-shifting for non-byte-aligned cuts
- 🎵 **100% original quality** — every single bit is preserved

Your audio remains **exactly** as the original — just split into separate files.

## Features

- ✅ **Bit-perfect cutting in DSD domain** — cuts directly, never converts to PCM
- ✅ **No quality loss** — every single bit preserved, 100% original audio
- ✅ **Non-byte-aligned cuts** — handles any split point correctly with bit-shifting
- ✅ **Multi-track support** — splits entire albums in one command
- ✅ **Metadata preservation** — keeps track titles and performer info
- ✅ **Simple CLI** — No GUI, no bloat, just get the job done
- ✅ **Zero dependencies** — Pure Python, no external libraries needed

## Installation

### Manual Install

```bash
git clone https://github.com/your-repo/dsf-toolkit.git
cd dsf-toolkit
pip install .
```

### Portable (No Install)

```bash
python dsf_split.py yourfile.cue
```

## Usage

```bash
dsf_split [-h] [-o OUTPUT] [-f] [-v] cue_file
```

### Arguments

| Argument | Description |
|----------|-------------|
| `cue_file` | Path to your CUE sheet (required) |
| `-o, --output` | Output directory (default: same as CUE file) |
| `-f, --force` | Overwrite existing files |
| `-v, --verbose` | Show detailed progress |
| `-h, --help` | Show help message |

## Examples

### Basic Usage

Split a single album:

```bash
dsf_split "Album.cue"
```

### Output to Specific Folder

```bash
dsf_split "Album.cue" -o ./tracks
```

### Overwrite Existing Files

```bash
dsf_split "Album.cue" -f
```

### Verbose Mode

```bash
dsf_split "Album.cue" -v
```

## How It Works

DSF files use DSD (Direct Stream Digital) — a 1-bit per sample format. Unlike PCM audio, you can't simply cut on byte boundaries. Most tools fail because they convert to PCM first — **DSF Splitter doesn't**.

DSF Splitter operates **entirely in the DSD domain** using bit-shifting algorithms:
1. Read the original DSF file
2. Deinterleave multi-channel audio
3. Extract exact **bit ranges** for each track (not samples, not bytes — bits!)
4. Rebuild properly formatted DSF files

The result? **Bit-identical** tracks with no PCM conversion, no re-encoding, no quality loss.

## Requirements

- Python 3.8+
- No additional dependencies

## Supported Formats

- **Input:** DSF (DSD Stream File), DSD64/128/256
- **Channels:** Stereo, Multi-channel
- **CUE Sheet:** Standard format with INDEX 01

## Troubleshooting

### "Not a valid DSF file"
Make sure your file has the `.dsf` extension and is a valid DSD Stream File.

### "Only 1-bit DSD supported"
This tool only supports DSD (1-bit) format, not DST (DSD compressed).

### Files won't split
Check that your CUE sheet has `INDEX 01` for each track.

## License

MIT License — See [LICENSE](LICENSE) file.

---

**Author:** Vitaly Shinkarenko  
**Email:** vitaly@shinkarenko.net

If this tool saved you money or helped you enjoy your music, consider supporting the development!
