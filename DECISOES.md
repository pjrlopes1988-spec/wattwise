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
