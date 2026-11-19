/** Progresso: Condição prevista pelo plano até ao objetivo (gráfico 1 da spec 8.4). */
import React, { useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';
import Svg, { Circle, Line, Polyline } from 'react-native-svg';

import { api, AtletaJ, ComCache, Plano } from '../api';
import { Cartao, EtiquetaSecao, Esqueleto, Heroi, T } from '../componentes/base';
import { cor, letra } from '../tema';

export function Progresso({ atleta }: { atleta: number }) {
  const [p, setP] = useState<ComCache<Plano> | null>(null);
  const [a, setA] = useState<ComCache<AtletaJ> | null>(null);
  useEffect(() => { api.planoComCache(atleta).then(setP).catch(() => {}); api.atletaComCache(atleta).then(setA).catch(() => {}); }, [atleta]);
  if (!p || !a) return <View style={{ padding: 20, gap: 14 }}><Esqueleto altura={44} /><Esqueleto altura={240} escuro /></View>;

  const sem = p.dados.semanas;
  const vals = [sem[0] ? sem[0].condicao_fim - 5 : 0, ...sem.map((s) => s.condicao_fim)];
  const mx = Math.max(10, ...vals);
  const L = 320, A = 120;
  const pontos = vals.map((v, i) => `${Math.round((i / (vals.length - 1)) * (L - 8)) + 4},${Math.round(A - 6 - (v / mx) * (A - 18))}`).join(' ');
  const ultimo = pontos.split(' ').pop()!.split(',').map(Number);
  const ftp = a.dados.perfil.ftp?.valor;
  const wkg = ftp ? (ftp / a.dados.perfil.peso_kg).toFixed(1).replace('.', ',') : '—';

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 14 }}>
      <T estilo={{ fontFamily: letra.titulo, fontSize: 22, minHeight: 44, textAlignVertical: 'bottom' }}>Progresso</T>
      <Heroi>
        <EtiquetaSecao claro>CONDIÇÃO PREVISTA PELO PLANO</EtiquetaSecao>
        <T estilo={{ fontFamily: letra.titulo, fontSize: 32, color: '#FFFFFF' }}>{Math.round(vals[vals.length - 1])}
          <T estilo={{ fontSize: 15, color: cor.lima, fontFamily: letra.negrito }}>  no fim do plano</T></T>
        <Svg width={L} height={A} accessibilityLabel="Condição prevista semana a semana">
          <Line x1={0} y1={A - 1} x2={L} y2={A - 1} stroke={cor.heroiLinha} />
          <Polyline points={pontos} fill="none" stroke={cor.lima} strokeWidth={2.6} strokeDasharray="6 4" />
          <Circle cx={ultimo[0]} cy={ultimo[1]} r={5} fill="#A855F7" />
        </Svg>
        <T estilo={{ fontSize: 13, color: cor.heroiSuave, lineHeight: 19 }}>
          Linha tracejada: o que o plano prevê se cumprires. Com treinos registados, aparece a tua curva real.
        </T>
      </Heroi>
      <View style={{ flexDirection: 'row', gap: 10 }}>
        <Cartao estilo={{ flex: 1 }}><EtiquetaSecao>FTP</EtiquetaSecao>
          <T estilo={{ fontFamily: letra.titulo, fontSize: 20 }}>{ftp ? `${Math.round(ftp)} W` : '—'}</T>
          <T estilo={{ fontSize: 11.5, color: cor.tinta3 }}>{wkg} W/kg</T></Cartao>
        <Cartao estilo={{ flex: 1 }}><EtiquetaSecao>eFTP DOS TREINOS</EtiquetaSecao>
          <T estilo={{ fontFamily: letra.titulo, fontSize: 20 }}>{a.dados.eftp ? `${a.dados.eftp} W` : '—'}</T>
          <T estilo={{ fontSize: 11.5, color: cor.tinta3 }}>{a.dados.eftp ? 'pelos teus esforços' : 'a calibrar'}</T></Cartao>
      </View>
    </ScrollView>
  );
}
