# Especificação do Produto — Wattwise
## App de Treino de Ciclismo Adaptativo

> Nome provisório até verificação de marca (EUIPO/INPI). Nome nas lojas: "Wattwise: Cycling Coach" (a confirmar). Existem apps "WattWise" na área da energia doméstica; não há conflito conhecido no desporto.

> Documento de referência para o Claude Code. Lê este ficheiro inteiro antes de escrever código.
> Autor do produto: Paulo Lopes (treinador de ciclismo, licenciado em Desporto).
> Estado: versão 1 da especificação, novembro de 2026.

---

## 0. Instruções para o Claude Code (ler primeiro)

1. **Qualidade acima de velocidade.** O primeiro contacto dos atletas com a app tem de ser fiável. Um treino mal calculado destrói a confiança. Prefere fazer menos, mas bem feito e testado.
2. **Trabalha por fases** (secção 11). Não avances para a fase seguinte sem os critérios de aceitação da fase atual cumpridos e sem confirmação do Paulo.
3. **Testes primeiro em tudo o que é cálculo.** Cada métrica (secção 6) tem de ter testes unitários com valores de referência calculados à mão ou com ficheiros FIT de exemplo.
4. **Não inventes APIs nem endpoints.** Antes de integrar qualquer fonte de dados (secção 5), confirma na documentação oficial atual o que é permitido, o que exige aprovação e o que custa. Se não tiveres acesso à documentação, para e pergunta.
5. **O motor de treino é determinístico.** A IA generativa (LLM) nunca calcula cargas, zonas ou decide o treino. Só explica, em linguagem natural, decisões que o motor já tomou (secção 7.5).
6. **Todos os parâmetros do motor são configuráveis** num único ficheiro de configuração, com os valores por defeito indicados aqui. O Paulo vai validá-los e ajustá-los como treinador.
7. **Pergunta antes de decidir** sempre que esta especificação for omissa ou ambígua. Regista as decisões tomadas num ficheiro `DECISOES.md`.

---

## 1. Visão

Uma app que funciona como **treinador pessoal automático** para ciclistas de qualquer nível. Lê o perfil do atleta e os dados dos seus dispositivos (frequência cardíaca, potência, variabilidade da frequência cardíaca, sono), cria um plano rumo a um objetivo e **ajusta os treinos todos os dias** conforme o estado real do atleta. Explica sempre porquê.

**Público:** ciclistas de estrada, gravel e BTT, amadores e competidores, inicialmente em Portugal e Espanha. Modelo de venda: subscrição para qualquer atleta (B2C).

## 2. Diferenciação face à concorrência

Concorrentes diretos: TrainerRoad (Adaptive Training), JOIN, Humango, Athletica, Xert, Zwift Coach, e dezenas de apps novas de "treinador IA". A app distingue-se por:

1. **Explicação transparente:** cada ajuste mostra a razão em linguagem simples ("Hoje a tua VFC está abaixo do teu normal e dormiste mal; trocámos os intervalos por um rolo Z2 de 60 min").
2. **Português e espanhol de raiz**, com terminologia correta de treino em cada língua.
3. **Regras de treino definidas por um treinador** (o Paulo), não uma "caixa negra".
4. **Funciona com ou sem potenciómetro** (FC como alternativa completa) e com ou sem medição de VFC.
5. **Preço ibérico** (a definir; referência de mercado: JOIN 16,99 €/mês ou 119,99 €/ano).

## 3. Âmbito da primeira versão (MVP)

### Dentro do MVP
- Registo e perfil do atleta (secção 4).
- Importação de atividades por ficheiro FIT (upload manual) **e** por pelo menos uma integração automática (secção 5).
- Cálculo de métricas (secção 6).
- Plano de treino gerado a partir do objetivo e da disponibilidade semanal.
- Ajuste diário do treino (motor de adaptação, secção 7).
- Questionário curto pós-treino (esforço percebido, sensações, dor).
- Questionário matinal opcional (sono, cansaço, dores musculares, stress, doença).
- Explicação de cada ajuste.
- Exportação do treino estruturado para o dispositivo do atleta (ficheiro .FIT/.ZWO/.ERG para download no MVP; envio automático numa fase posterior).
- Painel de forma: CTL/ATL/TSB, cumprimento do plano, evolução do FTP.
- Interface em português (PT-PT). Espanhol na fase de lançamento público.

### Fora do MVP (fases futuras)
- Rede social, segmentos, rankings.
- Mundos virtuais e controlo do rolo em tempo real.
- Planos para corrida, natação ou triatlo.
- Área para treinadores gerirem atletas.
- Chat livre com IA (só explicações no MVP).

## 4. Perfil do atleta

Dados recolhidos no registo (os marcados com * são obrigatórios):

- Nome*, data de nascimento*, sexo*, peso*, altura.
- Nível de experiência* (iniciante / intermédio / avançado / competição) e anos de treino estruturado.
- Disciplina principal* (estrada, gravel, BTT XCO, BTT maratona, contrarrelógio).
- Objetivo* (prova com data, ou objetivo geral: melhorar FTP, perder peso, resistência).
- Disponibilidade semanal*: dias e horas por dia, incluindo dia longo.
- Equipamento: potenciómetro (sim/não), rolo inteligente (sim/não), cinta de FC, relógio/ciclocomputador (marca/modelo).
- Valores fisiológicos conhecidos (opcionais; se em falta, estimar e marcar como "estimado"):
  - FTP (W), FC limiar (LTHR), FC máxima, FC repouso.
- Restrições: lesões ou condições que o atleta queira indicar (texto livre, tratado como dado de saúde — ver secção 9).

**Regras:**
- Idade mínima: 18 anos no MVP (evita requisitos adicionais para menores).
- Se o atleta não souber o FTP ou o LTHR, a app propõe um teste guiado na primeira semana (ex.: teste de 20 min ou rampa) e usa valores conservadores até lá.

## 5. Fontes de dados

**Atenção:** o acesso a dados de terceiros mudou muito em 2026. Confirmar sempre os termos atuais antes de implementar.

| Prioridade | Fonte | Estado conhecido (nov. 2026) | Notas |
|---|---|---|---|
| 1 | **Upload de ficheiro FIT** | Sempre disponível | Base obrigatória. Funciona com qualquer marca. Usar biblioteca oficial do FIT SDK da Garmin ou equivalente testada. |
| 2 | **Garmin Connect Developer Program** | Reaberto em out. 2026 com nível Starter para empresas pequenas; requer candidatura e aprovação | Starter inclui Activity, Health, Training API, mas sem histórico e com nº de utilizadores limitado. Candidatar cedo: pode demorar. |
| 3 | **Apple HealthKit** (iOS) | Disponível em apps nativas | **Atenção:** a VFC no Apple Health é guardada como SDNN, não rMSSD. Não misturar as duas métricas; tratar cada fonte com a sua própria linha de base. |
| 4 | **Health Connect** (Android) | A confirmar | Verificar que tipos de dados de VFC e treino expõe. |
| 5 | Wahoo, Polar, Coros, Suunto | A confirmar | Cada marca tem programa próprio; verificar termos e aprovação. |
| — | **Strava** | **Excluído** | Os termos da API proíbem o uso dos dados em aplicações de IA. Não integrar. |
| — | **Fitbit Web API** | **Desligada** a 2 nov. 2026 | Não integrar. |
| — | **Intervals.icu como ponte de dados** | **Não usar como base do produto** | Os novos termos da Garmin (out. 2026) impedem que plataformas licenciadas passem dados Garmin a serviços não aprovados. A app de IA "Intervals Pro", que funcionava assim, fechou a 12 out. 2026. O Intervals.icu serve como **referência de métodos** (secção 6), não como fonte de dados. |

**Regras de dados:**
- Guardar sempre a fonte de cada valor (dispositivo, app, introduzido manualmente, estimado).
- Deduplicar atividades que cheguem por duas vias (mesma hora de início ± 2 min e duração semelhante).
- Nunca sobrescrever dados do atleta com estimativas; as estimativas ficam marcadas.

## 6. Métricas (com testes obrigatórios)

Todas as fórmulas abaixo são padrão na literatura de treino de ciclismo. Cada uma tem de ter testes com valores de referência.

### 6.1 Potência
- **Zonas de potência:** 7 zonas de Coggan, em % do FTP (Z1 <55%, Z2 56–75%, Z3 76–90%, Z4 91–105%, Z5 106–120%, Z6 121–150%, Z7 >150%).
- **Potência normalizada (NP):** média móvel de 30 s, elevar à 4.ª potência, média, raiz 4.ª.
- **Fator de intensidade (IF):** NP / FTP.
- **TSS:** (duração_s × NP × IF) / (FTP × 3600) × 100.
- **Curva de potência:** melhores médias para 5 s, 1 min, 5 min, 20 min, 60 min.
- **FTP estimado automaticamente (eFTP), sem testes** — referência: Intervals.icu.
  - Detetar esforços máximos na curva de potência com duração entre 3 e 30 min (duração mínima configurável; por defeito 5 min).
  - Ajustar o modelo de potência crítica de 3 parâmetros de Morton e estimar o FTP a partir de um único esforço máximo. Implementar também, como alternativa configurável, o modelo de 3 parâmetros com 3 esforços (5 s, 3–5 min, 10–30 min) e o modelo de 2 parâmetros de Monod & Scherrer (3–5 min e 10–30 min).
  - Manter dois valores: eFTP da época (só esforços desta época) e eFTP com histórico, que **decai lentamente com o tempo** se não houver esforços comparáveis.
  - O modelo é sensível aos dados de entrada (um valor errado de 1 min muda muito o resultado). Por isso: só aceitar esforços de atividades que passaram a verificação de qualidade (secção 6.6), e exigir confirmação por um segundo esforço ou pelo cumprimento de treinos de limiar antes de subir o FTP mais de ~3%.
  - Qualquer alteração do FTP é **proposta ao atleta** com explicação, nunca aplicada em silêncio. Se o atleta não responder em 3 dias, aplicar apenas descidas (opção conservadora), nunca subidas.
  - Alternativa sem dados: teste guiado (ex.: 95% da média de 20 min).
- **W′ (capacidade anaeróbia):** estimar a partir da maior energia acima do eFTP na curva de potência em esforços curtos.
- **W′bal:** saldo de W′ ao longo do treino, pelo algoritmo diferencial.

### 6.2 Frequência cardíaca
- **Zonas de FC:** baseadas na FC limiar (LTHR), modelo de Friel para ciclismo. Configurável.
- **Carga por FC (HRSS, TRIMP normalizado)** — modelo por defeito no Intervals.icu para atividades sem potência:
  - Usa FC de repouso, FC limiar (LTHR) e FC máxima do atleta.
  - Normalizado na mesma escala do TSS: 1 hora perto da FC limiar ≈ 100.
  - Não precisa de histórico, por isso funciona desde o primeiro dia.
- **Modelo personalizado (quando há histórico com potência e FC):** regressão que relaciona o tempo em cada zona de FC com a carga de potência do próprio atleta. Usar só quando houver dados suficientes e o ajuste for bom; caso contrário, voltar ao HRSS.
- **Prioridade de cálculo da carga:** potência → FC (personalizado ou HRSS) → RPE × duração. Se um treino planeado tem passos com potência e com FC, usar a potência.
- **Desacoplamento aeróbio (Pa:Hr):** comparação da relação potência/FC entre a 1.ª e a 2.ª metade de esforços contínuos em Z2. Valores abaixo de ~5% indicam boa base aeróbia (parâmetro configurável).

### 6.3 Carga e forma
- **CTL (forma/condição):** média móvel exponencial do TSS diário, constante de 42 dias.
- **ATL (fadiga):** média móvel exponencial, constante de 7 dias.
- **TSB (frescura):** CTL de ontem − ATL de ontem. Fórmula diária: CTL_hoje = CTL_ontem + (TSS_hoje − CTL_ontem) / 42 (igual para ATL com 7).
- **Forma em percentagem:** forma ÷ forma física × 100. Usar a percentagem nas regras do motor, porque −20 significa coisas muito diferentes para um atleta com CTL 40 ou CTL 100.
- **Taxa de subida (ramp rate):** variação do CTL por semana; alimenta os limites de segurança (7.3).
- **Constantes de 42 e 7 dias configuráveis** por atleta (fase futura: ajustar à idade e à recuperação observada).
- Nota legal: "CTL", "ATL", "TSB", "TSS", "NP" e "IF" são marcas da TrainingPeaks. Na interface usar nomes próprios (ex.: Carga, Condição, Fadiga, Frescura, Potência ponderada), como faz o Intervals.icu. Confirmar com jurista.
- Se uma atividade não tem potência nem FC, usar RPE × duração (carga por sessão) como último recurso, marcada como estimada.

### 6.4 Recuperação (VFC e outros)
- **VFC:** usar a medição matinal ou noturna de cada fonte. Transformar em ln(rMSSD) quando a fonte fornece rMSSD.
- **Linha de base:** média móvel de 7 dias comparada com uma **faixa normal** definida pela média e desvio-padrão dos últimos ~60 dias (abordagem usada por Plews e colegas e pela HRV4Training). Largura da faixa configurável.
- Só usar a VFC no motor de decisão depois de existirem pelo menos 14 dias de dados; antes disso, mostrar "a calibrar".
- **FC de repouso:** elevação sustentada acima da linha de base pessoal é sinal de alerta.
- **Sono:** duração e, se disponível, qualidade.
- **Questionário subjetivo:** cansaço, dores musculares, stress, humor, sintomas de doença (escala 1–5).
- **Campos de bem-estar a suportar** (lista de referência do Intervals.icu): peso, FC repouso, VFC rMSSD, VFC SDNN (campo separado; é o que o Apple Health usa), duração do sono, pontuação do sono, qualidade do sono, FC média a dormir, prontidão (readiness do dispositivo), dores musculares, fadiga, stress, humor, motivação, doença, lesão, hidratação, SpO2, tensão arterial, fase do ciclo menstrual.
- A "prontidão" calculada por cada marca (Garmin, Oura, WHOOP, etc.) é guardada mas **não é usada diretamente** no motor: cada marca calcula de forma diferente. O motor usa os valores de base (VFC, FC repouso, sono) com linhas de base próprias.
- Fase do ciclo menstrual: opcional, só com consentimento explícito; pode ajustar a tolerância de fadiga (a validar).

### 6.5 Métricas de evolução aeróbia (sem testes)
- **Potência/FC (fator de eficiência):** potência ponderada ÷ FC média; e **potência/FC só em Z2**, um bom indicador de condição aeróbia.
- **Desacoplamento aeróbio** (ver 6.2).
- **Recuperação da FC (HRRc):** descida da FC após esforços intensos.
- **Tempo em zonas** e distribuição em **3 zonas de Seiler** (baixa / limiar / alta), para controlar se o treino é polarizado ou piramidal.
- **Deteção automática de intervalos** nos treinos, para comparar o planeado com o feito sem depender do botão de volta.

### 6.6 Qualidade dos dados (essencial sem treinador a supervisionar)
Com muitos atletas, ninguém revê os ficheiros à mão. Dados maus geram treinos maus. Antes de qualquer cálculo:
- **Picos de potência e FC:** detetar e corrigir automaticamente (ex.: potência impossível para a duração, FC acima da FC máxima, saltos instantâneos).
- **Falhas de sinal:** detetar quedas de potência/FC a zero e não as contar como esforço.
- **FC ótica de pulso:** marcar como menos fiável em intervalos curtos; não usar para eFTP nem para VFC de treino.
- **Potenciómetros diferentes:** permitir escala e desvio por dispositivo, e avisar o atleta quando o mesmo esforço dá valores muito diferentes entre bicicletas.
- **Atividades suspeitas** (ex.: transporte de carro gravado como volta, e-bike, rolo calibrado mal) excluídas do eFTP e marcadas para o atleta confirmar.
- Cada atividade recebe um **índice de qualidade**; só atividades acima do limiar alimentam eFTP, W′ e modelos personalizados.

## 7. Motor de adaptação

### 7.1 Princípios
- Determinístico, baseado em regras explícitas, todas configuráveis e documentadas.
- Cada decisão gera um registo com: dados de entrada, regra aplicada, treino original, treino final.
- Em caso de dúvida, o motor escolhe sempre a opção **mais conservadora**.

### 7.2 Geração do plano
- Periodização em blocos (base → construção → específico → afinação), adaptada à data da prova ou a ciclos de 4 semanas (3 de carga + 1 de recuperação) se não houver prova.
- Distribuição de intensidade por defeito: maioritariamente baixa intensidade (modelo polarizado ou piramidal, configurável).
- Biblioteca de treinos estruturados com nível de dificuldade por zona (para escolher variantes mais fáceis ou mais difíceis).
- Respeitar sempre a disponibilidade do atleta.

### 7.3 Limites de segurança (nunca ultrapassar)
- **Subida máxima de CTL por semana:** configurável; por defeito conservador (ex.: 5 pontos/semana para iniciantes, até 7–8 para avançados).
- **Máximo de dias consecutivos de alta intensidade:** 2 (configurável).
- **Semana de recuperação** obrigatória pelo menos a cada 4 semanas.
- **Sintomas de doença** reportados → sem treino de intensidade até o atleta indicar melhoria.
- **Sinais de alarme** (dor no peito, desmaio, palpitações, falta de ar anormal) no questionário → bloquear treino e mostrar mensagem clara para procurar um médico.

### 7.4 Decisão diária (matriz de prontidão)
Cada manhã, combinar os sinais disponíveis num estado:

- **Verde:** VFC dentro da faixa normal, FC repouso normal, sono razoável, sem queixas → manter o treino planeado.
- **Amarelo:** um sinal fora do normal (ex.: VFC abaixo da faixa num dia, sono curto, cansaço 4/5) → reduzir intensidade ou volume (ex.: intervalos com menos repetições ou versão mais fácil).
- **Vermelho:** vários sinais fora do normal, VFC abaixo da faixa vários dias seguidos, TSB muito negativo, ou doença → substituir por recuperação ativa ou descanso.

Regras adicionais:
- **Treino falhado:** não acumular; reorganizar a semana mantendo o treino-chave mais importante.
- **Treino feito acima/abaixo do previsto:** recalcular a carga e ajustar os dias seguintes.
- **Atividade não planeada** (ex.: volta de grupo): contabilizar a carga e ajustar.
- Se faltarem dados (sem VFC, sem dispositivo), decidir só com os disponíveis e indicar isso na explicação.

Todos os limiares (quantos dias abaixo da faixa, valor de TSB "muito negativo", etc.) ficam no ficheiro de configuração para o Paulo validar.

### 7.5 Papel da IA generativa (LLM)
- Recebe **apenas** o registo da decisão do motor (secção 7.1) e escreve a explicação ao atleta, em PT-PT ou espanhol.
- Nunca altera números, zonas ou o treino.
- Validação automática: a explicação não pode conter números diferentes dos do registo; se falhar, mostrar uma explicação-modelo pré-escrita.
- Sem conselhos médicos, de nutrição clínica ou de medicação.

### 7.6 Funcionar sozinha com muitos atletas
O Paulo não consegue acompanhar cada atleta. A app tem de se autogerir:
- **O atleta é o único humano no circuito diário.** Todas as decisões que noutra plataforma seriam do treinador (subir FTP, mudar zonas, encurtar um bloco) são propostas ao atleta com explicação e botão de aceitar/recusar.
- **Arranque a frio:** atleta novo sem histórico começa com valores conservadores, plano de base aeróbia nas primeiras 2–3 semanas e "a calibrar" visível, até existirem dados para eFTP, linha de base de VFC e modelo de carga por FC.
- **Deteção automática de situações anormais**, por atleta: cumprimento do plano abaixo de ~60% durante 2 semanas, VFC abaixo da faixa normal mais de ~5 dias, subida de FC repouso sustentada, carga muito acima do planeado, eFTP a descer de forma consistente, dados em falta há mais de 7 dias. Cada situação dispara uma ação automática (replanear, reduzir carga, perguntar ao atleta, sugerir avaliação médica).
- **Painel interno para o Paulo** que mostra **só os casos sinalizados** e estatísticas agregadas (ex.: % de atletas em vermelho, ajustes mais frequentes, regras que disparam demasiado). Serve para afinar as regras para todos, não para treinar cada um.
- **Registo de auditoria** de todas as decisões (7.1), para investigar qualquer queixa.
- **Atualizações das regras** testadas primeiro na simulação (secção 10) e lançadas de forma gradual (ex.: 10% dos atletas) antes de chegar a todos.

## 8. Experiência do atleta

### 8.1 Princípios (requisitos, não sugestões)
1. **A pergunta "o que faço hoje?" responde-se em 2 segundos** ao abrir a app, sem tocar em nada.
2. **Uma ideia por ecrã.** Detalhe só quando o atleta pede (tocar para expandir).
3. **Cada número tem significado.** Todo o valor e gráfico tem uma frase curta "o que isto quer dizer para ti", em linguagem simples, e um ícone ⓘ com explicação mais longa.
4. **Linguagem de ciclista, não de cientista.** "Frescura" em vez de "TSB"; "Estás a acumular cansaço, normal nesta fase" em vez de "TSB −18".
5. **Estado nunca só por cor:** verde/amarelo/vermelho sempre acompanhado de ícone e palavra (acessível a daltónicos e legível ao sol).
6. **Botões grandes** (mín. 48 px), uso com uma mão, legível em pleno sol, modo claro e escuro.
7. **Configuração inicial em menos de 3 minutos:** só os campos obrigatórios; o resto pede-se mais tarde, no momento em que faz falta.
8. **Sem pop-ups de venda** nem ecrãs a empurrar a subscrição durante o uso (queixa frequente nas apps concorrentes).

### 8.2 Rapidez (requisitos medidos)
- Abrir a app e ver o ecrã "Hoje": **< 1,5 s** num telemóvel de gama média, mesmo sem rede (dados em cache).
- Mudar de ecrã: **< 100 ms** percebidos (sem ecrãs brancos; usar esqueletos de carregamento).
- Gráficos com 1 ano de dados: **< 300 ms** a desenhar; zoom e deslizar a 60 fps.
- Atividade nova analisada e treino de amanhã ajustado: **< 60 s** após chegar o ficheiro.
- Funciona offline para consultar plano, treino do dia e gráficos; sincroniza quando houver rede.
- Os cálculos pesados (métricas, motor) correm no servidor e ficam pré-calculados; o telemóvel só mostra.
- Medir estes tempos automaticamente em cada versão; uma versão que piore algum deles não é lançada.

### 8.3 Ecrãs do MVP
1. **Hoje:** estado de prontidão com ícone e palavra, treino do dia (gráfico de blocos dos intervalos), explicação em 1–2 frases, botão para enviar/descarregar o treino. Por baixo, mini-gráfico de frescura dos últimos 14 dias.
2. **Manhã:** questionário de 30 segundos (deslizar ou tocar em emojis), aparece só se o atleta o ativar.
3. **Semana:** calendário com treinos planeados e feitos, barras de carga planeada vs. feita, cumprimento em %. Arrastar para mudar um treino de dia (o motor reajusta a semana).
4. **Atividade:** resumo em cima (duração, carga, potência ponderada, FC média, tempo em zonas), gráfico de potência/FC com os intervalos detetados, comparação planeado vs. feito, e o questionário pós-treino.
5. **Progresso:** os gráficos da secção 8.4.
6. **Perfil e dispositivos:** dados do atleta, zonas, ligações, privacidade, exportar/apagar dados.

### 8.4 Gráficos
Todos com período ajustável (4 semanas, 3 meses, época, ano), toque num ponto para ver o valor e a explicação, e sem mais de 2–3 linhas ao mesmo tempo.

| # | Gráfico | O que mostra | Frase-tipo para o atleta |
|---|---|---|---|
| 1 | **Forma** (principal) | Condição, Fadiga e Frescura ao longo do tempo, com **projeção futura** do plano (linha tracejada até à prova) | "Estás a construir condição. Na semana de recuperação a frescura vai subir." |
| 2 | **Faixas de frescura** | Frescura em % com faixas coloridas de fundo: transição, fresco, zona neutra, zona ótima de treino, risco elevado (limites configuráveis; referência do Intervals.icu: ótimo entre −10% e −30%, risco abaixo de −30%) | "Estás na zona ótima de treino." |
| 3 | **Prontidão** | Média de 7 dias da VFC sobre a faixa normal sombreada, com a FC de repouso por baixo | "A tua VFC está dentro do teu normal." |
| 4 | **FTP estimado** | Evolução do eFTP e W/kg, com marcadores nos esforços que o mudaram | "O teu FTP subiu 8 W desde março." |
| 5 | **Curva de potência** | Melhores potências de 5 s a 60 min: esta época vs. época anterior vs. últimos 42 dias | "És mais forte em esforços de 5 min do que no ano passado." |
| 6 | **Base aeróbia** | Potência/FC em Z2 e desacoplamento ao longo das semanas | "Produzes mais potência com a mesma FC: a tua base está a melhorar." |
| 7 | **Carga semanal** | Barras de carga planeada vs. feita + linha de cumprimento | "Cumpriste 92% do plano este mês." |
| 8 | **Distribuição da intensidade** | Tempo em 3 zonas (baixa / limiar / alta) por semana | "Esta semana foi 80% em intensidade baixa, como planeado." |

No ecrã de atividade: gráfico de potência e FC com zonas coloridas de fundo, intervalos detetados assinalados, e saldo de W′ quando houver potência.

Usar uma biblioteca de gráficos nativa e performante no telemóvel (o Claude Code propõe na Fase 0), com as mesmas cores de zonas em toda a app.

### 8.5 Validação da experiência
- Na fase alfa, testar com atletas reais de níveis diferentes, incluindo pelo menos um que nunca usou plataformas de treino: se não perceber o ecrã "Hoje" sem ajuda, o ecrã muda.
- Medir: tempo até ao primeiro treino, % de atletas que preenchem o questionário, % que abrem os gráficos, e onde desistem.

## 9. Privacidade, RGPD e responsabilidade

- FC, VFC, sono e lesões são **dados de saúde**, categoria especial no RGPD.
- **Consentimento explícito** e separado para tratar dados de saúde.
- Alojamento de dados na **União Europeia**.
- Encriptação em trânsito e em repouso.
- O atleta pode **exportar** e **apagar** todos os seus dados a qualquer momento.
- Fazer uma **avaliação de impacto (AIPD/DPIA)** antes do lançamento público. Recomenda-se validar com jurista.
- Aviso claro: a app não é um dispositivo médico, não substitui avaliação médica, e recomenda-se avaliação médico-desportiva antes de iniciar treino intenso.
- Não enviar dados identificáveis para o LLM; enviar só o registo da decisão sem nome nem contactos.

## 10. Plano de qualidade ("começar bem")

1. **Testes unitários** para todas as métricas (secção 6) com valores de referência.
2. **Ficheiros FIT de referência** reais (de várias marcas: Garmin, Wahoo, Coros, Polar) numa pasta de testes; os resultados (NP, TSS, zonas) comparados com valores calculados à parte.
   - **Validação cruzada:** carregar os mesmos ficheiros FIT do Paulo e dos atletas alfa numa conta pessoal do Intervals.icu e comparar carga, eFTP, W′, condição/fadiga/frescura e desacoplamento. Diferenças acima de ~3–5% têm de ser explicadas (método diferente, documentado) ou corrigidas.
3. **Testes do motor** com cenários de atletas fictícios: iniciante sem potenciómetro, avançado com tudo, atleta doente, atleta que falha treinos, atleta sem VFC. Para cada cenário, o resultado esperado é validado pelo Paulo.
4. **Simulação de temporada:** correr o motor sobre 6 meses de dados simulados e confirmar que nenhum limite de segurança (7.3) é ultrapassado.
5. **Monitorização de erros** em produção desde o primeiro dia.
6. **Lançamento faseado:**
   - Alfa: o Paulo e 5–10 atletas que ele treina (pelo menos 8 semanas).
   - Beta fechado: 30–50 atletas, com canal direto de feedback.
   - Lançamento público só depois de a beta não ter erros graves em pelo menos 4 semanas seguidas.
7. **Funcionalidades novas atrás de interruptores** (feature flags) para poder desligar algo sem nova versão.

## 11. Fases de desenvolvimento

| Fase | Entrega | Critério para avançar |
|---|---|---|
| 0 | Arquitetura proposta, escolha de tecnologias, `DECISOES.md` | Aprovação do Paulo |
| 1 | Importação de FIT + cálculo de métricas + testes | Todos os testes da secção 6 passam com ficheiros reais |
| 2 | Perfil do atleta + geração de plano | Planos dos cenários de teste validados pelo Paulo |
| 3 | Motor de adaptação diária + limites de segurança | Simulação de temporada sem violações |
| 4 | App móvel (ecrãs da secção 8) + explicações | Alfa com atletas do Paulo |
| 5 | Integração Garmin (se aprovada) e HealthKit/Health Connect | Dados a chegar e deduplicados corretamente |
| 6 | Pagamentos, RGPD completo, espanhol | Beta fechado |
| 7 | Lançamento público | Critérios da secção 10 cumpridos |

## 12. Tecnologia (sugestão; o Claude Code propõe na Fase 0)

- App móvel multiplataforma (iOS e Android) com acesso a HealthKit e Health Connect; ponderar React Native/Expo ou Flutter.
- Backend com boa biblioteca de leitura de FIT (Python é forte nesta área).
- Base de dados relacional (ex.: PostgreSQL) alojada na UE.
- O motor de adaptação deve ser um módulo isolado, testável sem interface nem base de dados.

## 13. Decisões em aberto (para o Paulo)

- Nome escolhido: **Wattwise**. Falta: verificação de marca (EUIPO/INPI), domínio, nome nas lojas de apps e redes sociais, e logótipo.
- Preço e se haverá versão gratuita limitada.
- Valores finais dos limites de segurança e da matriz de prontidão.
- Biblioteca inicial de treinos (o Paulo fornece ou valida).
- Empresa que submete a candidatura ao programa da Garmin.
