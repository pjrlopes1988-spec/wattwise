# Registo de Decisões — Wattwise

Cada entrada: contexto, decisão (ou pergunta), estado.
Estados: **Proposta** (aguarda o Paulo) · **Aprovada** · **Aberta** (preciso de resposta antes de implementar) · **Substituída**.

---

## Arquitetura e tecnologia

### D-001 — Tecnologias base
- **Proposta:** Python 3.12+ / FastAPI / PostgreSQL 16 no backend; React Native + Expo (TypeScript) no telemóvel; gráficos com Victory Native XL. Detalhe em `ARQUITETURA.md` §3.
- **Estado:** Proposta.

### D-002 — Cálculos e motor em bibliotecas puras
- **Proposta:** `ww_metrics`, `ww_plan` e `ww_engine` sem base de dados, rede nem LLM. O backend só orquestra. (Spec 12: "motor isolado, testável sem interface nem base de dados.")
- **Estado:** Proposta.

### D-003 — Configuração única e versionada
- **Proposta:** `config/motor.yaml`, validado no arranque. Cada decisão do motor regista o hash da versão da configuração usada. As sobreposições por atleta ficam na base de dados.
- **Estado:** Proposta.

### D-004 — Fila de tarefas sobre o PostgreSQL (Procrastinate)
- **Proposta:** evitar o Redis no MVP. Reavaliar acima de alguns milhares de atletas ativos.
- **Estado:** Proposta.

### D-005 — Alojamento na UE
- **Pergunta:** tens preferência ou orçamento? Opções: Hetzner/Scaleway/OVH (mais barato, mais trabalho de operação) ou AWS/GCP em Frankfurt/Paris (mais caro, mais serviços geridos). Recomendo um fornecedor europeu com PostgreSQL gerido.
- **Estado:** Aberta (não bloqueia a Fase 1).

### D-006 — Onde fica o código
- **Contexto:** esta sessão corre num contentor temporário, sem repositório ligado. O que não for guardado num repositório Git perde-se quando a sessão termina.
- **Pergunta:** crias um repositório GitHub privado (ex.: `wattwise`) e ligas à sessão? Até lá, descarrega os ficheiros gerados.
- **Estado:** Aberta (**bloqueia a Fase 1**).

## Métricas (secção 6)

### D-007 — Limites das zonas de potência
- **Contexto:** a spec diz Z1 <55% e Z2 56–75%, o que deixa 55–56% sem zona.
- **Proposta:** limites superiores inclusivos: Z1 ≤55%, Z2 >55–75%, Z3 >75–90%, Z4 >90–105%, Z5 >105–120%, Z6 >120–150%, Z7 >150%.
- **Estado:** Proposta.

### D-008 — Fórmula da média exponencial (Condição/Fadiga)
- **Contexto:** a spec indica `CTL_hoje = CTL_ontem + (TSS_hoje − CTL_ontem)/42`. A TrainingPeaks usa o fator `1 − e^(−1/42)` em vez de `1/42`. A diferença é de cerca de 1% e acumula-se pouco.
- **Proposta:** seguir a spec. Deixar a forma do fator configurável e confirmar na validação cruzada qual delas o Intervals.icu usa.
- **Estado:** Proposta.

### D-009 — Forma em percentagem com Condição baixa
- **Contexto:** Frescura ÷ Condição × 100 fica instável quando a Condição está perto de zero (atleta novo, regresso após paragem). Ex.: Condição 3, Frescura −6 dá −200%.
- **Proposta:** usar a mesma Condição de ontem que entra na Frescura. Abaixo de uma Condição mínima (por defeito 15, configurável), o motor usa a Frescura absoluta com limiares próprios e a app mostra "a calibrar".
- **Estado:** Aberta (preciso do teu valor mínimo).

### D-010 — eFTP a partir de um único esforço
- **Contexto:** o modelo de Morton tem 3 parâmetros (CP, W′, Pmax). Com um só esforço não é possível estimar os três: é preciso fixar dois.
- **Proposta:** com um esforço, fixar W′ e Pmax com os valores do próprio atleta (estimados da sua curva de potência), ou, sem histórico, com valores de população conservadores por sexo e nível (no ficheiro de configuração). Com 3 esforços válidos, ajuste completo. FTP = CP × fator configurável (a definir contigo; o Intervals.icu documenta o seu método e vou compará-lo na validação cruzada).
- **Estado:** Aberta (método e valores de população a validar contigo).

### D-011 — Carga por FC (HRSS)
- **Proposta:** TRIMP de Banister com reserva de FC (FC repouso, FC máx.), ponderação exponencial por sexo (homens 0,64·e^(1,92x); mulheres 0,86·e^(1,67x)), normalizado para que 1 h exatamente à FC limiar = 100. Confirmar com a documentação do Intervals.icu na implementação e registar diferenças.
- **Estado:** Proposta.

### D-012 — Exportação de treinos em .FIT
- **Contexto:** o SDK oficial da Garmin em Python só **lê** FIT. Para **escrever** ficheiros de treino há o SDK oficial noutras linguagens (JavaScript, Java, C#…) ou bibliotecas Python de terceiros.
- **Proposta:** começar por .ZWO e .ERG (formatos de texto simples). Para .FIT, usar o SDK oficial num pequeno serviço ou biblioteca testada, validando cada ficheiro gerado com o leitor oficial e num dispositivo Garmin real.
- **Estado:** Proposta (decisão final na fase de exportação).

### D-013 — Zonas de FC de Friel (ciclismo)
- **Proposta (por defeito, % da FC limiar):** Z1 <81%, Z2 81–89%, Z3 90–93%, Z4 94–99%, Z5a 100–102%, Z5b 103–106%, Z5c >106%. Configurável.
- **Estado:** Proposta (confirmar que é este o modelo que usas com os teus atletas).

### D-014 — Correspondência para as 3 zonas de Seiler
- **Contexto:** o modelo de Seiler define-se por limiares fisiológicos (LT1/LT2), que a app não mede diretamente.
- **Proposta:** Baixa = Z1–Z2 de potência (ou FC < ~limiar aeróbio); Limiar = Z3–Z4; Alta = Z5 ou mais. Configurável.
- **Estado:** Aberta (é a correspondência que preferes? Z3 entra em "baixa" ou "limiar"?).

### D-015 — Linhas de base de VFC por fonte
- **Proposta:** uma linha de base por fonte e por métrica (rMSSD ≠ SDNN, spec 5). Se o atleta mudar de dispositivo, nova calibração de 14 dias; durante esse tempo o motor decide sem VFC e diz isso na explicação.
- **Estado:** Proposta.

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
