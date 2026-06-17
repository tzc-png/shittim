#!/usr/bin/env python3
"""
plana_tts_server.py — 独立 torch 推理服务
完全不依赖 GPT-SoVITS 项目，只需 plana_engine/ 目录

依赖：
    pip install torch torchaudio transformers soundfile numpy

启动：
    PLANA_ENGINE_DIR=./plana_engine \
    PLANA_GPT_PATH=./models/Plana-e15.ckpt \
    PLANA_VITS_PATH=./models/Plana_e16_s208.pth \
    PLANA_REF_WAV=./references/ref.wav \
    python3 plana_tts_server.py

环境变量：
    PLANA_ENGINE_DIR — plana_engine/ 目录路径（包含模型定义和 text/）
    PLANA_GPT_PATH   — GPT 模型路径 (.ckpt)
    PLANA_VITS_PATH  — SoVITS 模型路径 (.pth)
    PLANA_REF_WAV    — 参考音频路径
    PLANA_REF_TXT    — 参考文本
    PLANA_SOCK       — Unix socket 路径（默认 /tmp/plana_tts.sock）
"""

import os, sys, json, socket, threading, traceback
import numpy as np
import torch
import torchaudio
import soundfile as sf

# ── 配置 ──────────────────────────────────────────────────────────────────────
ENGINE_DIR = os.environ.get("PLANA_ENGINE_DIR", "./plana_engine")
GPT_PATH   = os.environ.get("PLANA_GPT_PATH",  "./models/Plana-e15.ckpt")
VITS_PATH  = os.environ.get("PLANA_VITS_PATH", "./models/Plana_e16_s208.pth")
REF_WAV    = os.environ.get("PLANA_REF_WAV",   "./models/ref.wav")
REF_TXT    = os.environ.get("PLANA_REF_TXT",
             "理解しました，先生は今，特にやるべきことはないですね，暇なんですね。")
SOCK_PATH  = os.environ.get("PLANA_SOCK", "/tmp/plana_tts.sock")

if not ENGINE_DIR:
    # 默认与本脚本同级的 plana_engine/
    ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plana_engine")

# plana_engine/ 加入路径（提供 feature_extractor, module, AR, text 等包）
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[Server] 使用设备：{DEVICE}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════════
#  工具
# ═══════════════════════════════════════════════════════════════════════════════

class DictToAttrRecursive(dict):
    def __init__(self, d):
        super().__init__(d)
        for k, v in d.items():
            setattr(self, k, DictToAttrRecursive(v) if isinstance(v, dict) else v)
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self, k, v):
        v = DictToAttrRecursive(v) if isinstance(v, dict) else v
        super().__setitem__(k, v)
        super().__setattr__(k, v)


def spectrogram_torch(y, n_fft, sampling_rate, hop_size, win_size, center=False):
    hann = torch.hann_window(win_size).to(y)
    y = torch.nn.functional.pad(
        y.unsqueeze(1),
        ((n_fft - hop_size) // 2, (n_fft - hop_size) // 2),
        mode="reflect"
    ).squeeze(1)
    spec = torch.stft(y, n_fft, hop_length=hop_size, win_length=win_size,
                      window=hann, center=center, normalized=False,
                      onesided=True, return_complex=False)
    return torch.sqrt(spec.pow(2).sum(-1) + 1e-6)


# ═══════════════════════════════════════════════════════════════════════════════
#  模型加载（只做一次）
# ═══════════════════════════════════════════════════════════════════════════════

_model = {}


def _load_models():
    global _model
    if _model:
        return

    cnhubert_path = os.path.join(ENGINE_DIR, "pretrained_models", "chinese-hubert-base")

    # 1. cnhubert（使用 plana_engine/ 内的精简版）
    print("[Server] 加载 cnhubert...", file=sys.stderr)
    from feature_extractor import cnhubert as _cnhubert_mod
    _cnhubert_mod.cnhubert_base_path = cnhubert_path
    ssl_model = _cnhubert_mod.get_model().to(DEVICE).eval()
    _model["ssl"] = ssl_model

    # 2. SoVITS
    print("[Server] 加载 SoVITS...", file=sys.stderr)
    from module.models import SynthesizerTrn
    dict_s2 = torch.load(VITS_PATH, map_location="cpu", weights_only=False)
    hps = dict_s2["config"]
    hps["model"]["version"] = (
        "v1" if dict_s2["weight"]["enc_p.text_embedding.weight"].shape[0] == 322
        else "v2"
    )
    hps = DictToAttrRecursive(hps)
    hps.model.semantic_frame_rate = "25hz"
    vq_model = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model,
    ).to(DEVICE).eval()
    vq_model.load_state_dict(dict_s2["weight"], strict=False)
    _model["vits"] = vq_model
    _model["hps"]  = hps
    _model["version"] = hps.model.version

    # 3. GPT
    print("[Server] 加载 GPT...", file=sys.stderr)
    from AR.models.t2s_lightning_module import Text2SemanticLightningModule
    dict_s1 = torch.load(GPT_PATH, map_location="cpu", weights_only=False)
    cfg = dict_s1["config"]
    t2s = Text2SemanticLightningModule(cfg, "ojbk", is_train=False)
    t2s.load_state_dict(dict_s1["weight"])
    t2s = t2s.to(DEVICE).eval()
    _model["gpt"]     = t2s.model
    _model["gpt_cfg"] = cfg

    # 4. 预处理参考音频（缓存）
    print("[Server] 预处理参考音频...", file=sys.stderr)
    wav, sr = torchaudio.load(REF_WAV)
    if wav.shape[0] > 1:
        wav = wav.mean(0, keepdim=True)

    wav16k = torchaudio.functional.resample(wav, sr, 16000).to(DEVICE)
    with torch.no_grad():
        # ssl_content = ssl_model.model(wav16k)["last_hidden_state"].transpose(1, 2)
        ssl_content = ssl_model.model(wav16k.half())["last_hidden_state"].transpose(1, 2).float()
    _model["ssl_content"] = ssl_content

    wav_sr = torchaudio.functional.resample(wav, sr, hps.data.sampling_rate).to(DEVICE)
    _model["refer"] = spectrogram_torch(
        wav_sr,
        hps.data.filter_length, hps.data.sampling_rate,
        hps.data.hop_length, hps.data.win_length, center=False,
    )

    # 5. 预处理参考文本（缓存）
    print("[Server] 预处理参考文本...", file=sys.stderr)
    ref_ids, ref_bert = _text_to_phones_and_bert(REF_TXT, "ja")
    _model["ref_seq"]  = torch.LongTensor([ref_ids]).to(DEVICE)
    _model["ref_bert"] = ref_bert.to(DEVICE)

    print("[Server] 所有模型加载完成", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════════
#  文本处理
# ═══════════════════════════════════════════════════════════════════════════════

def _text_to_phones_and_bert(text: str, lang: str = "ja"):
    from text import cleaned_text_to_sequence
    version = _model.get("version", "v2")

    if lang == "ja":
        from text.japanese import g2p as ja_g2p
        phones = ja_g2p(text)
        import importlib
        sym_mod = "text.symbols2" if version == "v2" else "text.symbols"
        valid = set(importlib.import_module(sym_mod).symbols)
        phones = [p for p in phones if p in valid]
        ids  = cleaned_text_to_sequence(phones, version=version)
        bert = torch.zeros(len(ids), 1024)
        return ids, bert
    else:
        raise ValueError(f"不支持的语言: {lang}")


# ═══════════════════════════════════════════════════════════════════════════════
#  推理
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def tts(text: str, output_wav: str, lang: str = "ja"):
    hps = _model["hps"]
    gpt = _model["gpt"]
    vq  = _model["vits"]
    cfg = _model["gpt_cfg"]

    text_ids, text_bert = _text_to_phones_and_bert(text, lang)
    text_seq  = torch.LongTensor([text_ids]).to(DEVICE)
    text_bert = text_bert.to(DEVICE)

    ref_seq     = _model["ref_seq"]
    ref_bert    = _model["ref_bert"]
    ssl_content = _model["ssl_content"]
    refer       = _model["refer"]

    all_phoneme_ids = torch.cat([ref_seq, text_seq], dim=1)
    bert = torch.cat(
        [ref_bert.T.unsqueeze(0), text_bert.T.unsqueeze(0)], dim=2
    )

    prompt_semantic = vq.extract_latent(ssl_content)[0, 0].unsqueeze(0)

    top_k   = cfg["inference"].get("top_k", 5)
    max_sec = cfg["data"].get("max_sec", 30)

    pred_semantic, _ = gpt.infer_panel(
        all_phoneme_ids,
        all_phoneme_ids.shape[-1],
        prompt_semantic,
        bert,
        top_k=top_k,
        early_stop_num=50 * max_sec,
    )
    #pred_semantic = pred_semantic[:, -text_seq.shape[1]:].unsqueeze(0)
    #pred_semantic = pred_semantic.unsqueeze(0)  # 去掉截取，直接用完整结果
    pred_semantic = pred_semantic[:, prompt_semantic.shape[1]:].unsqueeze(0)

    # audio    = vq(pred_semantic, text_seq, refer)[0, 0]
    # audio = vq.infer(pred_semantic, text_seq, refer)[0, 0]

    audio = vq.decode(
    pred_semantic,
    text_seq,
    refer,
    )[0].squeeze()
    
    audio_np = audio.cpu().float().numpy()

    print(f"[Debug] audio type={type(audio)}, shape={audio.shape if hasattr(audio, 'shape') else 'N/A'}", file=sys.stderr)
    audio_np = audio.cpu().float().numpy()
    print(f"[Debug] audio_np shape={audio_np.shape}", file=sys.stderr)

    sf.write(output_wav, audio_np, hps.data.sampling_rate)
    dur = len(audio_np) / hps.data.sampling_rate
    print(f"[TTS] 完成：{output_wav}  ({dur:.2f}s)", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════════
#  Socket 服务
# ═══════════════════════════════════════════════════════════════════════════════

def handle_client(conn):
    try:
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk

        req  = json.loads(data.decode().strip())
        text = req.get("text", "")
        out  = req.get("out",  "/tmp/plana_tts_out.wav")
        lang = req.get("lang", "ja")

        if not text:
            conn.sendall(b'{"status":"error","msg":"empty text"}\n')
            return

        tts(text, out, lang)
        conn.sendall(json.dumps({"status": "ok", "out": out}).encode() + b"\n")

    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        try:
            conn.sendall(
                json.dumps({"status": "error", "msg": str(e)}).encode() + b"\n"
            )
        except Exception:
            pass
    finally:
        conn.close()


def main():
    import signal
    signal.signal(signal.SIGINT, lambda s, f: (
        os.remove(SOCK_PATH) if os.path.exists(SOCK_PATH) else None,
        sys.exit(0)
    ))

    print("[Server] 正在加载模型...", file=sys.stderr)
    _load_models()

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCK_PATH)
    os.chmod(SOCK_PATH, 0o600)
    server.listen(5)
    print(f"[Server] 监听 {SOCK_PATH}", file=sys.stderr)

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
