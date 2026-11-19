# Wattwise — Simulação de temporada (Fase 3)

Motor v1.0, configuração `55c30bee202b`. Cada cenário: 182 dias (6 meses) dia a dia. O atleta simulado falha treinos, às vezes faz mais do que o previsto, vai a voltas de grupo, dorme mal e fica doente; a VFC, a FC de repouso e o cansaço reagem à fadiga. O motor decide cada manhã.

**Critério da Fase 3 (spec 11):** nenhuma violação dos limites de segurança (spec 7.3), verificados dia a dia sobre as prescrições do motor: nada com sinal de alarme; sem intensidade com doença; dias vermelhos só com recuperação/descanso; nunca mais de 2 dias seguidos de alta intensidade (contando o que o atleta fez de facto, incluindo voltas de grupo); a Condição nunca sobe mais do que a rampa do nível em 7 dias (com a carga real); recuperação pelo menos a cada 4 semanas.

| Cenário | Violações | Verde | Amarelo | Vermelho | Bloqueado | Condição semana 4 → 26 | Treinos feitos |
|---|---|---|---|---|---|---|---|
| iniciante sem potenciometro | **0** | 88% | 12% | 0% | 0 | 8 → 19 | 76 |
| avancado com tudo | **0** | 72% | 19% | 9% | 1 | 16 → 47 | 133 |
| falha treinos | **0** | 87% | 10% | 3% | 0 | 13 → 28 | 81 |
| doente 10 dias | **0** | 68% | 22% | 10% | 0 | 17 → 53 | 136 |
| sem vfc | **0** | 92% | 7% | 1% | 0 | 5 → 10 | 45 |
| epoca com provas e etapas | **0** | 71% | 20% | 9% | 0 | 17 → 39 | 109 |
| juvenil | **0** | 90% | 5% | 5% | 0 | 10 → 30 | 92 |
| mais agressivo 5 | **0** | 73% | 20% | 7% | 0 | 18 → 54 | 133 |

## Iniciante sem potenciometro

Atleta: Ana (fictícia) (iniciante). Comportamento: cumprimento 90%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres, sem VFC.

**Sinais mais frequentes:** sono curto (19), cansaço (2)

**Decisões:** dia de descanso (104), verde: treino mantido (69), amarelo: resistência mais curta (6), amarelo: teste adiado (2), amarelo: recuperação mantida (1)

Exemplo (26/11): estado **amarelo**; sinais: sono curto = 5.9 (limiar 6.0); planeado: Finisterra · Teste de FC limiar (30 min, sem potenciómetro) 55 min → final: Tejo · Resistência Z2 30 min; dados em falta: vfc, fc_repouso

## Avancado com tudo

Atleta: Carlos (fictício) (avancado). Comportamento: cumprimento 90%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres, doença ((60, 5, 2),), alarme no dia 100.

**Sinais mais frequentes:** frescura negativa (25), sono curto (13), cansaço (5), doença (5), FC de repouso alta (5), frescura muito negativa (4)

**Decisões:** verde: treino mantido (107), dia de descanso (29), amarelo: resistência mais curta (12), vermelho: recuperação ativa (11), amarelo: versão mais fácil (10), amarelo: recuperação mantida (8), doença: recuperação, sem intensidade (3), doença com febre: descanso (1), ALARME: treino bloqueado, procurar médico (1)

Exemplo (03/12): estado **amarelo**; sinais: sono curto = 5.7 (limiar 6.0); planeado: Tejo · Resistência Z2 60 min, Tejo · Resistência Z2 60 min → final: Tejo · Resistência Z2 45 min, Tejo · Resistência Z2 45 min; dados em falta: vfc_a_calibrar, fc_repouso

## Falha treinos

Atleta: Bruno (fictício) (intermedio). Comportamento: cumprimento 60%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres.

**Sinais mais frequentes:** sono curto (12), frescura negativa (6), VFC abaixo do normal (3), frescura muito negativa (3), cansaço (2)

**Decisões:** verde: treino mantido (106), dia de descanso (54), amarelo: resistência mais curta (8), amarelo: troca por resistência (3), amarelo: recuperação mantida (3), vermelho: recuperação ativa (3), amarelo: versão mais fácil (3), guarda da rampa: treino reduzido (2), vermelho: recuperação mantida (1), prova mantida (1)

Exemplo (30/11): estado **amarelo**; sinais: sono curto = 5.2 (limiar 6.0); planeado: Penedono · Arranques 5 × 15 s em cadência baixa 45 min → final: Tejo · Resistência Z2 30 min; dados em falta: vfc_a_calibrar, fc_repouso

## Doente 10 dias

Atleta: Diana (fictícia) (competicao). Comportamento: cumprimento 90%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres, doença ((30, 10, 3),).

**Sinais mais frequentes:** frescura negativa (32), sono curto (10), doença (10), frescura muito negativa (7), FC de repouso alta (6), cansaço (3)

**Decisões:** verde: treino mantido (105), dia de descanso (29), amarelo: resistência mais curta (21), amarelo: versão mais fácil (9), vermelho: recuperação ativa (8), doença: recuperação, sem intensidade (6), doença com febre: descanso (2), amarelo: recuperação mantida (1), prova mantida (1)

Exemplo (30/11): estado **amarelo**; sinais: frescura negativa = -27.8 (limiar -25.0); planeado: Coca · Força ao limiar 5 × 6 min 75 min → final: Peñíscola · Força ao limiar 4 × 5 min 60 min; dados em falta: vfc_a_calibrar, fc_repouso

## Sem vfc

Atleta: Eduardo (fictício) (intermedio). Comportamento: cumprimento 90%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres, sem VFC.

**Sinais mais frequentes:** sono curto (13), cansaço (2), dores musculares (2)

**Decisões:** dia de descanso (130), verde: treino mantido (47), amarelo: recuperação mantida (2), amarelo: troca por resistência (2), amarelo: resistência mais curta (1)

Exemplo (19/12): estado **amarelo**; sinais: sono curto = 4.9 (limiar 6.0); planeado: Tejo · Resistência Z2 90 min → final: Tejo · Resistência Z2 60 min; dados em falta: vfc, questionario

## Epoca com provas e etapas

Atleta: Gonçalo (fictício) (avancado). Comportamento: cumprimento 90%, faz mais 25% das vezes, volta de grupo 40% dos sábados livres.

**Sinais mais frequentes:** frescura negativa (28), sono curto (13), frescura muito negativa (12), cansaço (7), dores musculares (4)

**Decisões:** verde: treino mantido (95), dia de descanso (50), amarelo: resistência mais curta (11), vermelho: recuperação ativa (10), amarelo: versão mais fácil (5), prova mantida (4), guarda da rampa: treino reduzido (3), prova mantida com alerta (3), amarelo: recuperação mantida (2), vermelho: prova desaconselhada (1)

Exemplo (30/11): estado **amarelo**; sinais: frescura negativa = -26.3 (limiar -25.0); planeado: Belmonte · Força 3 × 10 min a 60 rpm 65 min → final: Penedono · Arranques 5 × 15 s em cadência baixa 45 min; dados em falta: vfc_a_calibrar, fc_repouso

## Juvenil

Atleta: Filipe (fictício) (competicao). Comportamento: cumprimento 90%, faz mais 10% das vezes, volta de grupo 15% dos sábados livres, doença ((90, 4, 0),).

**Sinais mais frequentes:** sono curto (8), FC de repouso alta (6), doença (5), cansaço (2), dores musculares (2), VFC abaixo do normal (2)

**Decisões:** verde: treino mantido (93), dia de descanso (78), vermelho: recuperação ativa (3), doença: recuperação, sem intensidade (3), amarelo: resistência mais curta (2), amarelo: versão mais fácil (2), guarda da rampa: treino reduzido (1), amarelo: recuperação mantida (1)

Exemplo (29/11): estado **amarelo**; sinais: sono curto = 5.8 (limiar 6.0); planeado: Tejo · Resistência Z2 60 min → final: Tejo · Resistência Z2 45 min; dados em falta: vfc_a_calibrar, fc_repouso

## Mais agressivo 5

Atleta: Carlos (fictício) (avancado). Comportamento: cumprimento 90%, faz mais 20% das vezes, volta de grupo 30% dos sábados livres.

**Sinais mais frequentes:** frescura negativa (31), sono curto (11), frescura muito negativa (6), cansaço (5), dores musculares (5), FC de repouso alta (1)

**Decisões:** verde: treino mantido (115), dia de descanso (26), amarelo: resistência mais curta (17), amarelo: versão mais fácil (12), vermelho: recuperação ativa (11), amarelo: recuperação mantida (1), guarda da rampa: treino reduzido (1)

Exemplo (06/12): estado **vermelho**; sinais: cansaço = 4 (limiar 4), dores musculares = 4 (limiar 4), frescura negativa = -28.4 (limiar -25.0); planeado: Montejunto · Sweet spot 3 × 15 min 80 min, Montejunto · Sweet spot 3 × 15 min 80 min → final: Mondego · Recuperação ativa 40 min, Mondego · Recuperação ativa 40 min

---

## Perguntas para o Paulo

1. A proporção de dias amarelos/vermelhos parece-te realista? (limiares em `config/motor.yaml` → `motor`)
2. Frescura: sinal abaixo de −30% e vermelho abaixo de −45% (ou −25/−40 absolutos com Condição < 30). É o sinal que mais dispara — os limiares estão bem?
3. Amarelo numa sessão-chave: versão mais fácil do mesmo tipo (até 75% da carga). Preferes menos repetições?
4. Dia de prova vermelho: a app desaconselha a prova, mas o atleta pode fazê-la. Para provas A, outro comportamento?
5. VFC: vermelho direto ao 3.º dia seguido abaixo da faixa. Concordas?
