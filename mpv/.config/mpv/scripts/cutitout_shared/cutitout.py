"""
    cutitout: automatically cut silence from videos
    Copyright (C) 2020 Wolf Clement

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# Margin before and after a clip (in seconds)
clip_margin = 0.4
assert clip_margin >= 0.0

# How loud should noise be to be considered a sound?
audio_treshold = 0.01
assert audio_treshold > 0.0 and audio_treshold <= 1.0

# Minimum clip length (in seconds)
# Sounds shorter than that will be considered noise and cut.
min_clip_length = 0.2
assert min_clip_length > 0.0

# Minimum silence length to skip (in seconds)
min_skip_length = 2.0
assert min_skip_length > 2 * clip_margin


import audioop
import subprocess
import sys


# Returns the index of the first audio stream and its sample rate.
def get_sample_rate(filename) -> (int, int):
    streams = []
    probe = subprocess.check_output(
        ["ffprobe", "-show_streams", filename],
        encoding="utf-8",
        stderr=subprocess.DEVNULL,
    )

    for line in probe.split("\n"):
        if line == "[STREAM]":
            streams.append({})

        try:
            key, value = line.split("=")
            streams[-1][key] = value
        except ValueError:
            pass

    audio_stream = next(filter(lambda s: s["codec_type"] == "audio", streams))
    return int(audio_stream["index"]), int(audio_stream["sample_rate"])


if __name__ == "__main__":
    filename = sys.argv[1]
    minute = sys.argv[2]

    # Offset in seconds, at which we start searching for skips
    start_offset = float(sys.argv[2]) * 60.0

    # hh:mm:ss.xx formatted start offset to pass to ffmpeg
    hours = int(float(sys.argv[2]) / 60)
    minutes = int(sys.argv[2]) % 60
    start_str = f"{hours}:{minutes}:00.00"

    # Set the fragment size for 10ms long audio fragments (* 2 because we get 2 bytes)
    index, sample_rate = get_sample_rate(filename)
    fragment_length = int(sample_rate * 0.01 * 2)

    # Start an ffmpeg process that will pipe us raw audio fragments
    orig_audio = subprocess.Popen(
        [
            "ffmpeg",
            "-ss",
            start_str,
            "-t",
            "1:00.00",
            "-i",
            filename,
            # Output only one channel
            "-ac",
            "1",
            # Output raw 16bit samples for fast processing
            "-f",
            "s16le",
            # Open specific audio stream
            "-map",
            f"0:{index}",
            # Only use one core to avoid making mpv lag
            "-threads",
            "1",
            # Pipe to orig_audio
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    clips = []
    clip_index = 0
    loud_start = -1

    chunk_data = orig_audio.stdout.read(fragment_length)
    while chunk_data:
        # With *signed* 16 bit audio, the maximal absolute value is 2^15 = 32768.
        volume = audioop.max(chunk_data, 2) / 32768

        if loud_start == -1 and volume >= audio_treshold:
            loud_start = clip_index
        elif loud_start != -1 and volume < audio_treshold:
            # Remove sounds that are too short to be important
            if clip_index - loud_start > min_clip_length * 100:
                clips.append((loud_start, clip_index))
            loud_start = -1

        chunk_data = orig_audio.stdout.read(fragment_length)
        clip_index += 1

    # Turn clips into skips
    skips = []
    last_skip = 0.0
    index_to_time = lambda index: index / 100
    for clip in clips:
        clip_start = index_to_time(clip[0])
        clip_end = index_to_time(clip[1])

        if clip_start - last_skip < min_skip_length:
            last_skip = clip_end + clip_margin
        else:
            skips.append((last_skip, clip_start - clip_margin))
            last_skip = clip_end + clip_margin

    if 1.0 - last_skip >= min_skip_length:
        skips.append((last_skip, 1.0))

    skips = [(start_offset + s[0], start_offset + s[1]) for s in skips]
    skips = ["{" + f"{v[0]},{v[1]}" + "}" for v in skips]
    print("return {" + ",".join(skips) + "}")
