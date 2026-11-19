# Wattwise — Biblioteca de treinos

**118 treinos outdoor** (alvos em intervalo: terreno, vento, trânsito) e **122 indoor** (alvos fixos para o rolo em modo ERG; até 150 min), dos quais 10 do Paulo (🅿). O atleta escolhe onde treina; o plano usa a biblioteca desse ambiente (D-058).

Cada linha é um treino; a coluna *Onde* diz se existe em 🌳 outdoor, 🏠 indoor ou ambos. A estrutura mostrada é a outdoor (a indoor usa o alvo fixo do meio do intervalo). Alvos em % do FTP.

Editar: `config/treinos_outdoor.yaml`, `config/treinos_indoor.yaml` (geradas por `core/tools/gerar_biblioteca.py`), `config/treinos_paulo.yaml`, `config/nomes_treinos.yaml`.

## Rios — recuperação e resistência

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Guadiana** 🅿 | Express Z2 20 | 1 | 20 | 12 | 🏠 |  | 4 min em rampa 45→65%, cadência 90 rpm → 4 min a 65% (Z2), cadência 90 rpm → 3 × [30 s a 65% (Z2), cadência 110 rpm; 2 min 30 s a 65% (Z2), cadência 90 rpm] → 3 min a 50% (Z1), cadência 85 rpm |
| **Mondego** | Recuperação ativa | 1 | 30 | 12 | 🌳 🏠 |  | 30 min a 45–55% (Z1) |
| **Vouga** | Pernas soltas 40 min | 1 | 40 | 17 | 🌳 🏠 |  | 10 min a 45–55% (Z1) → 4 × [30 s a 50–55% (Z1), cadência 110–120 rpm; 4 min 30 s a 45–55% (Z1)] → 10 min a 45–55% (Z1) |
| **Lima** | Recuperação com cadência 45 min | 1 | 45 | 19 | 🌳 🏠 |  | 15 min a 45–55% (Z1) → 5 × [1 min a 50–55% (Z1), cadência 100–110 rpm; 3 min a 45–55% (Z1)] → 10 min a 45–55% (Z1) |
| **Tejo** | Resistência Z2 | 1 | 60 | 40 | 🌳 🏠 |  | 10 min a 50–60% (Z1) → 40 min a 62–72% (Z2) → 10 min a 50–60% (Z1) |
| **Sado** | Recuperação 60 min | 1 | 60 | 25 | 🌳 🏠 |  | 60 min a 45–55% (Z1) |
| **Paiva** | Z2 75 min | 1 | 75 | 52 | 🌳 🏠 |  | 12 min em rampa 45→70% → 55 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Zêzere** | Z2 progressivo 90 min | 2 | 90 | 63 | 🌳 🏠 |  | 12 min em rampa 45→70% → 25 min a 60–65% (Z2) → 25 min a 65–70% (Z2) → 20 min a 70–75% (Z2) → 8 min em rampa 60→45% |
| **Côa** | Z2 com força 90 min | 2 | 90 | 63 | 🌳 🏠 |  | 12 min em rampa 45→70% → 4 × [10 min a 62–72% (Z2); 5 min a 65–72% (Z2), cadência 60–65 rpm] → 10 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Minho** | Z2 com cadência 90 min | 2 | 92 | 64 | 🌳 🏠 |  | 12 min em rampa 45→70% → 6 × [9 min a 62–72% (Z2); 1 min a 62–70% (Z2), cadência 105–115 rpm] → 12 min a 60–70% (Z2) → 8 min em rampa 60→45% |
| **Tâmega** | Z2 2 h | 2 | 120 | 85 | 🌳 🏠 |  | 15 min em rampa 45→70% → 97 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Esla** | Z2 2 h 45 | 3 | 165 | 118 | 🌳 |  | 15 min em rampa 45→70% → 142 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Tormes** | Z2 3 h | 3 | 180 | 130 | 🌳 |  | 15 min em rampa 45→70% → 157 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Sil** | Z2 2 h 20 com tempo | 4 | 140 | 105 | 🌳 🏠 |  | 15 min em rampa 45→70% → 60 min a 62–72% (Z2) → 2 × [10 min a 76–82% (Z3); 10 min a 62–70% (Z2)] → 17 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Cávado** | Z2 2 h 30 com sprints | 4 | 158 | 117 | 🌳 | sim | 15 min em rampa 45→70% → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 20 min a 62–72% (Z2) → 10 s a 150–200% (Z7) → 50 s a 55–65% (Z2) → 9 min a 62–72% (Z2) → 8 min em rampa 60→45% |
| **Douro** | Z2 longo 3 h com tempo no fim | 4 | 193 | 147 | 🌳 |  | 15 min em rampa 45→70% → 120 min a 62–72% (Z2) → 3 × [10 min a 76–85% (Z3); 5 min a 60–65% (Z2)] → 5 min a 55–65% (Z2) → 8 min em rampa 60→45% |
| **Guadalquivir** | Z2 longo 4 h com sweet spot | 5 | 235 | 186 | 🌳 |  | 15 min em rampa 45→70% → 60 min a 62–72% (Z2) → 2 × [15 min a 88–92% (Z3); 10 min a 60–68% (Z2)] → 90 min a 62–72% (Z2) → 12 min a 55–65% (Z2) → 8 min em rampa 60→45% |
| **Ebro** | Z2 longo 5 h | 5 | 293 | 202 | 🌳 |  | 15 min em rampa 45→70% → 270 min a 60–70% (Z2) → 8 min em rampa 60→45% |

## Serras — tempo

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Montesinho** 🅿 | Express Tempo 30 | 1 | 30 | 27 | 🏠 |  | 5 min em rampa 45→70%, cadência 90 rpm → 2 × [10 min a 80% (Z3), cadência 90 rpm; 2 min a 55% (Z1), cadência 90 rpm] → 1 min a 50% (Z1), cadência 85 rpm |
| **Arada** | Tempo 2 × 10 min (40 min) | 1 | 41 | 32 | 🌳 🏠 |  | 10 min em rampa 45→72% → 2 × [10 min a 76–82% (Z3); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Freita** | Tempo 3 × 8 min (48 min) | 2 | 48 | 38 | 🌳 🏠 |  | 10 min em rampa 45→72% → 3 × [8 min a 76–82% (Z3); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Sintra** | Tempo 2 × 15 min | 2 | 60 | 48 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [15 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Arrábida** | Tempo 3 × 10 min | 2 | 65 | 50 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [10 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Candeeiros** | Tempo 2 × 18 min (55 min) | 3 | 57 | 50 | 🌳 🏠 |  | 10 min em rampa 45→72% → 2 × [18 min a 76–85% (Z3); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Sicó** | Tempo 3 × 13 min (59 min) | 3 | 60 | 53 | 🌳 🏠 |  | 10 min em rampa 45→72% → 3 × [13 min a 76–85% (Z3); 2 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Marão** | Tempo 3 × 12 min | 3 | 68 | 55 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [12 min a 76–85% (Z3); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Gredos** | Tempo 2 × 20 min | 3 | 70 | 59 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [20 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Bussaco** | Tempo 4 × 10 min | 3 | 76 | 62 | 🌳 🏠 |  | 12 min em rampa 45→70% → 4 × [10 min a 76–85% (Z3); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Estrela** | Tempo 3 × 14 min (60 min) | 4 | 60 | 55 | 🌳 🏠 |  | 8 min em rampa 45→75% → 3 × [14 min a 76–85% (Z3); 1 min 30 s a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Alvão** | Tempo 3 × 15 min | 4 | 80 | 67 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [15 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Malcata** | Tempo progressivo 3 × 15 min | 4 | 80 | 68 | 🌳 🏠 |  | 12 min em rampa 45→70% → 5 min a 76–79% (Z3) → 5 min a 80–83% (Z3) → 5 min a 84–87% (Z3) → 5 min a 50–60% (Z1) → 5 min a 76–79% (Z3) → 5 min a 80–83% (Z3) → 5 min a 84–87% (Z3) → 5 min a 50–60% (Z1) → 5 min a 76–79% (Z3) → 5 min a 80–83% (Z3) → 5 min a 84–87% (Z3) → 5 min a 50–60% (Z1) → 8 min em rampa 60→45% |
| **Aire** | Tempo contínuo 40 min (55 min) | 5 | 55 | 51 | 🌳 🏠 |  | 10 min em rampa 45→72% → 40 min a 76–85% (Z3) → 5 min em rampa 60→45% |
| **Moncayo** | Tempo contínuo 45 min | 5 | 68 | 61 | 🌳 🏠 |  | 15 min em rampa 45→70% → 45 min a 76–85% (Z3) → 8 min em rampa 60→45% |
| **Sierra Morena** | Tempo contínuo 60 min | 5 | 83 | 77 | 🌳 🏠 |  | 15 min em rampa 45→70% → 60 min a 76–85% (Z3) → 8 min em rampa 60→45% |
| **Guadarrama** | Tempo 2 × 30 min | 5 | 90 | 80 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [30 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Picos de Europa** | Tempo 3 × 25 min | 5 | 113 | 101 | 🌳 🏠 |  | 15 min em rampa 45→70% → 3 × [25 min a 76–85% (Z3); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |

## Serras — sweet spot

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Gerês** 🅿 | Express Sweet Spot 30 | 1 | 30 | 30 | 🏠 |  | 5 min em rampa 45→70%, cadência 90 rpm → 2 × [9 min a 90% (Z3), cadência 90 rpm; 3 min a 50% (Z1), cadência 90 rpm] → 1 min a 50% (Z1), cadência 85 rpm |
| **Bornes** | Sweet spot 2 × 10 min (40 min) | 1 | 41 | 38 | 🌳 🏠 |  | 10 min em rampa 45→72% → 2 × [10 min a 88–92% (Z3); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Peneda** 🅿 | Express Sweet Spot 25 Contínuo | 2 | 25 | 26 | 🏠 |  | 5 min em rampa 45→75%, cadência 90 rpm → 15 min a 90% (Z3), cadência 90 rpm → 5 min em rampa 60→45%, cadência 85 rpm |
| **Gardunha** | Sweet spot 2 × 14 min (48 min) | 2 | 49 | 49 | 🌳 🏠 |  | 10 min em rampa 45→72% → 2 × [14 min a 88–93% (Z4); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Lousã** | Sweet spot 2 × 12 min | 2 | 52 | 47 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [12 min a 88–93% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Caramulo** | Sweet spot 3 × 10 min | 2 | 65 | 59 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [10 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Larouco** | Sweet spot 3 × 11 min (55 min) | 3 | 57 | 58 | 🌳 🏠 |  | 10 min em rampa 45→72% → 3 × [11 min a 88–93% (Z4); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Montemuro** | Sweet spot 2 × 20 min (59 min) | 3 | 59 | 65 | 🌳 🏠 |  | 10 min em rampa 45→72% → 20 min a 88–93% (Z4) → 4 min a 50–60% (Z1) → 20 min a 88–93% (Z4) → 5 min em rampa 60→45% |
| **Monchique** | Sweet spot 3 × 12 min | 3 | 68 | 66 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [12 min a 88–93% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Cazorla** | Sweet spot 2 × 20 min | 3 | 70 | 70 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [20 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Grazalema** | Sweet spot progressivo 2 × 20 min | 3 | 70 | 71 | 🌳 🏠 |  | 12 min em rampa 45→70% → 10 min a 88–90% (Z3) → 10 min a 92–94% (Z4) → 5 min a 50–60% (Z1) → 10 min a 88–90% (Z3) → 10 min a 92–94% (Z4) → 5 min a 50–60% (Z1) → 8 min em rampa 60→45% |
| **Montseny** | Sweet spot com acelerações 3 × 12 min | 3 | 71 | 72 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [1 min 50 s a 88–92% (Z3); 10 s a 130–150% (Z6)] → 5 min a 50–60% (Z1) → 6 × [1 min 50 s a 88–92% (Z3); 10 s a 130–150% (Z6)] → 5 min a 50–60% (Z1) → 6 × [1 min 50 s a 88–92% (Z3); 10 s a 130–150% (Z6)] → 5 min a 50–60% (Z1) → 8 min em rampa 60→45% |
| **Ossa** | Sweet spot 5 × 8 min | 3 | 75 | 73 | 🌳 🏠 |  | 12 min em rampa 45→70% → 5 × [8 min a 88–93% (Z4); 3 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Açor** | Sweet spot 4 × 10 min | 3 | 76 | 73 | 🌳 🏠 |  | 12 min em rampa 45→70% → 4 × [10 min a 88–93% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Javalambre** | Sweet spot 3 × 13 min (58 min) | 4 | 58 | 63 | 🌳 🏠 |  | 8 min em rampa 45→75% → 3 × [13 min a 88–93% (Z4); 2 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Urbión** | Sweet spot 2 × 22 min | 4 | 74 | 76 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [22 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Montejunto** | Sweet spot 3 × 15 min | 4 | 80 | 79 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [15 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Aitana** | Sweet spot contínuo 45 min (58 min) | 5 | 58 | 68 | 🌳 🏠 |  | 8 min em rampa 45→75% → 45 min a 88–92% (Z3) → 5 min em rampa 60→45% |
| **Sierra Nevada** | Sweet spot 2 × 30 min | 5 | 90 | 97 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [30 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Peña de Francia** | Sweet spot 3 × 20 min | 5 | 95 | 100 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [20 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Gata** | Sweet spot 4 × 15 min | 5 | 100 | 102 | 🌳 🏠 |  | 12 min em rampa 45→70% → 4 × [15 min a 88–93% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |

## Subidas míticas — limiar

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Ancares** | Limiar 3 × 4 min (39 min) | 1 | 39 | 33 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 3 × [4 min a 95–100% (Z4); 4 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **El Fito** | Limiar 3 × 5 min (42 min) | 1 | 42 | 38 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 3 × [5 min a 95–100% (Z4); 4 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Fóia** | Limiar 3 × 8 min | 2 | 56 | 55 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [8 min a 95–102% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Lagoa Comprida** | Limiar 2 × 12 min | 2 | 56 | 55 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 2 × [12 min a 95–102% (Z4); 6 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **La Camperona** | Limiar sobe e desce 2 × 12 min | 2 | 56 | 57 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [2 min a 95–97% (Z4); 1 min a 108–112% (Z5)] → 6 min a 50–60% (Z1) → 4 × [2 min a 95–97% (Z4); 1 min a 108–112% (Z5)] → 6 min a 50–60% (Z1) → 8 min em rampa 60→45% |
| **Malhão** | Limiar 4 × 6 min | 2 | 60 | 57 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [6 min a 95–102% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Calar Alto** | Limiar 2 × 15 min (50 min) | 3 | 50 | 58 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 15 min a 95–100% (Z4) → 5 min a 50–60% (Z1) → 15 min a 95–100% (Z4) → 5 min em rampa 60→45% |
| **Velefique** | Limiar 3 × 9 min (51 min) | 3 | 51 | 56 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 3 × [9 min a 95–102% (Z4); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Trevim** | Limiar 5 × 5 min | 3 | 60 | 58 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [5 min a 95–100% (Z4); 3 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Navacerrada** | Limiar 2 × 15 min | 3 | 62 | 65 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 2 × [15 min a 95–102% (Z4); 6 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Senhora da Graça** | Limiar sobe e desce 3 × 9 min | 3 | 62 | 63 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [1 min 30 s a 95–97% (Z4); 1 min 30 s a 103–106% (Z4)] → 5 min a 50–60% (Z1) → 3 × [1 min 30 s a 95–97% (Z4); 1 min 30 s a 103–106% (Z4)] → 5 min a 50–60% (Z1) → 3 × [1 min 30 s a 95–97% (Z4); 1 min 30 s a 103–106% (Z4)] → 5 min a 50–60% (Z1) → 8 min em rampa 60→45% |
| **Penhas Douradas** | Limiar 3 × 10 min | 3 | 65 | 66 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [10 min a 95–102% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Torre** | Limiar 4 × 8 min | 3 | 68 | 70 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [8 min a 95–102% (Z4); 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Covão d'Ametade** | Limiar 3 × 11 min (55 min) | 4 | 55 | 64 | 🌳 🏠 | sim | 8 min em rampa 45→75% → 3 × [11 min a 95–100% (Z4); 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Lagos de Covadonga** | Limiar 3 × 12 min | 4 | 71 | 76 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [12 min a 95–102% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Angliru** | Limiar 2 × 20 min | 4 | 76 | 83 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 2 × [20 min a 95–102% (Z4); 8 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Bola del Mundo** | Limiar 4 × 10 min | 4 | 80 | 85 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [10 min a 95–102% (Z4); 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Valdelinares** | Limiar contínuo 30 min | 5 | 53 | 60 | 🌳 🏠 | sim | 15 min em rampa 45→70% → 30 min a 95–100% (Z4) → 8 min em rampa 60→45% |
| **La Farrapona** | Limiar 4 × 9 min (57 min) | 5 | 57 | 68 | 🌳 🏠 | sim | 8 min em rampa 45→75% → 4 × [9 min a 95–100% (Z4); 2 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Ézaro** | Limiar 3 × 15 min | 5 | 83 | 91 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [15 min a 95–100% (Z4); 6 min a 50–60% (Z1)] → 8 min em rampa 60→45% |

## Ventos — VO2máx

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Brisa** | Ativação pré-prova 3 × 1 min | 1 | 42 | 28 | 🌳 🏠 | sim | 20 min a 55–70% (Z2) → 3 × [1 min a 110–120% (Z5); 3 min a 45–55% (Z1)] → 10 min a 50–60% (Z1) |
| **Gregal** | VO2máx 2 × 12 × 15/15 s | 1 | 44 | 34 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 12 × [15 s a 120–130% (Z6); 15 s a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 12 × [15 s a 120–130% (Z6); 15 s a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Nortada** | VO2máx 4 × 3 min | 2 | 44 | 40 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [3 min a 106–115% (Z5); 3 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Levante** | VO2máx 5 × 3 min | 2 | 50 | 47 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [3 min a 106–115% (Z5); 3 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Galerno** | VO2máx pirâmide 2-3-4-3-2 | 2 | 51 | 47 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 2 min a 110–120% (Z5) → 2 min a 45–55% (Z1) → 3 min a 108–115% (Z5) → 3 min a 45–55% (Z1) → 4 min a 106–112% (Z5) → 4 min a 45–55% (Z1) → 3 min a 108–115% (Z5) → 3 min a 45–55% (Z1) → 2 min a 110–120% (Z5) → 5 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Terral** | VO2máx 3 × 8 × 30/30 s | 2 | 59 | 50 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [30 s a 115–125% (Z5); 30 s a 45–55% (Z1)] → 5 min a 45–55% (Z1) → 8 × [30 s a 115–125% (Z5); 30 s a 45–55% (Z1)] → 5 min a 45–55% (Z1) → 8 × [30 s a 115–125% (Z5); 30 s a 45–55% (Z1)] → 5 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Ábrego** | VO2máx 2 × 10 × 40/20 s | 3 | 52 | 51 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 10 × [40 s a 118–125% (Z6); 20 s a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 10 × [40 s a 118–125% (Z6); 20 s a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Barlavento** | VO2máx 8 × 2 min | 3 | 52 | 52 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [2 min a 110–120% (Z5); 2 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Sotavento** | VO2máx 4 × 4 min | 3 | 52 | 50 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [4 min a 106–115% (Z5); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Siroco** | VO2máx 3 × 6 min | 3 | 53 | 51 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 3 × [6 min a 105–110% (Z5); 5 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Poniente** | VO2máx 6 × 3 min | 3 | 56 | 55 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [3 min a 106–115% (Z5); 3 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Cierzo** | VO2máx 5 × 4 min | 3 | 60 | 61 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [4 min a 106–118% (Z5); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Mestral** | VO2máx com arranque 5 × 4 min | 3 | 60 | 61 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 30 s a 130–140% (Z6) → 3 min 30 s a 106–112% (Z5) → 4 min a 45–55% (Z1) → 30 s a 130–140% (Z6) → 3 min 30 s a 106–112% (Z5) → 4 min a 45–55% (Z1) → 30 s a 130–140% (Z6) → 3 min 30 s a 106–112% (Z5) → 4 min a 45–55% (Z1) → 30 s a 130–140% (Z6) → 3 min 30 s a 106–112% (Z5) → 4 min a 45–55% (Z1) → 30 s a 130–140% (Z6) → 3 min 30 s a 106–112% (Z5) → 4 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Zéfiro** | VO2máx 4 × 5 min (44 min) | 4 | 47 | 53 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 4 × [5 min a 106–112% (Z5); 3 min a 45–55% (Z1)] → 5 min em rampa 60→45% |
| **Llebeig** | VO2máx 4 × 6 min | 4 | 64 | 65 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [6 min a 105–110% (Z5); 5 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Tramontana** | VO2máx 6 × 4 min | 4 | 68 | 72 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [4 min a 108–120% (Z5); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Alísio** | VO2máx 5 × 5 min (50 min) | 5 | 50 | 62 | 🌳 🏠 | sim | 8 min em rampa 45→75% → 5 × [5 min a 106–112% (Z5); 2 min 30 s a 45–55% (Z1)] → 5 min em rampa 60→45% |
| **Vendaval** | VO2máx 5 × 5 min | 5 | 70 | 72 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [5 min a 106–115% (Z5); 5 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Rajada** | VO2máx 2 × 8 × 2 min | 5 | 80 | 93 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [2 min a 112–118% (Z5); 1 min a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 8 × [2 min a 112–118% (Z5); 1 min a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 8 min em rampa 60→45% |

## Ventos — anaeróbio

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Garbí** | Sprints 6 × 15 s | 1 | 50 | 30 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [15 s a 150–200% (Z7); 4 min 45 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Solano** | Sprints 10 × 10 s | 1 | 50 | 33 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 10 × [10 s a 170–220% (Z7); 2 min 50 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Ventisca** | Anaeróbio 6 × 30 s (40 min) | 2 | 39 | 27 | 🌳 🏠 | sim | 10 min em rampa 45→72% → 6 × [30 s a 130–150% (Z6); 3 min 30 s a 45–55% (Z1)] → 5 min em rampa 60→45% |
| **Remoinho** | Anaeróbio 4 × 1 min | 2 | 40 | 28 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [1 min a 120–130% (Z6); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Suão** | Anaeróbio 8 × 30 s | 2 | 60 | 38 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [30 s a 130–150% (Z6); 4 min 30 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Xaloc** | Anaeróbio 6 × 45 s | 3 | 50 | 34 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [45 s a 125–140% (Z6); 4 min 15 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Migjorn** | Anaeróbio 6 × 1 min | 3 | 50 | 36 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [1 min a 120–130% (Z6); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Bochorno** | Anaeróbio 10 × 30 s | 3 | 50 | 37 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 10 × [30 s a 130–150% (Z6); 2 min 30 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Matacabras** | Anaeróbio 2 × 8 × 20/10 s | 4 | 44 | 38 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [20 s a 140–160% (Z6); 10 s a 40–50% (Z1)] → 8 min a 45–55% (Z1) → 8 × [20 s a 140–160% (Z6); 10 s a 40–50% (Z1)] → 8 min a 45–55% (Z1) → 8 min em rampa 60→45% |
| **Furacão** | Anaeróbio 8 × 1 min | 4 | 52 | 41 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [1 min a 120–130% (Z6); 3 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Galerna** | Anaeróbio 5 × 2 min | 5 | 50 | 43 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [2 min a 118–125% (Z6); 4 min a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Ventania** | Anaeróbio 2 × 5 × 1 min | 5 | 62 | 50 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [1 min a 120–130% (Z6); 2 min a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 5 × [1 min a 120–130% (Z6); 2 min a 45–55% (Z1)] → 6 min a 45–55% (Z1) → 8 min em rampa 60→45% |

## Castelos — força

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Penedono** | Arranques 5 × 15 s em cadência baixa | 2 | 45 | 25 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [15 s a 140–160% (Z6), cadência 40–60 rpm; 4 min 45 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Almourol** 🅿 | Arranques de Força 45 | 2 | 45 | 29 | 🏠 | sim | 12 min em rampa 45→70%, cadência 90 rpm → 8 × [15 s a 150% (Z6), cadência 40–60 rpm; 2 min 15 s a 50% (Z1), cadência 90 rpm] → 5 min a 65% (Z2), cadência 90 rpm → 8 min em rampa 60→45%, cadência 90 rpm |
| **Guimarães** 🅿 | Torque ao Limiar 10x1 | 2 | 50 | 38 | 🏠 | sim | 12 min em rampa 45→70%, cadência 90 rpm → 10 × [1 min a 100% (Z4), cadência 50 rpm; 1 min a 50% (Z1), cadência 95 rpm] → 10 min a 65% (Z2), cadência 90 rpm → 8 min em rampa 60→45%, cadência 90 rpm |
| **Belver** | Arranques 8 × 20 s em cadência baixa | 3 | 44 | 29 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 8 × [20 s a 140–160% (Z6), cadência 40–60 rpm; 2 min 40 s a 45–55% (Z1)] → 8 min em rampa 60→45% |
| **Trancoso** | Força 3 × 8 min a 60 rpm | 3 | 56 | 41 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [8 min a 76–80% (Z3), cadência 55–65 rpm; 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Marvão** | Força 5 × 5 min em cadência baixa | 3 | 60 | 45 | 🌳 🏠 |  | 12 min em rampa 45→70% → 5 × [5 min a 78–82% (Z3), cadência 50–60 rpm; 3 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Peñíscola** | Força ao limiar 4 × 5 min | 3 | 60 | 52 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 4 × [5 min a 95–100% (Z4), cadência 50–60 rpm; 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Alcazaba** 🅿 | Força Sweet Spot 5x6 | 3 | 60 | 55 | 🏠 |  | 10 min em rampa 45→70%, cadência 90 rpm → 5 × [6 min a 90% (Z3), cadência 58–62 rpm; 3 min a 50% (Z1), cadência 95 rpm] → 5 min em rampa 60→45%, cadência 90 rpm |
| **Loarre** | Força em subida 6 × 4 min | 3 | 62 | 52 | 🌳 🏠 |  | 12 min em rampa 45→70% → 6 × [4 min a 88–92% (Z3), cadência 50–60 rpm; 3 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Belmonte** | Força 3 × 10 min a 60 rpm | 3 | 65 | 52 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [10 min a 80–85% (Z3), cadência 55–65 rpm; 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Almeida** | Força 4 × 8 min a sweet spot (56 min) | 4 | 59 | 57 | 🌳 🏠 |  | 10 min em rampa 45→72% → 4 × [8 min a 88–92% (Z3), cadência 55–62 rpm; 3 min a 50–60% (Z1)] → 5 min em rampa 60→45% |
| **Monsaraz** 🅿 | Contraste de Cadência 60 | 4 | 60 | 58 | 🏠 |  | 10 min em rampa 45→70%, cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 3 min a 88% (Z3), cadência 58–62 rpm → 3 min a 88% (Z3), cadência 98–102 rpm → 2 min a 50% (Z1), cadência 90 rpm → 2 min em rampa 60→45%, cadência 90 rpm |
| **Peñafiel** 🅿 | Força Tempo 4x8 | 4 | 60 | 52 | 🏠 |  | 10 min em rampa 45→70%, cadência 90 rpm → 4 × [8 min a 85% (Z3), cadência 55–60 rpm; 4 min a 50% (Z1), cadência 95 rpm] → 2 min em rampa 60→45%, cadência 90 rpm |
| **Óbidos** 🅿 | Força Longa 3x12 | 4 | 65 | 52 | 🏠 |  | 10 min em rampa 45→70%, cadência 90 rpm → 3 × [12 min a 80% (Z3), cadência 50–55 rpm; 5 min a 50% (Z1), cadência 95 rpm] → 4 min em rampa 60→45%, cadência 90 rpm |
| **Sabugal** | Força a tempo 2 × 20 min | 4 | 70 | 60 | 🌳 🏠 |  | 12 min em rampa 45→70% → 2 × [20 min a 78–85% (Z3), cadência 55–65 rpm; 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Coca** | Força ao limiar 5 × 6 min | 4 | 75 | 71 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 5 × [6 min a 95–100% (Z4), cadência 50–60 rpm; 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **Cardona** | Força ao limiar 6 × 6 min | 5 | 80 | 80 | 🌳 🏠 | sim | 12 min em rampa 45→70% → 6 × [6 min a 95–100% (Z4), cadência 50–60 rpm; 4 min a 50–60% (Z1)] → 8 min em rampa 60→45% |
| **La Mota** | Força 3 × 15 min a sweet spot | 5 | 80 | 79 | 🌳 🏠 |  | 12 min em rampa 45→70% → 3 × [15 min a 88–92% (Z3), cadência 55–62 rpm; 5 min a 50–60% (Z1)] → 8 min em rampa 60→45% |

## Faróis — testes

| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |
|---|---|---|---|---|---|---|---|
| **Finisterra** | Teste de FC limiar (30 min, sem potenciómetro) | 3 | 55 | 64 | 🌳 🏠 | sim | 15 min a 55–70% (Z2) → 30 min a 95–105% (Z4) → 10 min a 45–55% (Z1) |
| **Sagres** | Teste de FTP (20 min) | 3 | 65 | 69 | 🌳 🏠 | sim | 20 min a 55–70% (Z2) → 5 min a 105–115% (Z5) → 10 min a 50–60% (Z1) → 20 min a 100–110% (Z4) → 10 min a 45–55% (Z1) |
