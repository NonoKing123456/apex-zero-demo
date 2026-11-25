import os
import subprocess
from pathlib import Path

ROOT = Path(r"d:\WorkSpace\Video-Generation")
VID_DIR = ROOT / "outputs" / "videos"
AUD_DIR = ROOT / "outputs" / "audio"
WORK_DIR = ROOT / "outputs" / "build_tmp"
WORK_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUT = ROOT / "outputs" / "APEX_ZERO_零号弯道_30s_FINAL_1080P.mp4"
FONT_ZH = r"C\:/Windows/Fonts/Noto Sans SC Medium (TrueType).otf"
FONT_EN = r"C\:/Windows/Fonts/bahnschrift.ttf"


def run(cmd):
    print(">>", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def prep_vo():
    """Trim silence and tighten VO_01 pacing while keeping deep voice."""
    # VO_01: keep 0.30-3.32s + 3.82-6.58s, slight 1.16x tempo -> ~4.45s
    vo1 = WORK_DIR / "vo1.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(AUD_DIR / "VO_01.mp3"),
        "-filter_complex",
        "[0:a]atrim=0.30:3.32,asetpts=PTS-STARTPTS[a1];"
        "[0:a]atrim=3.80:6.58,asetpts=PTS-STARTPTS[a2];"
        "[a1][a2]concat=n=2:v=0:a=1,atempo=1.18,highpass=f=75,"
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=60,"
        "volume=1.55,aresample=48000,aformat=channel_layouts=stereo[out]",
        "-map", "[out]", str(vo1)
    ])

    for idx, src_name, vol in [
        (2, "VO_02.mp3", 1.50),
        (3, "VO_03.mp3", 1.55),
        (4, "VO_04.mp3", 1.50),
    ]:
        out_wav = WORK_DIR / f"vo{idx}.wav"
        run([
            "ffmpeg", "-y", "-v", "error", "-i", str(AUD_DIR / src_name),
            "-af",
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
            "highpass=f=90,equalizer=f=3200:t=q:w=1.2:g=2.5,"
            f"acompressor=threshold=-18dB:ratio=3:attack=5:release=60,volume={vol},"
            "aresample=48000,aformat=channel_layouts=stereo",
            str(out_wav)
        ])


def prep_bgm_and_boom():
    """Build structured BGM track (0-21.1s main + 26-30s breakdown at 21.1s) + 55Hz sub-bass boom."""
    bgm_out = WORK_DIR / "bgm_track.wav"
    # Main 0-21.1s + breakdown 25.8-30.0s (4.2s) -> fade out by 25.5s
    # Apply ducking windows during VO lines:
    # VO1: 0.15-4.55, VO2: 4.75-8.00, VO3: 12.25-14.95, VO4: 22.1-24.9
    duck_expr = (
        "if(between(t,0.15,4.55),0.45,"
        "if(between(t,4.75,8.00),0.48,"
        "if(between(t,8.00,12.00),0.72,"
        "if(between(t,12.25,14.95),0.55,"
        "if(between(t,15.30,21.10),0.92,"
        "if(between(t,21.10,26.10),0.36,0.0))))))"
    )
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(AUD_DIR / "BGM_30s.mp3"),
        "-filter_complex",
        "[0:a]atrim=0:21.10,asetpts=PTS-STARTPTS,afade=t=out:st=20.90:d=0.20[m1];"
        "[0:a]atrim=25.80:30.00,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.18,afade=t=out:st=3.20:d=1.00[m2];"
        "[m1][m2]concat=n=2:v=0:a=1,apad=whole_dur=29.1,"
        f"volume='{duck_expr}':eval=frame,volume=0.58,"
        "aresample=48000,aformat=channel_layouts=stereo[out]",
        "-map", "[out]", str(bgm_out)
    ])

    # Deep cinematic sub-bass boom ("Dong") for 26.1s title card hit
    boom = WORK_DIR / "boom.wav"
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        "aevalsrc='0.75*exp(-1.9*t)*sin(2*PI*(58-22*min(t,0.4))*t)"
        "+0.35*exp(-6.0*t)*sin(2*PI*116*t)':s=48000:d=2.4",
        "-af", "lowpass=f=180,afade=t=in:st=0:d=0.015,afade=t=out:st=1.7:d=0.7,"
        "aformat=channel_layouts=stereo",
        str(boom)
    ])


def build_title_card():
    """Render 3.0s 1080p 60fps sleek black cinematic title card."""
    title_mp4 = WORK_DIR / "seg9_title.mp4"
    vf = (
        "drawbox=x=840:y=536:w=240:h=3:color=0xE08E79@0.95:t=fill,"
        f"drawtext=fontfile='{FONT_EN}':text='A P E X   Z E R O':"
        "fontcolor=0xF5F7FA:fontsize=74:x=(w-text_w)/2:y=430,"
        f"drawtext=fontfile='{FONT_ZH}':text='零   号   弯   道':"
        "fontcolor=0xEAECEF:fontsize=46:x=(w-text_w)/2:y=572,"
        f"drawtext=fontfile='{FONT_EN}':text='ORIGINAL  AI  CINEMA  DEMO':"
        "fontcolor=0x8D96A5@0.85:fontsize=20:x=(w-text_w)/2:y=668,"
        "fade=t=in:st=0.05:d=0.45,fade=t=out:st=2.35:d=0.65"
    )
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "color=c=0x06070A:s=1920x1080:r=60:d=3.0",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=3.0",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-shortest", str(title_mp4)
    ])


def build_video_segments():
    """Cut, 1080p upscale+sharpen, unify Morandi grading, and adjust SFX volume per shot."""
    grade = (
        "scale=1920:1080:flags=lanczos,"
        "unsharp=5:5:0.42:5:5:0.0,"
        "eq=saturation=0.95:contrast=1.03:brightness=0.008,"
        "fps=60,format=yuv420p"
    )
    specs = [
        ("seg1", "S01.mp4", 0.00, 4.00, 0.90, "fade=t=in:st=0:d=0.25"),
        ("seg2", "S02.mp4", 0.00, 4.00, 0.75, ""),
        ("seg3", "S03.mp4", 0.00, 4.00, 1.35, ""),
        ("seg4", "S04.mp4", 0.00, 3.30, 0.85, ""),
        ("seg5", "S05.mp4", 0.00, 2.40, 1.20, ""),
        ("seg6", "S04.mp4", 3.20, 4.00, 1.05, ""),  # 0.8s smirk flash-cut!
        ("seg7", "S05.mp4", 2.40, 5.00, 1.25, ""),
        ("seg8", "S06.mp4", 0.00, 5.00, 1.45, "fade=t=in:st=0:d=0.22:color=0xE8DCD8,fade=t=out:st=4.82:d=0.18"),
    ]
    seg_files = []
    for name, src, st, ed, sfx_vol, extra_vf in specs:
        out_mp4 = WORK_DIR / f"{name}.mp4"
        vf = grade + (f",{extra_vf}" if extra_vf else "")
        dur = round(ed - st, 3)
        af = (
            f"volume={sfx_vol},afade=t=in:st=0:d=0.03,"
            f"afade=t=out:st={max(0, dur - 0.04):.3f}:d=0.04,"
            "aresample=48000,aformat=channel_layouts=stereo"
        )
        run([
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{st:.3f}", "-to", f"{ed:.3f}",
            "-i", str(VID_DIR / src),
            "-vf", vf, "-af", af,
            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "pcm_s16le", str(out_mp4)
        ])
        seg_files.append(out_mp4)
    seg_files.append(WORK_DIR / "seg9_title.mp4")
    return seg_files


def write_ass_subtitles():
    """Minimalist high-fashion cinema subtitles synced to exact VO timings."""
    ass_path = WORK_DIR / "subs.ass"
    ass_content = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Villain,Noto Sans SC Medium,40,&H00E8DFD8,&H000000FF,&H7010141A,&H90000000,0,0,0,0,100,100,2.5,0,1,1.6,2.2,2,120,120,58,1
Style: Hero,Noto Sans SC Medium,44,&H00F8F6FA,&H000000FF,&H7012151C,&H90000000,0,0,0,0,100,100,3.5,0,1,1.8,2.4,2,120,120,58,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.15,0:00:02.45,Villain,,0,0,0,,{\fad(150,150)}三年前，零号弯道废了三台车
Dialogue: 0,0:00:02.45,0:00:04.55,Villain,,0,0,0,,{\fad(120,180)}你踩着十厘米高跟鞋，上赛道？
Dialogue: 0,0:00:04.80,0:00:08.15,Hero,,0,0,0,,{\fad(150,200)}那是因为，他们只会踩刹车。
Dialogue: 0,0:00:12.25,0:00:15.05,Hero,,0,0,0,,{\fad(150,180)}零号弯道，没有刹车线。
Dialogue: 0,0:00:22.10,0:00:25.15,Hero,,0,0,0,,{\fad(180,260)}下一局，赌你的全部。
"""
    ass_path.write_text(ass_content, encoding="utf-8")
    return ass_path


def assemble_final(seg_files, ass_path):
    """Concat video+SFX, mix VO+BGM+Boom, burn cinema subtitles, export 1080p 60fps master."""
    list_txt = WORK_DIR / "concat_list.txt"
    list_txt.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in seg_files),
        encoding="utf-8"
    )
    concat_mp4 = WORK_DIR / "concat_base.mp4"
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_txt),
        "-c", "copy", str(concat_mp4)
    ])

    ass_esc = ass_path.as_posix().replace(":", r"\:")
    # Mix: [0:a] SFX + [1:a] BGM + VO1@150ms + VO2@4800ms + VO3@12250ms + VO4@22100ms + Boom@26100ms
    filter_complex = (
        "[0:a]aresample=48000,volume=0.95[sfx];"
        "[1:a]aresample=48000[bgm];"
        "[2:a]adelay=150|150[v1];"
        "[3:a]adelay=4800|4800[v2];"
        "[4:a]adelay=12250|12250[v3];"
        "[5:a]adelay=22100|22100[v4];"
        "[6:a]adelay=26100|26100,volume=1.15[boom];"
        "[sfx][bgm][v1][v2][v3][v4][boom]amix=inputs=7:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.95:attack=3:release=40[aout]"
    )
    run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(concat_mp4),
        "-i", str(WORK_DIR / "bgm_track.wav"),
        "-i", str(WORK_DIR / "vo1.wav"),
        "-i", str(WORK_DIR / "vo2.wav"),
        "-i", str(WORK_DIR / "vo3.wav"),
        "-i", str(WORK_DIR / "vo4.wav"),
        "-i", str(WORK_DIR / "boom.wav"),
        "-vf", f"ass='{ass_esc}'",
        "-filter_complex", filter_complex,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-movflags", "+faststart",
        str(FINAL_OUT)
    ])
    print("DONE ->", FINAL_OUT)


if __name__ == "__main__":
    prep_vo()
    prep_bgm_and_boom()
    build_title_card()
    segs = build_video_segments()
    ass = write_ass_subtitles()
    assemble_final(segs, ass)
