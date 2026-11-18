# Wattwise

App de treino de ciclismo adaptativo. Ver `ESPECIFICACAO.md`, `ARQUITETURA.md` e `DECISOES.md`.

## Estado
- Fase 0: concluída (decisões provisórias).
- Fase 1 (em curso): leitura de FIT, qualidade de dados e métricas em `core/`.

## Correr os testes
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e "core[dev]"
pytest core
```
