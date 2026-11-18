# Wattwise — Proposta de Arquitetura (Fase 0)

> Estado: **proposta, aguarda aprovação do Paulo**.
> Base: `ESPECIFICACAO.md` v1 (nov. 2026). Decisões e perguntas em `DECISOES.md`.

---

## 1. Visão geral

```
┌──────────────────────────┐        ┌───────────────────────────────────────────────┐
│  App móvel (iOS/Android) │  HTTPS │  Backend (UE)                                  │
│  React Native + Expo     │◄──────►│                                                │
│  - mostra, não calcula   │  JSON  │  API (FastAPI) ──► PostgreSQL (dados + auditoria)
│  - cache offline (SQLite)│        │      │                                         │
│  - HealthKit / Health    │        │      ▼                                         │
│    Connect (Fase 5)      │        │  Fila de tarefas ──► Workers:                  │
└──────────────────────────┘        │      • importar FIT  → qualidade → métricas    │
                                    │      • recalcular carga/forma                  │
┌──────────────────────────┐        │      • motor diário (cada manhã e após ativ.)  │
│  Painel interno (web)    │◄──────►│      • explicação (LLM, só texto)              │
│  só casos sinalizados    │        │                                                │
└──────────────────────────┘        └───────────────────────────────────────────────┘
```

Princípio central: **os cálculos e as decisões vivem em bibliotecas Python puras**, sem base de dados, sem rede e sem interface. A API e os workers só carregam dados, chamam essas bibliotecas e guardam os resultados. Assim, tudo o que pode estragar um treino é testável com testes unitários e com simulações.

## 2. Módulos

O repositório é um monorepo:

```
wattwise/
├── ESPECIFICACAO.md  ARQUITETURA.md  DECISOES.md
├── config/
│   └── motor.yaml              # TODOS os parâmetros do motor e das métricas (spec 0.6)
├── packages/
│   ├── ww_fit/                 # leitura de FIT → modelo interno (séries temporais)
│   ├── ww_quality/             # picos, falhas de sinal, FC ótica, índice de qualidade (6.6)
│   ├── ww_metrics/             # zonas, NP, IF, carga, curva, eFTP, W′, W′bal, HRSS,
│   │                           # desacoplamento, CTL/ATL/TSB, VFC, Seiler… (secção 6)
│   ├── ww_plan/                # geração do plano e biblioteca de treinos (7.2)
│   ├── ww_engine/              # motor de adaptação diária + limites de segurança (7.3–7.4)
│   ├── ww_export/              # exportação .FIT / .ZWO / .ERG
│   └── ww_simulator/           # atletas fictícios e simulação de temporada (secção 10)
├── backend/                    # FastAPI, modelos SQL, migrações, workers
├── mobile/                     # app Expo (Fase 4)
├── admin/                      # painel interno (Fase 4+)
└── tests/fixtures/fit/         # ficheiros FIT reais de referência (Garmin, Wahoo, Coros, Polar)
```

Dependências permitidas (sentido único):
`ww_fit → ww_quality → ww_metrics → ww_plan → ww_engine`. O `ww_engine` **não** importa nada do backend nem do LLM.

### 2.1 Configuração (`config/motor.yaml`)
- Um único ficheiro YAML com os valores por defeito da especificação, validado no arranque com Pydantic (tipos, intervalos permitidos). Um valor inválido impede o arranque, não chega aos atletas.
- Cada versão do ficheiro tem um identificador (hash). **Cada decisão do motor regista a versão da configuração usada.** Isto serve a auditoria (7.6) e o lançamento gradual: atleta X pode correr a configuração v12 e o atleta Y a v13 (10% dos atletas).
- Sobreposições por atleta (ex.: constantes 42/7 dias) ficam na base de dados e são aplicadas por cima do ficheiro.

### 2.2 Registo de decisão (7.1)
Estrutura imutável gerada pelo motor, guardada em JSON na tabela de auditoria:
`entradas` (sinais disponíveis com origem e valor), `estado` (verde/amarelo/vermelho), `regras_disparadas` (id da regra + limiar + valor observado), `treino_original`, `treino_final`, `versao_config`, `versao_motor`.
O mesmo registo, **sem dados identificáveis**, é a única entrada do LLM.

### 2.3 Fluxo de uma atividade nova (objetivo < 60 s, spec 8.2)
1. Upload do FIT (ou chegada por integração) → guardado tal como veio (ficheiro original nunca é alterado).
2. Deduplicação (início ± 2 min, duração semelhante).
3. `ww_quality`: limpeza + índice de qualidade.
4. `ww_metrics`: métricas da atividade; recálculo incremental de carga/forma desde essa data.
5. eFTP/W′ só se a qualidade passar o limiar → se mudar, gera **proposta** ao atleta (nunca aplica em silêncio).
6. `ww_engine`: reavalia os próximos dias.
7. Explicação (LLM com validação de números, ou texto-modelo).
8. Notificação à app; a app descarrega os resultados pré-calculados.

## 3. Tecnologias propostas

| Área | Escolha | Porquê |
|---|---|---|
| Linguagem dos cálculos e do backend | **Python 3.12+** | Melhor ecossistema para FIT, numpy/scipy (ajuste de modelos de potência crítica), e testes. |
| Leitura de FIT | **SDK oficial da Garmin** (`garmin-fit-sdk`, Python) | Oficial e mantido; lê todas as marcas que cumprem o protocolo FIT. Alternativa testada: `fitdecode`. |
| Escrita de treinos .FIT | A decidir (ver D-012) | O SDK Python oficial só lê; para escrever é preciso outra biblioteca ou o SDK oficial em JS/Java/C#. |
| API | **FastAPI** + Pydantic | Tipos validados de ponta a ponta, documentação automática (OpenAPI), simples. |
| Base de dados | **PostgreSQL 16** | Pedido na spec; JSONB para os registos de auditoria; séries temporais das atividades guardadas comprimidas (Parquet em armazenamento de objetos) e não linha a linha. |
| Fila de tarefas | **Procrastinate** (fila sobre o próprio PostgreSQL) | Evita mais um serviço (Redis) no início. Troca-se por outra se o volume o exigir. |
| Alojamento | Fornecedor com centros de dados na UE (ex.: Hetzner, Scaleway, OVH, ou AWS/GCP em Frankfurt/Paris) | RGPD (spec 9). Ver D-008. |
| App móvel | **React Native + Expo** (TypeScript), com *development build* | Um só código para iOS e Android; módulos maduros para HealthKit e Health Connect; atualizações por OTA para correções rápidas. Flutter seria igualmente viável; a escolha pesa a facilidade de contratar programadores e o ecossistema. |
| Gráficos no telemóvel | **Victory Native XL** (desenho com Skia, na GPU) | Pensado para 60 fps com muitos pontos; cumpre os 300 ms para 1 ano de dados. Validar com protótipo na Fase 4. |
| Offline na app | SQLite local (`expo-sqlite`) + sincronização | Ecrã "Hoje" em < 1,5 s sem rede (spec 8.2). |
| Tradução | `i18next` com ficheiros PT-PT e ES; glossário de termos de treino validado pelo Paulo | Spec 2.2 e 8.1. |
| Explicações (LLM) | API da Anthropic (modelo Claude), chamada só a partir do backend | Recebe o registo sem dados pessoais; validação automática de números; texto-modelo de reserva. Ver D-010. |
| Monitorização de erros | Sentry (região UE) | Spec 10.5. |
| Interruptores (feature flags) | Tabela própria na base de dados com percentagem por atleta | Simples e suficiente para o MVP; reavaliar (ex.: Unleash) mais tarde. |
| Testes | `pytest`, `hypothesis` (testes por propriedades: ex. "a carga nunca é negativa"), cobertura mínima de 95% nos pacotes `ww_*` | Spec 0.3 e 10. |
| CI | GitHub Actions: testes, tipos (`mypy --strict` nos pacotes de cálculo), *lint*, simulação de temporada em cada alteração ao motor | Uma regra nova que viole um limite de segurança não entra. |

## 4. Nomes na interface vs. no código

No código usa-se a nomenclatura técnica (`ctl`, `atl`, `tsb`, `np`) para facilitar a comparação com a literatura. **Na interface nunca aparecem** essas siglas (marcas da TrainingPeaks, spec 6.3): usam-se Condição, Fadiga, Frescura, Potência ponderada, Carga, Intensidade. Um teste automático verifica que os ficheiros de tradução não contêm as siglas.

## 5. Segurança e RGPD (resumo técnico)
- Encriptação em trânsito (TLS) e em repouso (disco e cópias de segurança).
- Dados de saúde em tabelas separadas; consentimento explícito registado com data e versão do texto.
- Exportação e apagamento completos por atleta (incluindo ficheiros FIT originais e registos de auditoria — o que deve ficar dos registos após apagar é decisão jurídica, ver D-015).
- O LLM nunca recebe nome, contactos, data de nascimento, nem texto livre de lesões.

## 6. Plano da Fase 1 (após aprovação)
1. Esqueleto do monorepo, CI e `config/motor.yaml` com os valores da spec.
2. `ww_fit`: leitura de FIT → séries temporais (1 Hz, com tratamento de pausas).
3. `ww_quality`: picos, falhas de sinal, índice de qualidade.
4. `ww_metrics`, nesta ordem: zonas → NP/IF/carga → curva de potência → CTL/ATL/TSB → zonas e carga por FC (HRSS) → desacoplamento e potência/FC → W′ e W′bal → eFTP (por último, é o mais sensível).
5. Para cada métrica: testes com valores calculados à mão **antes** da implementação, depois com os ficheiros FIT reais.
6. Relatório de validação cruzada com o Intervals.icu (diferenças > 3–5% explicadas ou corrigidas).

**Preciso de ti para a Fase 1:** 10–20 ficheiros FIT reais de várias marcas (com e sem potência, com FC ótica e de cinta, rolo e estrada, pelo menos um com problemas conhecidos), e os valores que o Intervals.icu mostra para cada um.
