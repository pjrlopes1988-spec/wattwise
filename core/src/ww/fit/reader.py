"""Leitura de ficheiros FIT com o SDK oficial da Garmin → `Serie` a 1 Hz.

Regras (D-020):
- Registos com intervalo <= `pausa_minima_s` (ex.: gravação inteligente) são
  preenchidos repetindo o último valor conhecido até ao registo seguinte.
- Intervalos maiores são pausas e não entram na série.
- O ficheiro original nunca é alterado.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from garmin_fit_sdk import Decoder, Stream

from ww.stream import FonteFC, Serie, vazia


class ErroFIT(ValueError):
    pass


def ler_ficheiro(caminho: Path | str, pausa_minima_s: float = 10) -> Serie:
    return ler_bytes(Path(caminho).read_bytes(), pausa_minima_s)


def ler_bytes(dados: bytes, pausa_minima_s: float = 10) -> Serie:
    decoder = Decoder(Stream.from_byte_array(bytearray(dados)))
    if not decoder.is_fit():
        raise ErroFIT("o ficheiro não é um FIT válido")
    mensagens, erros = decoder.read(convert_datetimes_to_dates=True)
    registos = mensagens.get("record_mesgs", [])
    avisos = [f"Erro de leitura FIT: {e}" for e in erros]
    if not registos:
        raise ErroFIT("o ficheiro não tem registos de atividade")
    return construir_serie(
        registos,
        pausa_minima_s=pausa_minima_s,
        fonte_fc=_fonte_fc(mensagens.get("device_info_mesgs", [])),
        desporto=_desporto(mensagens.get("session_mesgs", [])),
        avisos=tuple(avisos),
    )


def construir_serie(
    registos: list[dict[str, Any]],
    *,
    pausa_minima_s: float,
    fonte_fc: FonteFC = "desconhecida",
    desporto: str = "cycling",
    avisos: tuple[str, ...] = (),
) -> Serie:
    regs = sorted((r for r in registos if r.get("timestamp") is not None), key=lambda r: r["timestamp"])
    if not regs:
        raise ErroFIT("registos sem hora")
    inicio: datetime = regs[0]["timestamp"]
    tempos = [(r["timestamp"] - inicio).total_seconds() for r in regs]

    # Cada registo ocupa os segundos até ao seguinte (ou 1 s se houver pausa / for o último).
    blocos: list[tuple[dict[str, Any], int]] = []
    for i, r in enumerate(regs):
        if i + 1 < len(regs):
            dt = tempos[i + 1] - tempos[i]
            if dt <= 0:
                continue  # registo duplicado: fica o último com a mesma hora
            n = int(round(dt)) if dt <= pausa_minima_s else 1
        else:
            n = 1
        blocos.append((r, n))

    total = sum(n for _, n in blocos)
    pot, fc, cad, vel = vazia(total), vazia(total), vazia(total), vazia(total)
    pos = 0
    for r, n in blocos:
        sl = slice(pos, pos + n)
        pot[sl] = _num(r.get("power"))
        fc[sl] = _num(r.get("heart_rate"))
        cad[sl] = _num(r.get("cadence"))
        vel[sl] = _num(r.get("enhanced_speed", r.get("speed")))
        pos += n
    return Serie(inicio, pot, fc, cad, vel, fonte_fc=fonte_fc, desporto=desporto, avisos=avisos)


def _num(v: Any) -> float:
    if v is None:
        return np.nan
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def _fonte_fc(dispositivos: list[dict[str, Any]]) -> FonteFC:
    # Um sensor ANT+/BLE de FC externo indica cinta (ou braçadeira); sem isso não sabemos.
    for d in dispositivos:
        if d.get("antplus_device_type") == "heart_rate" or d.get("ble_device_type") == "heart_rate":
            return "cinta"
    return "desconhecida"


def _desporto(sessoes: list[dict[str, Any]]) -> str:
    if sessoes and sessoes[0].get("sport"):
        return str(sessoes[0]["sport"])
    return "cycling"
