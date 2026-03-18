import asyncio
import hashlib
import subprocess
from pathlib import Path

import edge_tts

from app.core.config import get_settings


class TTSUnavailableError(RuntimeError):
    pass


class TTSService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.audio_dir = self.settings.storage_path / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize_chunk(self, cache_key: str, text: str) -> Path:
        file_name = f"{hashlib.sha256(cache_key.encode('utf-8')).hexdigest()}.mp3"
        output_path = self.audio_dir / file_name

        if output_path.exists():
            return output_path

        edge_error: Exception | None = None

        try:
            await self._synthesize_edge_tts(text, output_path)
            return output_path
        except Exception as exc:
            edge_error = exc

        piper_output_path = output_path.with_suffix(".wav")
        try:
            await self._synthesize_piper(text, piper_output_path)
            return piper_output_path
        except Exception as piper_error:
            edge_msg = f" Edge: {edge_error}" if edge_error else ""
            piper_msg = f" Piper: {piper_error}" if piper_error else ""
            raise TTSUnavailableError(
                "Nao foi possivel sintetizar audio: edge-tts falhou e Piper nao esta disponivel. "
                "Configure BOOKFLIX_PIPER_BIN/BOOKFLIX_PIPER_MODEL ou atualize o edge-tts."
                f"{edge_msg}{piper_msg}"
            ) from piper_error

    async def _synthesize_edge_tts(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.settings.BOOKFLIX_TTS_VOICE,
            rate=self.settings.BOOKFLIX_TTS_RATE,
        )
        await communicate.save(str(output_path))

    async def _synthesize_piper(self, text: str, output_path: Path) -> None:
        piper_bin = self.settings.BOOKFLIX_PIPER_BIN
        piper_model = self.settings.BOOKFLIX_PIPER_MODEL
        if not piper_bin or not piper_model:
            raise RuntimeError("Piper nao esta configurado")

        wav_path = output_path.with_suffix(".wav")
        cmd = [
            piper_bin,
            "--model",
            piper_model,
            "--output_file",
            str(wav_path),
        ]

        def _run() -> None:
            proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.decode("utf-8", errors="ignore"))

        await asyncio.to_thread(_run)
