/** Componentes base do estilo Wattwise. Botões com área de toque ≥ 44 px (spec 8.1). */
import React from 'react';
import { Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { cor, coresZonas, letra, raio, sombra, zonaDe } from '../tema';

// ------------------------------------------------------------ ícones (traço, nunca emoji)
type NomeIcone = 'relogio' | 'calendario' | 'grafico' | 'pessoa' | 'aviso' | 'check' | 'alarme' | 'bicicleta'
  | 'casa' | 'descarregar' | 'voltar' | 'seta' | 'lua' | 'logo';

export function Icone({ nome, cor: c = cor.tinta, tamanho = 20, espessura = 2 }:
  { nome: NomeIcone; cor?: string; tamanho?: number; espessura?: number }) {
  const p = { stroke: c, strokeWidth: espessura, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, fill: 'none' };
  const d: Record<NomeIcone, React.ReactNode> = {
    relogio: <><Circle cx={12} cy={12} r={8.5} {...p} /><Path d="M12 7.5V12l3 2" {...p} /></>,
    calendario: <><Rect x={3.5} y={5} width={17} height={15.5} rx={3} {...p} /><Path d="M3.5 10h17M8.5 3v4M15.5 3v4" {...p} /></>,
    grafico: <Path d="M4 19.5h16M5 15l4.5-4.5 3.5 3 6-6.5" {...p} />,
    pessoa: <><Circle cx={12} cy={8.5} r={3.8} {...p} /><Path d="M4.5 20.5c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5" {...p} /></>,
    aviso: <Path d="M12 3 2 20h20L12 3zM12 10v4M12 17.5v.5" {...p} />,
    check: <Path d="m5 12.5 4.5 4.5L19 7.5" {...p} />,
    alarme: <><Circle cx={12} cy={12} r={10} {...p} /><Path d="M12 7v6M12 16.5v.5" {...p} /></>,
    bicicleta: <><Circle cx={5.5} cy={17} r={3.5} {...p} /><Circle cx={18.5} cy={17} r={3.5} {...p} /><Path d="M5.5 17 9 9h6l3.5 8M9 9l3 8h2M14 5h2l-1 4" {...p} /></>,
    casa: <Path d="M3 11 12 4l9 7v9H3v-9zM9 20v-6h6v6" {...p} />,
    descarregar: <Path d="M12 3v12M7 10l5 5 5-5M5 21h14" {...p} />,
    voltar: <Path d="m15 18-6-6 6-6" {...p} />,
    seta: <Path d="m9 6 6 6-6 6" {...p} />,
    lua: <Path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" {...p} />,
    logo: <Path d="M3 6l4 12 5-9 5 9 4-12" {...p} />,
  };
  return <Svg width={tamanho} height={tamanho} viewBox="0 0 24 24" accessibilityElementsHidden importantForAccessibility="no">{d[nome]}</Svg>;
}

// ------------------------------------------------------------ texto
export function T({ children, estilo, ...props }: { children: React.ReactNode; estilo?: object } & React.ComponentProps<typeof Text>) {
  return <Text style={[{ fontFamily: letra.corpo, color: cor.tinta, fontSize: 14 }, estilo]} {...props}>{children}</Text>;
}

export function EtiquetaSecao({ children, claro = false }: { children: React.ReactNode; claro?: boolean }) {
  return <T estilo={{ fontFamily: letra.negrito, fontSize: 11, letterSpacing: 0.9, color: claro ? cor.heroiMuted : cor.tinta2 }}>{children}</T>;
}

// ------------------------------------------------------------ contentores
export function Cartao({ children, estilo }: { children: React.ReactNode; estilo?: ViewStyle }) {
  return <View style={[{ backgroundColor: cor.superficie, borderRadius: raio.cartao, padding: 14, gap: 8 }, sombra, estilo]}>{children}</View>;
}

export function Heroi({ children, estilo }: { children: React.ReactNode; estilo?: ViewStyle }) {
  return <View style={[{ backgroundColor: cor.heroi, borderRadius: raio.heroi, padding: 18, gap: 12 }, estilo]}>{children}</View>;
}

// ------------------------------------------------------------ botões
export function Botao({ texto, aoTocar, icone, desativado = false, secundario = false }:
  { texto: string; aoTocar: () => void; icone?: NomeIcone; desativado?: boolean; secundario?: boolean }) {
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ disabled: desativado }} disabled={desativado} onPress={aoTocar}
      style={({ pressed }) => [estilos.botao, secundario && estilos.botaoSec, desativado && { backgroundColor: '#D1D5DB' }, pressed && { opacity: 0.85 }]}>
      {icone ? <Icone nome={icone} cor={secundario ? cor.tinta : cor.lima} tamanho={18} espessura={2.2} /> : null}
      <T estilo={{ fontFamily: letra.negrito, fontSize: 15, color: desativado ? cor.tinta2 : secundario ? cor.tinta : '#FFFFFF' }}>{texto}</T>
    </Pressable>
  );
}

/** Grupo de opções (escala 1–5, sim/não, indoor/outdoor…). A escolhida fica grafite com texto lima. */
export function Opcoes<V extends string | number>({ valores, valor, aoMudar, rotulo, perigo, rotulos }:
  { valores: V[]; valor: V | null; aoMudar: (v: V) => void; rotulo: string; perigo?: (v: V) => boolean; rotulos?: Record<string, string> }) {
  return (
    <View accessibilityRole="radiogroup" accessibilityLabel={rotulo} style={{ flexDirection: 'row', gap: 6 }}>
      {valores.map((v) => {
        const sel = v === valor;
        const vermelho = sel && perigo?.(v);
        return (
          <Pressable key={String(v)} accessibilityRole="radio" accessibilityState={{ checked: sel }} accessibilityLabel={`${rotulo}: ${v}`}
            onPress={() => aoMudar(v)}
            style={[estilos.opcao, sel && { backgroundColor: vermelho ? cor.perigo : cor.tinta }]}>
            <T estilo={{ fontFamily: letra.negrito, fontSize: 14.5, color: sel ? (vermelho ? '#FFFFFF' : cor.lima) : cor.tinta }}>
              {rotulos?.[String(v)] ?? String(v)}
            </T>
          </Pressable>
        );
      })}
    </View>
  );
}

// ------------------------------------------------------------ gráfico de blocos do treino (cores das zonas)
export function Blocos({ passos, altura = 50 }: { passos: { segundos: number; pct_min: number; pct_max: number }[]; altura?: number }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 2, height: altura }} accessibilityLabel="Estrutura do treino por zonas">
      {passos.map((p, i) => {
        const pct = (p.pct_min + p.pct_max) / 2;
        return <View key={i} style={{ flexGrow: p.segundos, flexBasis: 0, height: Math.max(4, Math.min(1, pct / 130) * altura),
          backgroundColor: coresZonas[zonaDe(pct)], borderRadius: 3 }} />;
      })}
    </View>
  );
}

// ------------------------------------------------------------ esqueleto de carregamento (sem ecrãs brancos, spec 8.2)
export function Esqueleto({ altura, escuro = false }: { altura: number; escuro?: boolean }) {
  return <View style={{ height: altura, borderRadius: raio.cartao, backgroundColor: escuro ? '#1F242B' : '#E5E7EB' }} />;
}

const estilos = StyleSheet.create({
  botao: { height: 54, borderRadius: raio.botao, backgroundColor: cor.tinta, flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: 8 },
  botaoSec: { backgroundColor: cor.superficie, ...sombra },
  opcao: { flex: 1, minHeight: 44, borderRadius: 12, backgroundColor: cor.fundo, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
});
