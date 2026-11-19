# Registo de Decisões — Wattwise

Cada entrada: contexto, decisão (ou pergunta), estado.
Estados: **Proposta** · **Provisória** (em uso; o Paulo pode mudar a qualquer momento) · **Aprovada** · **Aberta** · **Substituída**.

> 18/11/2026 — o Paulo pediu para avançar com as propostas e mudar depois o que não gostar. Todas as propostas passaram a **Provisória**; nas perguntas abertas que bloqueavam código usa-se a proposta como valor por defeito.

---

## Arquitetura e tecnologia

### D-001 — Tecnologias base
- **Proposta:** Python 3.12+ / FastAPI / PostgreSQL 16 no backend; React Native + Expo (TypeScript) no telemóvel; gráficos com Victory Native XL. Detalhe em `ARQUITETURA.md` §3.
- **Estado:** Provisória.

### D-002 — Cálculos e motor em bibliotecas puras
- **Proposta:** `ww_metrics`, `ww_plan` e `ww_engine` sem base de dados, rede nem LLM. O backend só orquestra. (Spec 12: "motor isolado, testável sem interface nem base de dados.")
- **Estado:** Provisória.

### D-003 — Configuração única e versionada
- **Proposta:** `config/motor.yaml`, validado no arranque. Cada decisão do motor regista o hash da versão da configuração usada. As sobreposições por atleta ficam na base de dados.
- **Estado:** Provisória.

### D-004 — Fila de tarefas sobre o PostgreSQL (Procrastinate)
- **Proposta:** evitar o Redis no MVP. Reavaliar acima de alguns milhares de atletas ativos.
- **Estado:** Provisória.

### D-005 — Alojamento na UE
- **Pergunta:** tens preferência ou orçamento? Opções: Hetzner/Scaleway/OVH (mais barato, mais trabalho de operação) ou AWS/GCP em Frankfurt/Paris (mais caro, mais serviços geridos). Recomendo um fornecedor europeu com PostgreSQL gerido.
- **Estado:** Aberta (não bloqueia a Fase 1).

### D-006 — Onde fica o código
- **Contexto:** esta sessão corre num contentor temporário, sem repositório ligado. O que não for guardado num repositório Git perde-se quando a sessão termina.
- **Pergunta:** crias um repositório GitHub privado (ex.: `wattwise`) e ligas à sessão? Até lá, descarrega os ficheiros gerados.
- **Estado:** Aberta (**urgente**: sem repositório, o trabalho perde-se quando a sessão terminar).

## Métricas (secção 6)

### D-007 — Limites das zonas de potência
- **Contexto:** a spec diz Z1 <55% e Z2 56–75%, o que deixa 55–56% sem zona.
- **Proposta:** limites superiores inclusivos: Z1 ≤55%, Z2 >55–75%, Z3 >75–90%, Z4 >90–105%, Z5 >105–120%, Z6 >120–150%, Z7 >150%.
- **Estado:** Provisória.

### D-008 — Fórmula da média exponencial (Condição/Fadiga)
- **Contexto:** a spec indica `CTL_hoje = CTL_ontem + (TSS_hoje − CTL_ontem)/42`. A TrainingPeaks usa o fator `1 − e^(−1/42)` em vez de `1/42`. A diferença é de cerca de 1% e acumula-se pouco.
- **Proposta:** seguir a spec. Deixar a forma do fator configurável e confirmar na validação cruzada qual delas o Intervals.icu usa.
- **Estado:** Provisória.

### D-009 — Forma em percentagem com Condição baixa
- **Contexto:** Frescura ÷ Condição × 100 fica instável quando a Condição está perto de zero (atleta novo, regresso após paragem). Ex.: Condição 3, Frescura −6 dá −200%.
- **Proposta:** usar a mesma Condição de ontem que entra na Frescura. Abaixo de uma Condição mínima (por defeito 15, configurável), o motor usa a Frescura absoluta com limiares próprios e a app mostra "a calibrar".
- **Estado:** Provisória (proposta em uso; falta o valor/validação do Paulo).

### D-010 — eFTP a partir de um único esforço
- **Contexto:** o modelo de Morton tem 3 parâmetros (CP, W′, Pmax). Com um só esforço não é possível estimar os três: é preciso fixar dois.
- **Proposta:** com um esforço, fixar W′ e Pmax com os valores do próprio atleta (estimados da sua curva de potência), ou, sem histórico, com valores de população conservadores por sexo e nível (no ficheiro de configuração). Com 3 esforços válidos, ajuste completo. FTP = CP × fator configurável (a definir contigo; o Intervals.icu documenta o seu método e vou compará-lo na validação cruzada).
- **Estado:** Provisória (proposta em uso; falta o valor/validação do Paulo).

### D-011 — Carga por FC (HRSS)
- **Proposta:** TRIMP de Banister com reserva de FC (FC repouso, FC máx.), ponderação exponencial por sexo (homens 0,64·e^(1,92x); mulheres 0,86·e^(1,67x)), normalizado para que 1 h exatamente à FC limiar = 100. Confirmar com a documentação do Intervals.icu na implementação e registar diferenças.
- **Estado:** Provisória.

### D-012 — Exportação de treinos em .FIT
- **Contexto:** o SDK oficial da Garmin em Python só **lê** FIT. Para **escrever** ficheiros de treino há o SDK oficial noutras linguagens (JavaScript, Java, C#…) ou bibliotecas Python de terceiros.
- **Proposta:** começar por .ZWO e .ERG (formatos de texto simples). Para .FIT, usar o SDK oficial num pequeno serviço ou biblioteca testada, validando cada ficheiro gerado com o leitor oficial e num dispositivo Garmin real.
- **Estado:** Provisória.

### D-013 — Zonas de FC de Friel (ciclismo)
- **Proposta (por defeito, % da FC limiar):** Z1 <81%, Z2 81–89%, Z3 90–93%, Z4 94–99%, Z5a 100–102%, Z5b 103–106%, Z5c >106%. Configurável.
- **Estado:** Provisória.

### D-014 — Correspondência para as 3 zonas de Seiler
- **Contexto:** o modelo de Seiler define-se por limiares fisiológicos (LT1/LT2), que a app não mede diretamente.
- **Proposta:** Baixa = Z1–Z2 de potência (ou FC < ~limiar aeróbio); Limiar = Z3–Z4; Alta = Z5 ou mais. Configurável.
- **Estado:** Provisória; implementada em `ww.metrics.aerobio` (Baixa = Z1–Z2, Limiar = Z3–Z4, Alta = Z5+). Falta a validação do Paulo.

### D-015 — Linhas de base de VFC por fonte
- **Proposta:** uma linha de base por fonte e por métrica (rMSSD ≠ SDNN, spec 5). Se o atleta mudar de dispositivo, nova calibração de 14 dias; durante esse tempo o motor decide sem VFC e diz isso na explicação.
- **Estado:** Provisória.

## Explicações (LLM)

### D-016 — Fornecedor do LLM e transferência de dados
- **Contexto:** mesmo sem dados identificáveis, os registos de decisão contêm dados de saúde (VFC, sono, doença). Se o fornecedor processar dados fora da UE, é preciso enquadramento jurídico (acordo de tratamento de dados, cláusulas contratuais-tipo).
- **Proposta:** API da Anthropic (Claude), atrás de um interruptor. Na fase alfa, começar com **textos-modelo pré-escritos** (são obrigatórios de qualquer forma como reserva, spec 7.5) e ligar o LLM só depois de validado com jurista.
- **Estado:** Aberta (precisa de parecer jurídico).

## Fontes de dados

### D-017 — Estado das APIs de terceiros
- **Contexto:** a spec descreve mudanças de out./nov. 2026 (Garmin Starter, fim da Fitbit Web API, termos da Strava, fecho do "Intervals Pro"). Não as consigo confirmar a partir do meu conhecimento atual.
- **Decisão:** mantém-se o que a spec indica (Strava e Fitbit excluídas; Intervals.icu só como referência de métodos). Antes da Fase 5 confirmo cada fonte na documentação oficial atual e registo aqui o resultado. Na Fase 1 só há upload de FIT.
- **Estado:** Aprovada (segue a spec 0.4).

## RGPD

### D-018 — O que fica dos registos de auditoria após o atleta apagar a conta
- **Contexto:** a auditoria (7.6) serve para investigar queixas; o direito ao apagamento (spec 9) pede remoção total.
- **Proposta:** apagar tudo por defeito; manter apenas estatísticas agregadas e anónimas para afinar as regras. Validar com jurista.
- **Estado:** Aberta (jurista).

## Implementação (Fase 1)

### D-019 — Um único pacote Python com subpacotes
- **Decisão:** em vez de vários pacotes (`ww_fit`, `ww_metrics`…), um pacote `ww` em `core/` com subpacotes `ww.fit`, `ww.quality`, `ww.metrics`. Mesma separação, menos configuração. O motor e o plano entram como `ww.plan` e `ww.engine`.
- **Estado:** Provisória.

### D-020 — Representação interna das atividades
- **Decisão:** séries a 1 Hz em tempo de movimento. Intervalos sem registo ≤ 10 s (gravação inteligente) são preenchidos com o último valor; intervalos maiores são pausas e saem da série. Desconhecido = NaN; zero é um valor real.
- **Consequências:** a duração usada na carga é o tempo em movimento. A potência normalizada ignora janelas de 30 s com menos de metade das amostras válidas. A curva de potência só usa janelas sem falhas. As amostras de FC desconhecidas não somam carga. No saldo de W′, uma amostra desconhecida mantém o saldo (não se inventa recuperação).
- **Estado:** Provisória (comparar com o Intervals.icu na validação cruzada).

### D-021 — Carga por RPE na mesma escala
- **Decisão:** carga = RPE (0–10) × minutos × 100 / (RPE de limiar × 60), com RPE de limiar = 7. Assim, 1 h com RPE 7 vale 100, como 1 h ao FTP. Sempre marcada como estimada.
- **Estado:** Provisória (o Paulo confirma o RPE de limiar).

### D-022 — Falha de sinal de potência
- **Decisão:** potência 0 com cadência > 30 rpm = falha de sinal (passa a desconhecida). Potência 0 sem cadência = parou de pedalar (válido).
- **Estado:** Provisória.

### D-023 — Decaimento do eFTP com histórico
- **Decisão:** cada esforço vale por inteiro durante 28 dias; depois a sua potência desce 0,5% por semana (composto). Ex.: 10 semanas após a carência → ×0,951. O eFTP da época não decai.
- **Consequência:** sem esforços duros há ~6 semanas, o eFTP com histórico desce mais de 1% e gera uma proposta de descida ("sem esforços recentes"), que se aplica se o atleta não responder em 3 dias (spec 6.1).
- **Estado:** Provisória (o Paulo valida o ritmo de decaimento e se as descidas por decaimento devem aplicar-se sozinhas).

### D-024 — Subidas grandes de FTP sem confirmação
- **Decisão:** se o eFTP sobe mais de 3% e só há uma atividade a suportá-lo (sem treinos de limiar cumpridos), propõe-se subir **apenas até +3%** e explica-se que o resto aguarda confirmação. Com um 2.º esforço noutra atividade (também ≥ +3%) ou treinos de limiar cumpridos, propõe-se o valor completo.
- **Alternativa:** não propor nada até haver confirmação. Escolhi a subida parcial porque o atleta vê progresso sem risco grande.
- **Estado:** Provisória.

### D-025 — Pormenores do eFTP
- Esforços usados no método de 1 esforço: 5–30 min (configurável), só de atividades com qualidade suficiente.
- W′ e Pmax do próprio atleta: ajuste de Morton (3 parâmetros) aos melhores esforços dos últimos 90 dias, se houver um esforço ≤ 15 s, um de 2–6 min e um de 10–30 min, e W′ entre 5 000 e 40 000 J. Caso contrário, valores de população (W′ 15 000 J; Pmax 14 W/kg) — **a validar pelo Paulo**.
- Cada estimativa guarda os esforços que a determinaram (marcadores do gráfico 4).
- Alterações abaixo de 1% não geram proposta.
- **Estado:** Provisória.

### D-026 — Linha de base da VFC e da FC de repouso
- **Decisão:**
  - VFC transformada em ln, tanto rMSSD como SDNN (a spec só refere rMSSD; aplico o mesmo ao SDNN porque ambos têm distribuição assimétrica). Cada fonte + métrica tem linha de base própria.
  - Estado do dia: média dos últimos 7 dias (mín. 4 medições) comparada com a faixa normal = média ± **1,0** desvio-padrão dos valores diários dos últimos 60 dias.
  - "A calibrar" até a fonte em uso ter 14 dias com medição. Ao mudar de fonte, recomeça a calibração.
  - Várias medições no mesmo dia: média (em ln).
  - FC de repouso: mesma abordagem, sem ln; alerta quando a média de 7 dias está acima da faixa 3 dias seguidos.
  - Sono curto: < 6 h.
- **Estado:** Provisória (o Paulo valida a largura da faixa — 1,0 DP é uma escolha minha; há quem use 0,5 ou 0,75 — e os 3 dias de alerta da FC repouso).

### D-027 — Importação de bem-estar por CSV
- **Decisão:** até haver integrações (Fase 5), a VFC, a FC de repouso e o sono entram por CSV exportado da app do atleta. Formato base `data;fonte;rmssd;sdnn;fc_repouso;sono_h`; outros formatos com um mapa de colunas. Valores fora de limites plausíveis são rejeitados e reportados, nunca corrigidos.
- **Estado:** Provisória.

### D-028 — Atividades suspeitas
- **Decisão:** marcam-se como suspeitas (e ficam fora do eFTP/W′ até o atleta confirmar; a carga conta na mesma):
  - **transporte motorizado:** ≥ 60 s seguidos acima de 72 km/h;
  - **e-bike:** registada como tal no ficheiro (sub_sport);
  - **potência inconsistente:** potência ponderada / FC média a mais de 20% do habitual do atleta (potenciómetro ou rolo mal calibrado, outra bicicleta);
  - **potência muito acima do habitual:** melhor potência numa duração > 25% acima do melhor da época.
- Calibração por potenciómetro: escala e desvio por dispositivo, aplicados antes de qualquer cálculo.
- **Limitação:** e-bike sem indicação no ficheiro não é detetada (precisaria de altimetria; fica para depois).
- **Estado:** Provisória.

### D-029 — Deteção automática de intervalos
- **Decisão:** trabalho = potência suavizada (média centrada de 10 s) ≥ 88% do FTP, ou, sem potência, FC ≥ 92% da FC limiar. Quedas ≤ 10 s juntam-se ao mesmo intervalo; intervalos < 30 s ignorados; pontas acertadas no sinal original. HRRc = FC no fim − FC 60 s depois.
- **Limitação:** sprints curtos (< 30 s) e intervalos em Z3 (sweet spot abaixo de 88%) não são detetados com estes valores; podem precisar de uma segunda passagem com limiares próprios.
- **Estado:** Provisória.

### D-030 — Deduplicação
- **Decisão:** duplicado = início a ± 2 min e duração a ± 10%. Guardam-se os dois ficheiros; a atividade principal é a que tem potência → FC → melhor qualidade → origem (dispositivo > app > manual) → chegou primeiro.
- **Estado:** Provisória.

### D-031 — Modelo de carga por FC personalizado
- **Decisão:** regressão sem constante e com coeficientes ≥ 0 (carga por hora em cada zona de FC de Friel), ajustada às atividades do atleta com potência e FC dos últimos 180 dias. Só é usada com ≥ 20 atividades, R² ≥ 0,8 e coeficientes a subir com a zona (tolerância 5%). Caso contrário usa-se o HRSS.
- **Estado:** Provisória.

### D-032 — W′/Pmax do próprio atleta exigem 3 atividades
- **Contexto:** num teste, uma única sessão de intervalos (não máxima) bastou para a app ajustar um W′ "do atleta" de 33,7 kJ — pouco credível.
- **Decisão:** o perfil anaeróbio do atleta só é usado se os melhores esforços vierem de pelo menos 3 atividades diferentes; caso contrário, valores de população.
- **Estado:** Provisória.

### D-033 — Relatório de validação cruzada
- `python -m ww.relatorio analisar PASTA --ftp … --sexo … --peso … --saida validacao.csv` gera um CSV (';' e vírgula decimal) com os valores da Wattwise e colunas `iv_*` vazias para os valores do Intervals.icu; `python -m ww.relatorio comparar validacao.csv` lista as diferenças acima de 5%.
- **Estado:** Provisória.

### D-034 — Proteção contra descidas de FTP por sessões não máximas
- **Contexto (1.º ficheiro real, 17/11/2026):** uma sessão de intervalos no rolo, que não foi máxima, dá eFTP 279 W para um FTP de 334 W. Com as regras anteriores, a app propunha −16% e aplicava-o sozinha ao fim de 3 dias.
- **Decisão:** sem pelo menos 42 dias de dados de potência na app não se propõem descidas; com histórico, cada proposta desce no máximo 5%. As subidas mantêm as regras de D-024.
- **Estado:** Provisória.

### D-035 — Intervalos com histerese
- **Contexto (mesmo ficheiro):** um bloco de 12 min a 297–310 W com FTP 334 (limiar de 88% = 294 W) era partido em 3 pedaços por pequenas oscilações.
- **Decisão:** um intervalo começa com a potência suavizada ≥ 88% do FTP e só acaba quando desce abaixo de 80% (FC: 92% / 88% da FC limiar). Agora o bloco é detetado como um só intervalo de 11 min 53 s a 302 W.
- **Estado:** Provisória.

### D-036 — Ficheiros FIT reais fora do repositório
- **Decisão (o Paulo delegou, 19/11/2026):** os ficheiros FIT reais são dados pessoais de treino (do Paulo e, na fase alfa, dos atletas) e **não entram no repositório** (`.gitignore`). Ficam numa pasta local `core/tests/fixtures/fit/`; os testes com ficheiros reais correm quando os ficheiros existem e saltam-se quando não existem.
- No repositório ficam os valores de referência e os resultados de cada ficheiro (neste registo e nos testes).
- Se um dia se quiser que corram sempre (ex.: na integração contínua), a alternativa é guardá-los num armazenamento privado na UE, com consentimento dos atletas.
- 1.º ficheiro: Wahoo ELEMNT ROAM, rolo, 17/11/2026 (sem posição GPS nem perfil): potência ponderada 239,5 vs. 240 W (−0,2%), potência média 211,7 vs. 211 W (+0,3%), carga 64,2 vs. 63,9 (+0,5%), intensidade 0,717 vs. 0,717.
- **Estado:** Aprovada.

### D-037 — Tempo em movimento (alinhamento com o Intervals.icu)
- **Contexto:** comparação do ficheiro de 17/11/2026 com o Intervals.icu. Diferenças iniciais: potência ponderada 239,5 vs. 242, carga 62,7 vs. 60 (com o mesmo FTP), melhor 60 min sem valor vs. 223 W.
- **Decisão:**
  - **Parado** = velocidade 0 (roda livre a andar conta como movimento); sem dados de velocidade, potência 0 e cadência 0.
  - **Carga** calculada com o tempo em movimento.
  - **Potência ponderada:** média móvel de 30 s sobre a atividade inteira, contando só as janelas que terminam num segundo em movimento.
  - **Curva de potência:** segundos sem dados contam como 0 W (nunca aumentam a curva); janelas com < 90% de dados válidos são ignoradas.
- **Resultado (FTP 338, o do Intervals):** média +0,3%, potência ponderada +0,2%, intensidade +0,2%, carga +0,5%, melhores 5 s / 1 / 5 / 20 / 60 min entre 0,0% e +0,3%.
- **Nota:** o Wahoo usa o tempo total (potência ponderada 240, TSS 63,9); a referência passa a ser o Intervals.icu (spec 10.2).
- **Estado:** Provisória (confirmar com mais ficheiros, sobretudo de estrada).

### D-038 — Observações da tabela do Intervals.icu do Paulo (19/11/2026)
- O FTP definido no Intervals.icu (338 W) é diferente do do Wahoo (334 W), e o eFTP do próprio Intervals.icu é 313 W (W′ ≈ 25,3 kJ). A app tem de deixar claro qual é o FTP em vigor e de onde veio.
- O W′ do Paulo (≈ 25 kJ) está bem acima do valor de população em uso (15 kJ); rever esse valor (D-025).
- Uma atividade vinda da Strava não tem ficheiro original (como previsto).
- O desacoplamento que o Intervals.icu mostra para sessões de intervalos (25–51%) não tem significado fisiológico; na app só se calcula em esforços contínuos em Z2 (spec 6.2).
- **Estado:** Informação.

### D-039 — Potência média e 2.º ficheiro real (estrada, 14/11/2026)
- **Decisão:** potência média = soma da potência ÷ tempo total, com segundos sem dados a 0 W (como o Intervals.icu; 175,2 vs. 175 W).
- **Resultado (Wahoo ELEMNT ROAM + Quarq + cinta, 2 h 48 min, FTP ≈ 340):** média +0,1%, potência ponderada +0,2%, intensidade +0,2%, carga +0,6%, FC média +0,2%, melhores 5 s / 1 / 5 / 20 / 60 min entre 0,0% e +0,3%. Qualidade 0,99, sem suspeitas.
- **Desacoplamento: não comparável neste ficheiro.** Intervals.icu 6,3%; na Wattwise varia entre −3,7% e +6,9% consoante pormenores (aquecimento, média vs. potência ponderada), porque a volta é muito irregular (NP 224 vs. média 175). Como a spec indica, o desacoplamento só é calculado em esforços contínuos em Z2; validar com a volta estável de 10/11 (Intervals: 0,6%).
- **Por validar:** carga por FC (HRSS) — faltam a FC limiar, FC máxima e FC de repouso definidas no Intervals.icu.
- **Estado:** Provisória.

### D-040 — 3.º ficheiro real (rolo, 5 × 5 min em Z3, 09/11/2026) e intervalos a partir de 76%
- **Resultado (FTP 338):** média 0,0%, potência ponderada 0,0%, intensidade 0,0%, carga −0,4%, FC média +0,1%, melhores 5 s / 1 / 5 / 20 min entre 0,0% e +0,4%. Qualidade 0,999.
- **Desacoplamento:** Intervals.icu 10,9%; Wattwise 11,8% (média ÷ média por metade, método clássico). Variantes testadas: 10,2% (potência ponderada ÷ FC) a 11,8%. Mantém-se o método clássico; diferença < 1 ponto aceite (tolerância nos testes: ±1,5 pontos).
- **Intervalos (substitui os limiares de D-029/D-035):** com entrada a 88% nenhum dos 5 blocos a ~270 W (80% do FTP) era detetado; o Intervals.icu deteta-os. Novos limiares: **entrada 76% do FTP (início da Z3), saída 70%**. Resultado: 5 intervalos, durações a ≤ 9 s e potências a ≤ 2,6% da tabela do Intervals.icu; o bloco de 12 min de 17/11 passa a 716 s (planeado 720 s). Numa volta de estrada (14/11) são detetados 24 esforços (sobretudo subidas).
- **Pontas dos intervalos:** acertadas com o mínimo entre o segundo e a mediana dos 3 s à volta, para um pico isolado de ruído não esticar o intervalo.
- **Estado:** Provisória.

### D-041 — Carga por FC (HRSS) validada; perfil de FC impossível
- **Perfil de FC do Paulo no Intervals.icu (19/11/2026):** FC limiar 168, FC máx. 180, "RH Mínimo" 168 (impossível: igual à FC limiar). FC de repouso real indicada pelo Paulo: **48 bpm**.
- **Validação:** com FC limiar 168 e FC máx. 180 fixas, um único valor de repouso (~42 bpm) explica os dois treinos com FC: 09/11 → 49,9–50,6 vs. 50; 14/11 → 116,7–119,0 vs. 118 (≤ 1,1%). A fórmula (TRIMP de Banister normalizado, D-011) coincide com a do Intervals.icu; o Intervals estará a usar uma FC de repouso de outra origem (provavelmente bem-estar).
- Com a FC de repouso real (48): 09/11 → 48,6 (−2,8%); 14/11 → 112,7 (−4,5%). Diferença explicada pelo valor de repouso, não pelo método. **A confirmar** depois de o Paulo corrigir o "RH Mínimo" no Intervals.icu.
- **Correção na app:** um perfil com FC repouso ≥ FC limiar (ou FC limiar ≥ FC máx.) fazia a análise parar com erro. Agora não se calcula HRSS, a carga passa para o recurso seguinte (RPE) e a atividade leva o aviso `perfil_fc_invalido` para o atleta corrigir o perfil.
- **Estado:** Provisória.

## Fase 2 — perfil do atleta e geração do plano

### D-042 — Estimativas de perfil
- FTP em falta: 2,0 / 2,6 / 3,2 / 3,8 W/kg (iniciante / intermédio / avançado / competição) × 0,88 se feminino. FC máx. em falta: Tanaka (208 − 0,7 × idade). FC limiar em falta: 90% da FC máx. FC repouso em falta: 60. Sempre marcados "estimado"; nunca substituem valores do atleta.
- Teste guiado na 1.ª semana se o valor de referência for estimado: teste de 20 min (com potenciómetro) ou teste de FC limiar de 30 min (sem). Nunca é o primeiro treino do plano.
- **Estado:** Provisória (o Paulo valida os valores).

### D-043 — Carga semanal e limites de segurança do plano
- Carga-alvo das semanas de carga: a que sobe a Condição o máximo permitido (5 / 6 / 7 / 8 pontos por semana por nível). Recuperação: 60% da última semana de carga; afinação: 55%.
- A subida da Condição é verificada em **quaisquer 7 dias seguidos** (não só de segunda a domingo); se ultrapassar, encurtam-se os treinos de resistência. Um teste apanhou uma subida de 8,5 com limite 8 entre duas semanas.
- Recuperação após cada 3 semanas de carga; nunca mais de 2 dias seguidos de alta intensidade (também entre semanas e contando a prova); dias de descanso mínimos por nível (2 iniciante, 1 restantes; a prova conta como dia de treino).
- Quando a disponibilidade não chega, o plano fica abaixo do alvo (nunca acima) e regista "carga limitada pela disponibilidade".
- **Estado:** Provisória.

### D-044 — Biblioteca de treinos provisória
- `config/treinos.yaml`: 23 treinos (recuperação, resistência escalável, tempo, força em cadência baixa, sweet spot, limiar, VO2máx, anaeróbio, ativação pré-prova, testes). Carga prevista = horas × (intensidade)² × 100.
- Progressão: dificuldade sobe 1 por semana dentro da fase, a começar 2 abaixo do máximo do nível (iniciante 1, intermédio 1, avançado 2, competição 3). Afinação: o treino mais leve do tipo. Testes não dependem do nível.
- **Estado:** Provisória — **o Paulo valida/substitui** (spec 13).

### D-045 — Idade mínima 10 anos
- **Decisão do Paulo (19/11/2026):** idade mínima 10 anos (a spec tinha 18).
- Salvaguardas: abaixo dos 14 anos é obrigatório o consentimento de um responsável legal (RGPD: PT 13, ES 14 — usa-se 14); menores de 18 usam sempre as regras de treino de iniciante.
- **A validar com jurista:** consentimento para dados de saúde de menores. **A validar pelo Paulo:** regras próprias para jovens.
- **Estado:** Aprovada (idade); salvaguardas provisórias.

### D-046 — Alvos sem potenciómetro
- Zona de potência do passo → zona de FC de Friel (Z1 65–80%, Z2 81–89%, Z3 90–93%, Z4 94–100%, Z5 100–106% da FC limiar). Esforços curtos acima do limiar (< 3 min, Z5+) e Z6/Z7: esforço percebido (a FC não acompanha).
- **Estado:** Provisória.

### D-047 — Cenários de teste do plano
- 6 atletas fictícios em `core/tests/cenarios.py` (iniciante sem potenciómetro, intermédio com prova a 16 semanas, avançado com tudo, competição XCO com prova a 8 semanas, pouca disponibilidade, juvenil de 14 anos). Regras de segurança verificadas por testes em todos.
- Relatório para validação: `docs/cenarios_fase2.md` (`python -m ww.relatorio_plano`).
- **Estado:** Aguarda validação do Paulo (critério da Fase 2).

### D-048 — Biblioteca de treinos do Paulo (importada de ZWO, 19/11/2026)
- 21 ficheiros ZWO exportados do Intervals.icu (autor no ficheiro: "Paulo reis"): **10 de bicicleta** importados para `config/treinos_paulo.yaml` (6 de força em cadência baixa, 4 Express ≤ 30 min); **11 de força e mobilidade fora da bicicleta** guardados em `config/complementares_paulo.yaml` (ainda não usados: o MVP só planeia ciclismo).
- Conversor `python -m ww.zwo` (Warmup, Cooldown, Ramp, SteadyState, IntervalsT, FreeRide, MaxEffort, cadência). Carga das rampas exata: média de IF² = (a² + ab + b²) / 3. XML com DOCTYPE/ENTITY recusado.
- **Tipo e dificuldade são propostas automáticas** (tipo pela zona dominante do trabalho; "força" se ≥ 50% do trabalho em cadência ≤ 70 rpm; dificuldade pelos minutos de trabalho). **O Paulo confirma/corrige** em `config/treinos_paulo.yaml`.
- Os treinos do Paulo têm prioridade sobre os provisórios, à mesma dificuldade.
- Só entram treinos criados pelo Paulo (nada de planos comprados ou de outras plataformas).
- **Estado:** Provisória.

### D-049 — Alta intensidade pelo conteúdo do treino
- Conta como alta intensidade (regra dos 2 dias seguidos): tipos limiar, VO2máx, anaeróbio, teste e prova, **e qualquer treino com ≥ 5 min a ≥ 95% do FTP ou ≥ 1 min a ≥ 120%**. Ex.: "Torque ao Limiar 10×1" e "Arranques de Força" são de força mas contam como alta intensidade.
- **Estado:** Provisória.

### D-050 — Nomes de marca dos treinos (pedido do Paulo, 19/11/2026)
- Todos os treinos têm um nome ibérico (PT/ES) cuja família indica o tipo: **rios** (resistência/recuperação), **serras** (tempo/sweet spot), **subidas míticas** (limiar), **ventos** (VO2máx/anaeróbio), **castelos** (força), **faróis** (testes). Ex.: "Angliru · Limiar 2 × 20 min".
- Ficheiro `config/nomes_treinos.yaml` (editável); o nome técnico fica como subtítulo. Um teste garante que todos os treinos têm nome e que não há nomes repetidos.
- **Estado:** Provisória (o Paulo pode mudar qualquer nome). Nomes de lugares geográficos; confirmar com jurista ao registar a marca.

### D-051 — Ajustes do plano após leitura dos cenários
- Treinos curtos (ex.: Express) só quando o dia é curto: o treino escolhido tem de ocupar pelo menos ¾ do tempo disponível (até 45 min).
- Nas semanas de carga, a resistência concentra-se em menos dias, com pelo menos 60 min cada (em vez de muitas recuperações de 45 min).
- O controlo da rampa passa a encurtar (ou retirar) os treinos dos 7 dias onde está o excesso, em vez do treino mais longo da semana. Antes, um caso encolhia uma semana inteira para 3,6 h sem resolver o excesso.
- **Estado:** Provisória.

### D-052 — Treinos de outras plataformas não entram na biblioteca
- **Contexto (19/11/2026):** recebido um zip com 1 548 ficheiros ERG do catálogo do TrainerRoad (nomes de montanhas com nível de progressão, descrições traduzidas), exportados da conta do Paulo.
- **Decisão:** não importados e cópia local apagada. Conteúdo de concorrentes (TrainerRoad, Zwift, planos comprados, etc.) não entra na biblioteca da Wattwise, nem renomeado nem alterado. Estruturas genéricas de intervalos (ex.: 5 × 4 min a 110%) podem ser usadas quando descritas pelo Paulo e criadas de raiz.
- **Estado:** Aprovada (regra de propriedade intelectual; confirmar com jurista).

### D-053 — Biblioteca original da Wattwise (substitui a provisória de D-044)
- 50 treinos escritos de raiz a partir de estruturas genéricas de treino (conhecimento comum), gerados por `core/tools/gerar_biblioteca.py` para `config/treinos.yaml`: recuperação 2, resistência 5 (incl. Z2 longos com tempo/sweet spot), tempo 7, sweet spot 8, limiar 9 (incl. sobe e desce), VO2máx 10 (incl. pirâmide, 30/30, 40/20, ativação), anaeróbio 4, força 3, testes 2. Progressão de dificuldade 1–5 dentro de cada tipo. Descrições em PT-PT escritas para a app.
- Com os 10 do Paulo: 60 treinos, todos com nome de marca (D-050).
- Página de revisão: `docs/biblioteca.md` (`python -m ww.relatorio_biblioteca`).
- Os Z2 longos (Douro, Guadalquivir) ainda não são escolhidos pelo plano (o dia longo usa o Tejo escalável); fica para quando o Paulo validar a biblioteca.
- **Estado:** Provisória — o Paulo revê e acrescenta as pastas dele.

### D-054 — Biblioteca original alargada (81 originais + 10 do Paulo = 91)
- O Paulo pediu treinos "semelhantes" ao catálogo do TrainerRoad. Não se usou esse catálogo como modelo (seria cópia indireta; D-052) — os ficheiros já tinham sido apagados. Em vez disso, a biblioteca original foi alargada a partir de formatos clássicos de treino (15/15, 30/30, 40/20, 20/10, pirâmides, sobe e desce, progressivos, sprints, força em cadência baixa, Z2 longos com variações).
- Por tipo: recuperação 4, resistência 10, tempo 11, sweet spot 14, limiar 14, VO2máx 15, anaeróbio 9, força 12, testes 2. Níveis 1–5 cobertos em quase todos os tipos.
- **Estado:** Provisória — o Paulo revê em `docs/biblioteca.md`.

### D-055 — Regra única de dificuldade (todos os treinos, originais e importados)
- Minutos de trabalho a partir do início da zona do tipo (tempo 76%, sweet spot 88%, limiar 93%, VO2máx 105%, anaeróbio 121%) × fator de densidade = √(recuperação normal do tipo ÷ recuperação típica entre esforços), entre 1 e 1,5 (sem recuperação: 1,5). Recuperação "típica" = mediana dos descansos entre esforços ÷ mediana dos esforços (as pausas entre séries não diluem recuperações curtas como 40/20).
- Escalas (minutos efetivos que separam os níveis 1|2|3|4|5): tempo e sweet spot 20/30/40/55; limiar 15/24/32/40; VO2máx 10/15/20/24; anaeróbio 2/4/6/8. Força: +1 nível (cadência baixa) — a força começa no nível 2. Resistência: pela duração (1 h 15, 2 h 15, 3 h 30, 4 h 30) e +1 se tiver blocos de tempo/sweet spot.
- O conversor ZWO usa a mesma regra; os 10 treinos do Paulo foram reclassificados.
- **Estado:** Provisória (o Paulo valida as escalas).

### D-056 — Biblioteca completa e inspeção automática
- 118 treinos originais + 10 do Paulo = **128**. Tempo, sweet spot, limiar, VO2máx e anaeróbio: ≥ 2 treinos em cada nível 1–5 e uma versão até 60 min nos níveis 1–4 (dias de semana). Força ≥ 2 nos níveis 2–5; resistência ≥ 2 nos níveis 1–5.
- Descrições: o quê + sensação esperada (esforço percebido) + para quê.
- Teste de inspeção (`core/tests/test_biblioteca.py`) sobre todos os treinos: duração e carga/hora plausíveis, aquecimento ≥ 4 min e arrefecimento, trabalho na zona do tipo, recuperação entre esforços intensos, dificuldade pela regra única, descrição, nome único, nenhuma referência a outras plataformas, cobertura por nível.
- Correções apanhadas pela inspeção: "sobe e desce" com a parte de baixo em sweet spot (corrigido para 95–97%); versão curta de tempo com 61 min.
- **Estado:** Provisória — o Paulo revê `docs/biblioteca.md`.

### D-057 — Exportação ZWO, ERG e MRC
- `ww.exportar`: ZWO (% do FTP), ERG (watts, com o FTP do atleta) e MRC (% do FTP). Nos ERG/MRC, alvos em intervalo usam o meio do intervalo. Teste de ida e volta para todos os treinos (ZWO exportado e lido de volta sem diferenças; ERG com potência média e duração certas).
- Exportação para .FIT de treino e envio automático para o dispositivo: fases posteriores (spec 3).
- **Estado:** Provisória.

### D-058 — Bibliotecas indoor e outdoor separadas; o atleta escolhe (pedido do Paulo, 19/11/2026)
- **Indoor** (`config/treinos_indoor.yaml`): alvos **fixos** (no rolo em modo ERG não há descidas, vento nem trânsito); por defeito o meio do intervalo arredondado, ou o `alvo` indicado no passo. Só treinos até 150 min (`indoor.duracao_max_min`). Inclui os 10 treinos ZWO do Paulo (feitos para o rolo).
- **Outdoor** (`config/treinos_outdoor.yaml`): alvos em intervalo; inclui os Z2 longos (até 5 h).
- Mesmo treino nas duas bibliotecas = mesmo nome de marca (ex.: Angliru indoor a 98% / outdoor a 95–102%).
- **O atleta escolhe:** no perfil indica onde treina em cada dia (`ambiente`); sem indicação, com rolo inteligente = indoor de segunda a sexta e outdoor ao fim de semana (**regra por defeito a validar pelo Paulo**); sem rolo = outdoor. Cada treino do plano pode ser trocado (`trocar_ambiente`): usa a versão do outro ambiente ou, se não existir, a mais parecida (tipo, dificuldade, duração); indoor nunca passa de 150 min. A prova é sempre outdoor.
- Rolo inteligente sem potenciómetro: indoor tem alvos em watts (o rolo mede a potência); outdoor continua em FC/esforço percebido.
- Exportação: cada treino sai tal como está na sua biblioteca (indoor com alvos fixos; outdoor com intervalos).
- **Incidente corrigido:** um script de edição falhou a meio e esvaziou `test_exportar.py`; durante alguns minutos os testes de exportação "passavam" sem correr. Recuperado do Git; as edições passaram a escrever o ficheiro só depois de todas as substituições terem sucesso.
- **Estado:** Provisória.

### D-059 — Dois treinos lado a lado no calendário; "Onde vais treinar?" no perfil (Paulo, 19/11/2026)
- **Substitui** a escolha de ambiente por dia da semana de D-058 (e a regra "indoor seg–sex com rolo").
- Pergunta na configuração inicial: **"Onde vais treinar?"** — *Só outdoor* / *Só indoor* / *Indoor e outdoor*. Sugestão pelo equipamento: com rolo inteligente "Indoor e outdoor"; sem rolo "Só outdoor".
- **Indoor e outdoor:** cada dia tem as duas versões lado a lado (a mesma sessão da biblioteca outdoor e da indoor; se não existir, a mais parecida; indoor no máximo 150 min). O atleta toca numa e essa fica escolhida (`escolher`). **Só indoor / só outdoor:** uma versão. A prova é sempre só outdoor.
- **Segurança:** antes da escolha, a carga do dia é a da versão mais pesada e a alta intensidade conta se qualquer das versões o for (opção mais conservadora, spec 7.1); os limites (rampa, dias seguidos) ficam garantidos qualquer que seja a escolha.
- Interface (Fase 4): no "Hoje", as duas versões lado a lado com 🌳/🏠; a escolhida fica marcada.
- Nota para a interface: no sweet spot (88–93%) a etiqueta de zona pode diferir entre versões (Z4 no intervalo, Z3 no alvo fixo de 90%), porque o sweet spot está na fronteira das zonas.
- **Estado:** Aprovada (proposta do Paulo).

### D-060 — Calendário de provas com prioridade A–D (pedido do Paulo, 19/11/2026)
- O atleta regista as suas provas com prioridade **A** (objetivo da época) a **D** (prova-treino) e duração estimada. Um objetivo "prova" antigo, sem calendário, passa a ser uma prova A.
- **A:** ciclo completo para cada A (base → construção → específico → afinação de 1–2 semanas, com ativação 1–2 dias antes); 1 semana de recuperação depois. Com várias A, um ciclo para cada uma; depois da última A, ciclos do objetivo geral.
- **B:** mini-afinação: carga da semana × 0,8; 3 dias antes sem intensidade e com treinos ≤ 60 min; ativação (Brisa) 1–2 dias antes; dia seguinte só recuperação (≤ 45 min); sem dia longo nessa semana. Conta como sessão-chave.
- **C:** 1 dia antes sem intensidade (≤ 60 min); conta como sessão-chave; sem afinação.
- **D:** substitui um treino; conta como sessão-chave e para a carga; nada mais muda.
- Sem provas A: o plano segue o objetivo geral (sem afinação) e encaixa as B/C/D; o horizonte cobre a última prova.
- Carga estimada da prova = horas × IF² × 100, com IF pela duração (≤ 1 h 0,95; ≤ 2 h 0,88; ≤ 3 h 0,82; ≤ 5 h 0,76; mais 0,70). Sem duração: 2 h.
- Provas contam como alta intensidade e entram na regra dos 2 dias seguidos. Validação: prioridade A–D, data futura, uma prova por dia, duração 15 min–24 h.
- **Segurança:** se a rampa da Condição só puder ser cumprida mexendo numa sessão-chave (ex.: excesso numa janela de 7 dias que começa na semana anterior), a sessão-chave passa a uma versão mais leve do mesmo tipo (ou sai). Apanhado pelo novo cenário de época com provas A–D.
- Todos os valores em `config/motor.yaml` → `provas`.
- **Estado:** Provisória (o Paulo valida as regras de cada prioridade).

### D-061 — Ciclos 3+1 ou 2+1, à escolha do atleta (pedido do Paulo, 19/11/2026)
- Pergunta no perfil: "Como queres organizar os ciclos?" — **3 semanas de carga + 1 de recuperação** ou **2 + 1**. **O atleta escolhe sempre**; a opção adequada aparece já selecionada como sugestão: 2+1 a partir dos 50 anos (recuperação mais lenta), 3+1 abaixo (`perfil.idade_ciclo_2_1`, a validar). Sem escolha, usa-se a sugestão. (Atualizado a pedido do Paulo: não há opção "automático".)
- 4+1 não é oferecido: a spec 7.3 obriga a recuperação pelo menos a cada 4 semanas.
- Aplica-se a todas as fases e a todos os ciclos entre provas A. Na Fase 3, o motor poderá antecipar uma recuperação por sinais de cansaço/VFC, qualquer que seja o ciclo.
- **Estado:** Aprovada (proposta do Paulo); idade do automático provisória.

### D-062 — Provas por etapas (pedido do Paulo, 19/11/2026)
- Uma prova pode ter **várias etapas**, cada uma com data, duração e descrição (ex.: "CR 15 km", "montanha"); as datas não têm de ser seguidas (dias de descanso). Prioridade A–D para a prova toda. Validação: ≥ 2 etapas, por ordem, em dias diferentes, no máximo **7 dias** entre a 1.ª e a última (`provas.etapas_max_dias`; por norma as provas por etapas têm até uma semana, com etapas seguidas — Paulo, 19/11/2026), nenhuma no mesmo dia de outra prova.
- **Antes:** afinação (A), dias sem intensidade (B/C) e ativação contam a partir da **1.ª etapa**.
- **Durante:** cada etapa é um dia de prova com carga pela sua duração; dias de descanso entre etapas só com recuperação curta (≤ 45 min) ou descanso; sem sessões-chave. Uma prova A que continua na semana seguinte deixa essa semana leve.
- **Depois:** dias fáceis e (A) semana de recuperação contam a partir da **última etapa**.
- **Exceções assumidas** (a prova é a prova): sequências feitas só de dias de prova (etapas seguidas) não contam para o limite de 2 dias seguidos de alta intensidade — a regra continua a valer para tudo o resto (ex.: a ativação vai para 2 dias antes se a véspera a colasse às etapas); a rampa da Condição pode ser ultrapassada numa janela com etapas, depois de encurtar/aliviar tudo o resto, e o plano assinala "rampa acima do limite por causa da prova". Os testes de segurança verificam que só há excesso nessas condições.
- **Estado:** Provisória (o Paulo valida, sobretudo os dias de descanso entre etapas e a recuperação depois).

### D-063 — Prontidão depois de uma prova A (Paulo, 19/11/2026)
- Depois de uma prova A (incluindo por etapas) mantém-se **1 semana de recuperação**.
- A 1.ª semana a seguir fica marcada no plano (`Semana.verificar_prontidao`). O **motor diário (Fase 3)** avalia o atleta antes de retomar a carga (VFC, FC de repouso, questionário, sensações); se não estiver em condições, prolonga a recuperação (até `provas.prolongar_recuperacao_max_semanas`, por defeito 1 semana) e replaneia.
- **Estado:** Aprovada (regra do Paulo); implementação da avaliação na Fase 3.

### D-064 — Fase 2 aprovada (Paulo, 19/11/2026)
- Planos dos cenários e biblioteca aprovados "para já". As decisões provisórias da Fase 2 (D-042 a D-063) mantêm-se e podem ser afinadas.
- **Pendente para mais tarde:** biblioteca maior (mais treinos por tipo e nível), com treinos do Paulo quando os tiver.
- Próximo: Fase 3 — motor de adaptação diária e limites de segurança (critério: simulação de temporada sem violações).

## Fase 3 — motor de adaptação diária

### D-065 — Prontidão e decisão diária (spec 7.3, 7.4)
- **Sinais** (cada um conta 1; "fortes" = vermelho direto): VFC (média 7 d) abaixo da faixa (forte ao 3.º dia seguido); FC de repouso acima da faixa (forte com alerta sustentado); sono < 6 h; cansaço/dores/stress ≥ 4 (1–5); humor ≤ 2; frescura < −30% (forte < −45%); doença (forte, mantém-se até o atleta indicar melhoria); alarme (dor no peito, desmaio, palpitações, falta de ar anormal → **bloqueado**, procurar médico).
- **Estado:** 0 sinais verde; 1 amarelo; ≥ 2 ou um forte vermelho. Dados em falta (sem VFC, a calibrar, sem questionário…) ficam no registo; decide-se com o que há.
- **Ações:** verde mantém. Amarelo: sessão-chave → versão mais fácil do mesmo tipo (≤ 75% da carga) ou resistência; teste → adiado (resistência); resistência → 75% da duração. Vermelho → recuperação ativa 40 min. Doença com febre → descanso; sem febre → recuperação, nunca intensidade. Aplica-se às duas versões (indoor/outdoor).
- **Registo de decisão** (spec 7.1) com entradas (sinais com valor e limiar), regras, treino original e final, versões; sem dados pessoais (vai para a auditoria e para o LLM).
- **Estado:** Provisória (todos os limiares em `config/motor.yaml` → `motor`).

### D-066 — Frescura com Condição baixa
- **Problema encontrado na simulação:** no início do plano a frescura em % é instável (Condição 16, Fadiga 32 → −118%); o motor punha dias vermelhos em série e o atleta não construía condição (Condição 22 às 9 semanas).
- **Decisão:** o motor só usa a frescura em % com Condição ≥ 30; abaixo usa a absoluta (sinal < −25, vermelho < −40). Resultado: 65% → 72% de dias verdes no avançado, Condição 46 às 26 semanas.
- **Estado:** Provisória.

### D-067 — Dia de prova com prontidão vermelha ou doença
- A app **desaconselha** a prova (regra registada) mas a decisão é do atleta ("vou fazer na mesma"); a carga feita entra nas contas. Amarelo: prova mantida com alerta.
- **A validar pelo Paulo:** comportamento para provas A.

### D-068 — Semana, guarda da rampa e simulação
- **Reorganização** (spec 7.4): treino-chave falhado não se acumula — o mais importante passa para um dia de resistência ainda por fazer, se não criar mais de 2 dias seguidos de intensidade; fica marcado "falhado" no histórico. Intensidade a mais (volta de grupo, treino acima do previsto) → a sessão intensa seguinte troca com um dia de resistência ou passa a resistência. Carga real dos últimos 7 dias > 115% do planeado → encurta-se a resistência que vem.
- **Guarda da rampa:** antes de prescrever, o motor calcula com a carga REAL quanto a Condição subiria em 7 dias; se passar do limite do nível, o treino passa a recuperação mais curta ou descanso (a prova não é alterada).
- **Depois da recuperação de uma prova A** (D-063): na semana marcada, sessões intensas só com prontidão verde; senão, recuperação.
- **Simulação de temporada** (`ww.simulacao`, `core/tests/test_simulacao.py`): 7 cenários × 182 dias, comportamento realista; verificação dia a dia de todos os limites. **0 violações** em todos. Relatório: `docs/simulacao_fase3.md`.
- **Limitação conhecida:** teste de FTP adiado por amarelo ainda não é remarcado automaticamente.
- **Estado:** Provisória — a Fase 3 aguarda validação do Paulo.
