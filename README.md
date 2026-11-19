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

## Validar com ficheiros reais (Intervals.icu)
```bash
python -m ww.relatorio analisar pasta_com_fits --ftp 250 --lthr 165 --fcmax 190 --fcrep 50 --sexo M --peso 70 --saida validacao.csv
# preencher as colunas iv_* com os valores do Intervals.icu e depois:
python -m ww.relatorio comparar validacao.csv
```
