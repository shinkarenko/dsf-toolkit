#!/usr/bin/env python3
"""
DSF Splitter - Bit-perfect DSD audio splitter using CUE sheets
Uses bit-shifting to handle non-byte-aligned cuts correctly.

MIT License
Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import os
import re
import struct
import sys


DSD_CHUNK_SIZE = 28
FMT_CHUNK_SIZE = 52


def parse_cue(cue_path: str) -> tuple[dict, dict]:
    """Parse CUE sheet and return {filename: [tracks]} and global metadata."""
    with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    files_tracks: dict = {}
    current_file: str | None = None
    current_track: dict | None = None
    global_meta: dict = {"performer": None, "title": None}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(maxsplit=1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if command == "FILE":
            if current_track and current_file:
                files_tracks.setdefault(current_file, []).append(current_track)
                current_track = None
            match = re.search(r'"(.*?)"', arg)
            current_file = match.group(1) if match else arg.split()[0]

        elif command == "PERFORMER" and not current_track:
            global_meta["performer"] = arg.strip('"')

        elif command == "TITLE" and not current_track:
            global_meta["title"] = arg.strip('"')

        elif command == "TRACK":
            if current_track and current_file:
                files_tracks.setdefault(current_file, []).append(current_track)
            track_num = int(arg.split()[0])
            current_track = {
                "num": track_num,
                "start": None,
                "title": None,
                "performer": None,
            }

        elif command == "TITLE" and current_track:
            current_track["title"] = arg.strip('"')

        elif command == "PERFORMER" and current_track:
            current_track["performer"] = arg.strip('"')

        elif command == "INDEX":
            if arg[:2] == "01":
                m, s, f = map(int, arg[3:].split(":"))
                current_track["start"] = m * 60 + s + f / 75.0

    if current_track and current_file:
        files_tracks.setdefault(current_file, []).append(current_track)

    return files_tracks, global_meta


def read_dsf_header(f) -> dict:
    """Read and parse DSF file header."""
    f.seek(0)

    if f.read(4) != b"DSD ":
        raise ValueError("Not a valid DSF file")

    chunk_size = struct.unpack("<Q", f.read(8))[0]
    if chunk_size != 28:
        raise ValueError("Invalid DSD chunk")
    file_size = struct.unpack("<Q", f.read(8))[0]
    meta_offset = struct.unpack("<Q", f.read(8))[0]

    if f.read(4) != b"fmt ":
        raise ValueError("Missing fmt chunk")

    fmt_size = struct.unpack("<Q", f.read(8))[0]
    if fmt_size != 52:
        raise ValueError("Invalid fmt chunk")

    version = struct.unpack("<I", f.read(4))[0]
    format_id = struct.unpack("<I", f.read(4))[0]
    if format_id != 0:
        raise ValueError("Only raw DSD format supported (not DST)")

    channel_type = struct.unpack("<I", f.read(4))[0]
    channels = struct.unpack("<I", f.read(4))[0]
    sample_rate = struct.unpack("<I", f.read(4))[0]
    bits_per_sample = struct.unpack("<I", f.read(4))[0]
    sample_count = struct.unpack("<Q", f.read(8))[0]
    block_size = struct.unpack("<I", f.read(4))[0]
    reserved = f.read(4)

    if f.read(4) != b"data":
        raise ValueError("Missing data chunk")
    data_size = struct.unpack("<Q", f.read(8))[0]

    return {
        "channel_type": channel_type,
        "channels": channels,
        "sample_rate": sample_rate,
        "bits_per_sample": bits_per_sample,
        "sample_count": sample_count,
        "block_size": block_size,
        "reserved": reserved,
        "data_start": f.tell(),
        "data_size": data_size - 12,
    }


def deinterleave_channels(
    data: bytes, channels: int, block_size: int, total_samples: int
) -> list[bytearray]:
    """Deinterleave DSD audio data into separate channel arrays."""
    bytes_per_channel = (total_samples + 7) // 8
    num_blocks = (bytes_per_channel + block_size - 1) // block_size

    channel_data = [bytearray() for _ in range(channels)]

    for blk in range(num_blocks):
        for c in range(channels):
            offset = (blk * channels + c) * block_size
            read_len = min(block_size, len(data) - offset)
            if read_len > 0:
                channel_data[c].extend(data[offset : offset + read_len])

    return [ch[:bytes_per_channel] for ch in channel_data]


def extract_bits(ch_data: bytes, start_bit: int, num_bits: int) -> bytes:
    """Extract bits from bitstream using efficient integer operations."""
    if num_bits <= 0:
        return b""

    start_byte = start_bit // 8
    end_bit = start_bit + num_bits

    if start_byte >= len(ch_data):
        return b""

    src = ch_data[start_byte : (end_bit + 7) // 8]
    if not src:
        return b""

    src_int = int.from_bytes(src, "big")
    bit_offset = start_bit % 8

    if bit_offset == 0:
        src_int >>= len(src) * 8 - num_bits
    else:
        src_int = (src_int << bit_offset) >> (len(src) * 8 - num_bits)

    return (src_int & ((1 << num_bits) - 1)).to_bytes((num_bits + 7) // 8, "big")


def build_dsf_header(header: dict, sample_count: int, data_bytes: int) -> bytes:
    """Build DSF file header with correct sizes."""
    data_size = 12 + data_bytes
    file_size = DSD_CHUNK_SIZE + 4 + FMT_CHUNK_SIZE + 4 + data_size

    dsd_chunk = b"DSD " + struct.pack("<Q", DSD_CHUNK_SIZE)
    dsd_chunk += struct.pack("<Q", file_size) + struct.pack("<Q", 0)

    fmt_chunk = b"fmt " + struct.pack("<Q", FMT_CHUNK_SIZE)
    fmt_chunk += struct.pack("<I", 1)  # version
    fmt_chunk += struct.pack("<I", 0)  # format_id (raw DSD)
    fmt_chunk += struct.pack("<I", header["channel_type"])
    fmt_chunk += struct.pack("<I", header["channels"])
    fmt_chunk += struct.pack("<I", header["sample_rate"])
    fmt_chunk += struct.pack("<I", 1)  # bits per sample
    fmt_chunk += struct.pack("<Q", sample_count)
    fmt_chunk += struct.pack("<I", header["block_size"])
    fmt_chunk += header["reserved"]

    data_chunk = b"data" + struct.pack("<Q", data_size)

    return dsd_chunk + fmt_chunk + data_chunk


def split_dsf(
    cue_path: str,
    output_dir: str | None = None,
    overwrite: bool = False,
    verbose: bool = False,
):
    """Split DSF files based on CUE sheet."""
    cue_path = os.path.abspath(cue_path)
    dir_path = os.path.dirname(cue_path)

    if output_dir is None:
        output_dir = dir_path

    files_tracks, global_meta = parse_cue(cue_path)

    if not files_tracks:
        raise ValueError("No FILE entries found in CUE sheet")

    for dsf_file, tracks in files_tracks.items():
        if not tracks:
            continue

        dsf_path = os.path.join(dir_path, dsf_file)

        if verbose:
            print(f"Processing: {dsf_file}")

        with open(dsf_path, "rb") as f:
            header = read_dsf_header(f)

            if header["bits_per_sample"] != 1:
                raise ValueError("Only 1-bit DSD supported")

            total_duration = header["sample_count"] / header["sample_rate"]

            if verbose:
                print(
                    f"  Duration: {total_duration:.2f}s, "
                    f"{header['channels']}ch, {header['sample_rate']}Hz"
                )

            for i in range(len(tracks) - 1):
                tracks[i]["end"] = tracks[i + 1]["start"]
            tracks[-1]["end"] = total_duration

            f.seek(header["data_start"])
            original_data = f.read(header["data_size"])

            channel_data = deinterleave_channels(
                original_data,
                header["channels"],
                header["block_size"],
                header["sample_count"],
            )

            for track in tracks:
                start_sample = int(track["start"] * header["sample_rate"])
                sample_len = int(track["end"] * header["sample_rate"]) - start_sample

                new_channel_data = []
                for ch in channel_data:
                    new_ch = extract_bits(bytes(ch), start_sample, sample_len)
                    block_size = header["block_size"]
                    num_blocks = (len(new_ch) + block_size - 1) // block_size
                    new_ch += b"\x00" * (num_blocks * block_size - len(new_ch))
                    new_channel_data.append(new_ch)

                data_bytes = num_blocks * header["block_size"] * header["channels"]
                file_header = build_dsf_header(header, sample_len, data_bytes)

                # Clean filename: "01 - 01 - Title" -> "01 - Title"
                track_num = f"{track['num']:02d}"
                title = track.get("title") or f"Track {track_num}"
                # Remove duplicate track number if present
                if title.startswith(f"{track_num} - "):
                    title = title[len(track_num) + 3 :]
                filename = f"{track_num} - {title}.dsf"

                output_path = os.path.join(output_dir, filename)

                if os.path.exists(output_path) and not overwrite:
                    print(f"  Skipping (exists): {filename}")
                    continue

                with open(output_path, "wb") as out_f:
                    out_f.write(file_header)
                    for blk in range(num_blocks):
                        for ch in range(header["channels"]):
                            out_f.write(
                                new_channel_data[ch][
                                    blk * header["block_size"] : (blk + 1)
                                    * header["block_size"]
                                ]
                            )

                if verbose:
                    print(f"  Created: {filename}")
                else:
                    print(f"  {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Split DSF files using CUE sheets with bit-perfect accuracy"
    )
    parser.add_argument("cue_file", help="Path to CUE sheet")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        split_dsf(args.cue_file, args.output, args.force, args.verbose)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
