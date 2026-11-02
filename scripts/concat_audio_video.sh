#!/usr/bin/env bash
# concat_audio_video.sh — montagem final (rodar DENTRO do container).
#
# Concatena cenas com crossfade, muxa narração TTS nas posições dos segmentos,
# opcional música de fundo, normaliza H.264/AAC para a plataforma e garante faststart.
#
# uso:
#   bash /work/scripts/concat_audio_video.sh --in /work/output/<sid> --platform <plataforma> \
#        [--music /work/output/<sid>/audio/bgm.mp3] [--subtitles-burn-in /work/output/<sid>/subs.srt] \
#        [--out /work/output/<sid>/final/video-final.mp4]
#
# Entradas esperadas (geradas pelas etapas 4 e 5):
#   $IN/manifest.json        lista de cenas ordenadas (id, arquivo de vídeo, audio, duração real)
#   $IN/scenes/*.mp4         cenas renderizadas
#   $IN/audio/*.mp3          TTS por segmento
set -euo pipefail

IN=""
PLATFORM=""
OUT=""
MUSIC=""
SUBTITLES=""
CROSSFADE=0.3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in) IN="$2"; shift 2 ;;
    --platform) PLATFORM="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --music) MUSIC="$2"; shift 2 ;;
    --subtitles-burn-in) SUBTITLES="$2"; shift 2 ;;
    --crossfade) CROSSFADE="$2"; shift 2 ;;
    -h|--help)
      cat <<'Usage'
uso: concat_audio_video.sh --in <dir-sessão> --platform <plataforma> [--music MP3]
                          [--subtitles-burn-in SRT] [--out MP4] [--crossfade 0.3]
Usage
      exit 0 ;;
    *) echo "arg desconhecido: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$IN" && -d "$IN" ]] || { echo "erro: --in obrigatório (dir da sessão)" >&2; exit 1; }
[[ -n "$PLATFORM" ]] || { echo "erro: --platform obrigatório" >&2; exit 1; }
MANIFEST="$IN/manifest.json"
[[ -f "$MANIFEST" ]] || { echo "erro: manifest.json ausente em $IN" >&2; exit 1; }

OUT="${OUT:-$IN/final/video-final.mp4}"
mkdir -p "$(dirname "$OUT")" "$IN/tmp"
TMP="$IN/tmp"

# resolução/pad por plataforma
case "$PLATFORM" in
  yt-long)                       W=1920; H=1080 ;;
  yt_shorts|ig_reels|tiktok)     W=1080; H=1920 ;;
  *) echo "erro: plataforma desconhecida $PLATFORM" >&2; exit 1 ;;
esac

python3 - "$MANIFEST" "$TMP" "$PLATFORM" <<'PYEOF'
import json, os, sys
manifest = json.load(open(sys.argv[1]))
tmp, platform = sys.argv[2], sys.argv[3]
scenes = [s for s in manifest.get("scenes", []) if s.get("status") == "success" and s.get("video_path")]
if not scenes:
    print("erro: nenhuma cena com status success no manifest", file=sys.stderr); sys.exit(1)
# manifesto de montagem: ordem + durações reais (áudio) para posicionamento de narração
proj = []
t = 0.0
for s in scenes:
    audio = s.get("audio_path") or ""
    proj.append({
        "video": s["video_path"],
        "audio": audio if audio and os.path.exists(audio) else "",
        "dur": float(s.get("duration", 0)) or float(s.get("real_duration", 0)) or 5.0,
        "start": round(t, 3),
        "segment_id": s.get("id", "")
    })
    t += proj[-1]["dur"]
json.dump({"platform": platform, "total": round(t, 3), "segments": proj},
          open(os.path.join(tmp, "assemble_plan.json"), "w"), indent=2)
print(f"plano de montagem: {len(proj)} segmentos, {round(t,3)}s total")
PYEOF

# --- Part 1: normalizar cada cena para a resolução da plataforma e fps constante
python3 - "$TMP" "$OUT" <<'PYEOF'
import json, subprocess, sys, os
plan = json.load(open(os.path.join(sys.argv[1], "assemble_plan.json")))
tmp, out = sys.argv[1], sys.argv[2]
W, H = (1920, 1080) if plan["platform"] == "yt-long" else (1080, 1920)
norm_files = []
failures = []
for i, seg in enumerate(plan["segments"]):
    src, dst = seg["video"], os.path.join(tmp, f"norm-{i:03d}.mp4")
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1,format=yuv420p")
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", src, "-vf", vf,
                        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                        "-pix_fmt", "yuv420p", dst])
    if r.returncode == 0 and os.path.exists(dst):
        norm_files.append(dst)
    else:
        failures.append(seg["segment_id"])
if failures:
    print(f"erro: falha ao normalizar cenas: {failures}", file=sys.stderr); sys.exit(1)
print(f"cenas normalizadas: {len(norm_files)}")
PYEOF

# --- Part 2: concat com crossfade (xfade) + trilha de vídeo base
python3 - "$TMP" "$OUT" "$CROSSFADE" "$W" "$H" <<'PYEOF'
import json, subprocess, sys, os
tmp, out, xf, W, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
plan = json.load(open(os.path.join(tmp, "assemble_plan.json")))
segs = [os.path.join(tmp, f"norm-{i:03d}.mp4") for i in range(len(plan["segments"]))]
base = os.path.join(tmp, "video-base.mp4")
assert segs, "sem cenas"
if len(segs) == 1:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", segs[0],
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", base], check=True)
else:
    # corrente de xfade: offsets acumulando (xfade reduz a duração total pelo crossfade)
    inputs = []
    for f in segs:
        inputs += ["-i", f]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs
    chains, cur_label, total_cum = [], "0:v", 0.0
    durs = []
    for f in segs:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                  "format=duration", "-of", "csv=p=0", f],
                                 capture_output=True, text=True).stdout.strip())
        durs.append(d)
    for i in range(len(segs) - 1):
        off = total_cum + durs[i] - xf
        out_l = f"x{i}"
        chains.append(f"[{cur_label}][{i+1}:v]xfade=transition=fade:duration={xf}:offset={off:.3f}[{out_l}]")
        cur_label, total_cum = out_l, off
    fc = ";".join(chains) + f";[{cur_label}]format=yuv420p[v]"
    cmd += ["-filter_complex", fc,
            "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", base]
    print("concatenando", len(segs), "cenas com xfade", xf, "s (offset final %.3f)" % total_cum)
    subprocess.run(cmd, check=True)
print("trilha base video:", base)
PYEOF

# --- Part 3: mux narration TTS at positions + optional music + loudnorm + faststart
python3 - "$TMP" "$OUT" "$PLATFORM" "$MUSIC" "$SUBTITLES" <<'PYEOF'
import json, subprocess, sys, os
tmp, out = sys.argv[1], sys.argv[2]
platform = sys.argv[3]; music = sys.argv[4]; subs = sys.argv[5]
plan = json.load(open(os.path.join(tmp, "assemble_plan.json")))
base = os.path.join(tmp, "video-base.mp4")
total = plan["total"]
inputs, filters = [], []
# narration per segment: adelay to its position + pad to full length
vol_anchors = []
for i, seg in enumerate(plan["segments"]):
    if not seg.get("audio"):
        continue
    inputs += ["-i", seg["audio"]]
    idx = len(inputs) - 1
    delay_ms = int(seg["start"] * 1000)
    filters.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={total}[a{i}]")
    vol_anchors.append(f"[a{i}]")
if vol_anchors:
    filters.append("".join(vol_anchors) + f"amix=inputs={len(vol_anchors)}:normalize=0,apad=whole_dur={total}[narr]")
    if music and os.path.exists(music):
        inputs += ["-i", music]
        m = len(inputs) - 1
        filters.append(f"[{m}:a]volume=0.08,afade=t=out:st={max(total-3,0)}:d=3[mus]")
        filters.append("[narr][mus]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        filters.append("[narr]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    final_audio = "[aout]"
else:
    filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total}[aout]")
    final_audio = "[aout]"
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", base] + inputs + [
    "-filter_complex", ";".join(filters),
    "-map", "0:v", "-map", final_audio,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
    "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-t", str(total),
]
if subs and os.path.exists(subs):
    vf = f"subtitles={subs}:force_style=\"FontName=Noto Sans,FontSize=16,PrimaryColour=&HFFFFFF&,OutlineColour=&H99000000&,Outline=2,Shadow=0,MarginV=250\""
    cmd += ["-vf", vf]
cmd += [out]
subprocess.run(cmd, check=True)
print("final video:", out)
PYEOF

echo "montagem concluída: $OUT"
