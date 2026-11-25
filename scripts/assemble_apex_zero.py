import subprocess
from pathlib import Path

ROOT = Path(r"d:\WorkSpace\Video-Generation")
VID_DIR = ROOT / "outputs" / "videos"
AUD_DIR = ROOT / "outputs" / "audio"
WORK_DIR = ROOT / "outputs" / "build_tmp_v2"
WORK_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUT = ROOT / "outputs" / "APEX_ZERO_零号弯道_30s_FINAL_1080P.mp4"
BGM_SRC = AUD_DIR / "BGM_V2A_dark_industrial.mp3"
FONT_ZH = r"C\:/Windows/Fonts/Noto Sans SC Medium (TrueType).otf"
FONT_EN = r"C\:/Windows/Fonts/bahnschrift.ttf"

TOTAL_DUR = 26.85


def run(cmd):
    print(">>", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def prep_vo_bus():
    """Tighten VO_01 to fit cleanly inside S01 (no overlap onto S02), add subtle tunnel/open-air reverb, build unified VO bus."""
    # VO_01: keep 0.32-3.28 (2.96s) + 3.88-6.54 (2.66s) = 5.62s -> silence trim + 1.30x? No, 1.30x too fast.
    # Better: trim internal pause 1.24-1.56 as well -> ~5.25s, atempo=1.22 -> ~4.3s; wait: let's target 3.50s cleanly without chipmunk!
    # Check speech length: 0.34-1.23 (0.89s) + 0.14s gap + 1.57-3.28 (1.71s) + 0.16s gap + 3.90-6.54 (2.64s) = 5.54s?
    # Ah! At 1.18x that's 4.69s. Wait: if S01 is 3.85s and VO_01 starts at 0.08s, let's make S01=3.95s, and trim VO_01 at 1.22x (~3.90s -> ends at 3.98s, zero bleed onto S02!)
    vo1 = WORK_DIR / "vo1.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(AUD_DIR / "VO_01.mp3"),
        "-filter_complex",
        "[0:a]atrim=0.35:1.24,asetpts=PTS-STARTPTS[p1];"
        "[0:a]atrim=1.48:3.28,asetpts=PTS-STARTPTS[p2];"
        "[0:a]atrim=3.86:6.54,asetpts=PTS-STARTPTS[p3];"
        "[p1][p2][p3]concat=n=3:v=0:a=1,atempo=1.22,"
        "highpass=f=80,equalizer=f=240:t=q:w=1.2:g=1.8,equalizer=f=2800:t=q:w=1.2:g=2.2,"
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=60,"
        "aecho=0.88:0.86:26|52:0.13|0.07,"
        "volume=1.55,aresample=48000,aformat=channel_layouts=stereo[out]",
        "-map", "[out]", str(vo1)
    ])

    vo_specs = [
        (2, "VO_02.mp3", 1.58, "aecho=0.88:0.86:28|56:0.13|0.07"),  # Tunnel space
        (3, "VO_03.mp3", 1.68, "aecho=0.88:0.86:24|48:0.12|0.06"),  # High-speed tunnel
        (4, "VO_04.mp3", 1.55, "aecho=0.90:0.88:44:0.09"),          # Open dawn overpass
    ]
    for idx, src_name, vol, reverb in vo_specs:
        out_wav = WORK_DIR / f"vo{idx}.wav"
        run([
            "ffmpeg", "-y", "-v", "error", "-i", str(AUD_DIR / src_name),
            "-af",
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.04,"
            "highpass=f=95,equalizer=f=3400:t=q:w=1.2:g=2.8,"
            f"acompressor=threshold=-18dB:ratio=3:attack=5:release=60,{reverb},"
            f"volume={vol},aresample=48000,aformat=channel_layouts=stereo",
            str(out_wav)
        ])

    # Assemble unified VO bus with exact timestamps matching clean non-overlapping shot timing:
    # S01: 0.00-4.00 (VO1: 0.05 -> ~3.95, finishes right before S02 cut!)
    # S02: 4.00-7.75 (0.45s cold gaze breath -> VO2: 4.45 -> ~7.60)
    # S03: 7.75-11.15 (pure engine & headlight burst)
    # S04: 11.15-15.15 (VO3: 11.45 -> ~14.00, leaving 1.15s for full-throttle smirk!)
    # S05: 15.15-20.15 (full 5.0s uninterrupted high-speed cornering climax!)
    # S06: 20.15-24.45 (VO4: 20.95 -> ~23.60, leaving 0.85s crisp dawn hold)
    # Title: 24.45-27.25 (2.8s -> total 27.25s)
    vo_bus = WORK_DIR / "vo_bus.wav"
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=27.25",
        "-i", str(WORK_DIR / "vo1.wav"),
        "-i", str(WORK_DIR / "vo2.wav"),
        "-i", str(WORK_DIR / "vo3.wav"),
        "-i", str(WORK_DIR / "vo4.wav"),
        "-filter_complex",
        "[1:a]adelay=50|50[v1];"
        "[2:a]adelay=4450|4450[v2];"
        "[3:a]adelay=11450|11450[v3];"
        "[4:a]adelay=20950|20950[v4];"
        "[0:a][v1][v2][v3][v4]amix=inputs=5:duration=first:dropout_transition=0:normalize=0[out]",
        "-map", "[out]", str(vo_bus)
    ])


def prep_bgm_and_sfx():
    """Build smooth sidechain-ducked Dark Industrial BGM + cinematic transition risers/whoosh/sub-drop/boom."""
    bgm_raw = WORK_DIR / "bgm_shaped.wav"
    # BGM_V2A natural curve: 0-6s dark pulse, 6-7.2s breath drop, 7.2-21s dark brass/bass climax, 21-30s dark tail.
    # Shift by +0.55s at start? No! S03 starts at 7.75s, and BGM climax hits right at 7.2-7.5s ->
    # Pad 0.35s silence/fade-in at start so BGM 7.4s hits EXACTLY on S03 7.75s!
    # And at 20.15s (S06 dawn cut), smoothly crossfade into BGM's 22.0-29.1s quiet dark pulse tail so it stays alive around -24dB!
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(BGM_SRC),
        "-filter_complex",
        "[0:a]atrim=0:19.95,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.25[b1];"
        "[0:a]atrim=22.40:29.50,asetpts=PTS-STARTPTS,volume=0.44,afade=t=out:st=5.20:d=1.90[b2];"
        "[b1][b2]acrossfade=d=0.45:c1=tri:c2=tri,adelay=350|350,apad=whole_dur=27.25,"
        "volume=0.68,aresample=48000,aformat=channel_layouts=stereo[out]",
        "-map", "[out]", str(bgm_raw)
    ])

    # True smooth sidechain ducking driven by vo_bus (zero hard volume steps!)
    bgm_ducked = WORK_DIR / "bgm_ducked.wav"
    run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(bgm_raw),
        "-i", str(WORK_DIR / "vo_bus.wav"),
        "-filter_complex",
        "[0:a][1:a]sidechaincompress=threshold=0.018:ratio=4.5:attack=35:release=340:makeup=1.0[out]",
        "-map", "[out]", str(bgm_ducked)
    ])

    # Synthesize 4 cinematic transition SFX glue elements:
    # 1) Riser before S03 ignition (0.85s, placed at 6.95s)
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        "aevalsrc='0.32*(t/0.85)^2*sin(2*PI*(55+165*(t/0.85)^2)*t)+0.16*(t/0.85)^2*(random(0)*2-1)':s=48000:d=0.85",
        "-af", "bandpass=f=380:width_type=h:w=600,afade=t=in:st=0:d=0.25,afade=t=out:st=0.78:d=0.07,aformat=channel_layouts=stereo",
        str(WORK_DIR / "sfx_riser1.wav")
    ])
    # 2) High-speed Riser + Whoosh before S05 climax (0.95s, placed at 14.30s)
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        "aevalsrc='0.36*(t/0.95)^2.2*sin(2*PI*(65+240*(t/0.95)^2)*t)+0.24*exp(-4*abs(t-0.82))*(random(0)*2-1)':s=48000:d=0.95",
        "-af", "lowpass=f=1800,afade=t=in:st=0:d=0.25,afade=t=out:st=0.84:d=0.11,aformat=channel_layouts=stereo",
        str(WORK_DIR / "sfx_whoosh_climax.wav")
    ])
    # 3) Deep Sub-Drop air brake into S06 dawn stillness (1.6s, placed at 20.12s)
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        "aevalsrc='0.48*exp(-2.4*t)*sin(2*PI*(95*exp(-1.5*t)+34)*t)+0.10*exp(-3.5*t)*(random(0)*2-1)':s=48000:d=1.6",
        "-af", "lowpass=f=320,afade=t=in:st=0:d=0.02,afade=t=out:st=1.1:d=0.5,aformat=channel_layouts=stereo",
        str(WORK_DIR / "sfx_subdrop_dawn.wav")
    ])
    # 4) Controlled cinematic 52Hz Boom on title card (placed at 24.45s, balanced level - no ear shock!)
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        "aevalsrc='0.46*exp(-1.7*t)*sin(2*PI*(54-18*min(t,0.45))*t)+0.16*exp(-5.0*t)*sin(2*PI*108*t)':s=48000:d=2.4",
        "-af", "lowpass=f=160,afade=t=in:st=0:d=0.018,afade=t=out:st=1.6:d=0.8,aformat=channel_layouts=stereo",
        str(WORK_DIR / "sfx_boom_title.wav")
    ])


def build_title_card():
    """Render 2.8s 1080p 60fps minimalist cinema title card with centered coral line."""
    title_mp4 = WORK_DIR / "seg7_title.mp4"
    vf = (
        "drawbox=x=840:y=536:w=240:h=3:color=0xE08E79@0.95:t=fill,"
        f"drawtext=fontfile='{FONT_EN}':text='A P E X   Z E R O':"
        "fontcolor=0xF5F7FA:fontsize=74:x=(w-text_w)/2:y=430,"
        f"drawtext=fontfile='{FONT_ZH}':text='零   号   弯   道':"
        "fontcolor=0xEAECEF:fontsize=46:x=(w-text_w)/2:y=572,"
        f"drawtext=fontfile='{FONT_EN}':text='ORIGINAL  AI  CINEMA  DEMO':"
        "fontcolor=0x8D96A5@0.85:fontsize=20:x=(w-text_w)/2:y=668,"
        "fade=t=in:st=0.04:d=0.38,fade=t=out:st=2.20:d=0.60"
    )
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "color=c=0x06070A:s=1920x1080:r=60:d=2.80",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=2.80",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-shortest", str(title_mp4)
    ])


def build_video_segments():
    """Cut with dynamic pacing (4.0 / 3.75 / 3.4 / 4.0 / 5.0 / 4.3 / 2.8 = 27.25s), 1080p upscale + Morandi grade."""
    grade = (
        "scale=1920:1080:flags=lanczos,"
        "unsharp=5:5:0.42:5:5:0.0,"
        "eq=saturation=0.94:contrast=1.04:brightness=0.006,"
        "fps=60,format=yuv420p"
    )
    # S03 cuts at 3.65s right after headlight burst + engine roar peak with a 3-frame bright flash!
    specs = [
        ("seg1", "S01.mp4", 0.00, 4.00, 0.92, "fade=t=in:st=0:d=0.22"),
        ("seg2", "S02.mp4", 0.00, 3.75, 0.78, ""),
        ("seg3", "S03.mp4", 0.25, 3.65, 1.45, "fade=t=out:st=3.30:d=0.10:color=0xDCEEFF"),
        ("seg4", "S04.mp4", 0.00, 4.00, 0.95, "fade=t=in:st=0:d=0.08:color=0xDCEEFF"),
        ("seg5", "S05.mp4", 0.00, 5.00, 1.32, ""),
        ("seg6", "S06.mp4", 0.00, 4.30, 1.55, "fade=t=in:st=0:d=0.22:color=0xEADED9,fade=t=out:st=4.14:d=0.16"),
    ]
    seg_files = []
    for name, src, st, ed, sfx_vol, extra_vf in specs:
        out_mp4 = WORK_DIR / f"{name}.mp4"
        vf = grade + (f",{extra_vf}" if extra_vf else "")
        dur = round(ed - st, 3)
        af = (
            f"volume={sfx_vol},afade=t=in:st=0:d=0.03,"
            f"afade=t=out:st={max(0, dur - 0.05):.3f}:d=0.05,"
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
    seg_files.append(WORK_DIR / "seg7_title.mp4")
    return seg_files


def write_ass_subtitles():
    """Clean, zero-bleed cinema subtitles: Villain finishes strictly inside S01; distinct cool-silver vs warm-ivory tones."""
    ass_path = WORK_DIR / "subs_v2.ass"
    ass_content = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Villain,Noto Sans SC Medium,38,&H00D4C8BF,&H000000FF,&H750E1218,&H90000000,0,0,0,0,100,100,2.5,0,1,1.6,2.2,2,120,120,56,1
Style: Hero,Noto Sans SC Medium,43,&H00FAF7F5,&H000000FF,&H7510141B,&H90000000,0,0,0,0,100,100,3.5,0,1,1.8,2.4,2,120,120,56,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.05,0:00:02.05,Villain,,0,0,0,,{\fad(120,120)}三年前，零号弯道废了三台车
Dialogue: 0,0:00:02.05,0:00:03.92,Villain,,0,0,0,,{\fad(100,140)}你踩着十厘米高跟鞋，上赛道？
Dialogue: 0,0:00:04.45,0:00:07.60,Hero,,0,0,0,,{\fad(140,180)}那是因为，他们只会踩刹车。
Dialogue: 0,0:00:11.45,0:00:14.05,Hero,,0,0,0,,{\fad(140,180)}零号弯道，没有刹车线。
Dialogue: 0,0:00:20.95,0:00:23.65,Hero,,0,0,0,,{\fad(160,240)}下一局，赌你的全部。
"""
    ass_path.write_text(ass_content, encoding="utf-8")
    return ass_path


def assemble_final(seg_files, ass_path):
    """Concat video+SFX, mix smooth ducked BGM + VO bus + 4 transition SFX, master to -14 LUFS."""
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
    # Mix:
    # [0:a] native SFX (gently sidechained to VO too!)
    # [1:a] bgm_ducked (already smooth-sidechained to VO)
    # [2:a] vo_bus
    # [3:a] riser1 @ 6950ms (into S03)
    # [4:a] whoosh_climax @ 14300ms (into S05)
    # [5:a] subdrop_dawn @ 20120ms (into S06)
    # [6:a] boom_title @ 24450ms (title card hit)
    filter_complex = (
        "[0:a]aresample=48000,volume=0.92[sfx_raw];"
        "[2:a]aresample=48000,asplit=2[vo_mix][vo_sc];"
        "[sfx_raw][vo_sc]sidechaincompress=threshold=0.025:ratio=2.5:attack=30:release=250[sfx];"
        "[1:a]aresample=48000[bgm];"
        "[3:a]adelay=6950|6950,volume=0.85[r1];"
        "[4:a]adelay=14300|14300,volume=0.95[r2];"
        "[5:a]adelay=20120|20120,volume=0.95[sd];"
        "[6:a]adelay=24450|24450,volume=0.90[bm];"
        "[sfx][bgm][vo_mix][r1][r2][sd][bm]amix=inputs=7:duration=first:dropout_transition=0:normalize=0,"
        "loudnorm=I=-14:TP=-1.2:LRA=8[aout]"
    )
    run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(concat_mp4),
        "-i", str(WORK_DIR / "bgm_ducked.wav"),
        "-i", str(WORK_DIR / "vo_bus.wav"),
        "-i", str(WORK_DIR / "sfx_riser1.wav"),
        "-i", str(WORK_DIR / "sfx_whoosh_climax.wav"),
        "-i", str(WORK_DIR / "sfx_subdrop_dawn.wav"),
        "-i", str(WORK_DIR / "sfx_boom_title.wav"),
        "-vf", f"ass='{ass_esc}'",
        "-filter_complex", filter_complex,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-movflags", "+faststart",
        str(FINAL_OUT)
    ])
    print("DONE V1.1 ->", FINAL_OUT)


if __name__ == "__main__":
    prep_vo_bus()
    prep_bgm_and_sfx()
    build_title_card()
    segs = build_video_segments()
    ass = write_ass_subtitles()
    assemble_final(segs, ass)
