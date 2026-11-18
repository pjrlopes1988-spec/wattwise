"""Gera ficheiros FIT sintéticos para testar o leitor (não substituem ficheiros reais)."""
from datetime import datetime, timezone

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.profile_type import FileType, Manufacturer

INICIO = datetime(2026, 11, 1, 9, 0, 0, tzinfo=timezone.utc)


def gerar(registos: list[tuple[int, float | None, float | None, float | None]]) -> bytes:
    """registos: (segundos desde o início, potência, FC, cadência)."""
    ms0 = int(INICIO.timestamp() * 1000)
    b = FitFileBuilder(auto_define=True, min_string_size=50)
    fid = FileIdMessage()
    fid.type = FileType.ACTIVITY
    fid.manufacturer = Manufacturer.DEVELOPMENT.value
    fid.product = 0
    fid.time_created = ms0
    fid.serial_number = 1
    b.add(fid)
    for t, p, f, c in registos:
        r = RecordMessage()
        r.timestamp = ms0 + t * 1000
        if p is not None:
            r.power = p
        if f is not None:
            r.heart_rate = f
        if c is not None:
            r.cadence = c
        b.add(r)
    return b.build().to_bytes()
