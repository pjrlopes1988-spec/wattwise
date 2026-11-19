/** Semana: treinos planeados, carga e fases (spec 8.3). */
import React, { useEffect, useState } from 'react';
import { ScrollView, View } from 'react-native';

import { api, ComCache, Plano } from '../api';
import { Cartao, EtiquetaSecao, Esqueleto, Heroi, T } from '../componentes/base';
import { cor, coresZonas, letra } from '../tema';

const FASES: Record<string, string> = { base: 'Base', construcao: 'Construção', especifico: 'Específico', recuperacao: 'Recuperação', afinacao: 'Afinação' };
const SEM = ['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SÁB'];
const COR_TIPO: Record<string, string> = { recuperacao: coresZonas[0], resistencia: coresZonas[1], tempo: coresZonas[2], sweetspot: coresZonas[2],
  forca: coresZonas[3], limiar: coresZonas[3], vo2max: coresZonas[4], anaerobio: coresZonas[5], teste: coresZonas[4], prova: coresZonas[6] };

export function Semana({ atleta }: { atleta: number }) {
  const [r, setR] = useState<ComCache<Plano> | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  useEffect(() => { api.planoComCache(atleta).then(setR).catch((e) => setErro(e.message)); }, [atleta]);
  if (erro) return <T estilo={{ padding: 20 }}>{erro}</T>;
  if (!r) return <View style={{ padding: 20, gap: 14 }}><Esqueleto altura={44} /><Esqueleto altura={170} escuro /><Esqueleto altura={360} /></View>;

  const hoje = new Date().toISOString().slice(0, 10);
  const s = r.dados.semanas.find((x) => x.inicio <= hoje && hoje < somaDias(x.inicio, 7)) ?? r.dados.semanas[0];
  const dias = Array.from({ length: 7 }, (_, i) => somaDias(s.inicio, i));
  const porDia = Object.fromEntries(s.treinos.map((t) => [t.data, t]));
  const max = Math.max(1, ...s.treinos.map((t) => Math.max(...t.opcoes.map((o) => o.carga))));

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 14 }}>
      <View style={{ minHeight: 44, justifyContent: 'flex-end' }}>
        <T estilo={{ fontFamily: letra.titulo, fontSize: 22 }}>Semana</T>
        <T estilo={{ fontSize: 12, color: cor.tinta2 }}>{FASES[s.fase]} · semana {s.numero} de {r.dados.semanas.length}</T>
      </View>
      <Heroi>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <View><EtiquetaSecao claro>CARGA PLANEADA</EtiquetaSecao>
            <T estilo={{ fontFamily: letra.titulo, fontSize: 30, color: cor.lima }}>{s.carga_planeada}</T></View>
          <View style={{ alignItems: 'flex-end' }}><EtiquetaSecao claro>CONDIÇÃO NO FIM</EtiquetaSecao>
            <T estilo={{ fontFamily: letra.tituloBold, fontSize: 18, color: '#FFFFFF' }}>{Math.round(s.condicao_fim)}</T></View>
        </View>
        <View style={{ flexDirection: 'row', gap: 6, alignItems: 'flex-end', height: 80 }}>
          {dias.map((d) => {
            const t = porDia[d];
            const c = t ? Math.max(...t.opcoes.map((o) => o.carga)) : 0;
            return (
              <View key={d} style={{ flex: 1, alignItems: 'center', gap: 6 }}>
                <View style={{ width: '70%', height: Math.max(4, (c / max) * 56), borderRadius: 6,
                  backgroundColor: d === hoje ? '#FFFFFF' : d < hoje ? cor.lima : '#3A414C', opacity: c ? 1 : 0.35 }} />
                <T estilo={{ fontSize: 11, fontFamily: letra.negrito, color: d === hoje ? '#FFFFFF' : cor.heroiMuted }}>{SEM[new Date(d + 'T12:00:00').getDay()][0]}</T>
              </View>
            );
          })}
        </View>
      </Heroi>
      <Cartao estilo={{ gap: 0, paddingVertical: 4 }}>
        {dias.map((d, i) => {
          const t = porDia[d];
          const o = t?.opcoes[0];
          return (
            <View key={d} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52, borderTopWidth: i ? 1 : 0, borderTopColor: cor.linha }}>
              <View style={{ width: 38, alignItems: 'center' }}>
                <T estilo={{ fontSize: 10.5, color: cor.tinta2, fontFamily: letra.negrito }}>{SEM[new Date(d + 'T12:00:00').getDay()]}</T>
                <T estilo={{ fontFamily: letra.tituloBold, fontSize: 18 }}>{Number(d.slice(8))}</T>
              </View>
              <View style={{ width: 4, height: 32, borderRadius: 2, backgroundColor: o ? COR_TIPO[o.tipo] ?? cor.neutro : cor.neutro }} />
              <View style={{ flex: 1 }}>
                <T estilo={{ fontFamily: letra.negrito, fontSize: 14.5 }}>{o ? (t.papel === 'prova' ? o.nome : o.nome) : 'Descanso'}</T>
                <T estilo={{ fontSize: 12, color: cor.tinta2 }}>{o ? `${o.subtitulo || o.tipo} · ${o.minutos} min${t.opcoes.length > 1 ? ' · outdoor ou indoor' : ''}` : 'Sem treino'}</T>
              </View>
              {d === hoje ? <T estilo={{ fontSize: 11.5, fontFamily: letra.negrito, color: cor.lima, backgroundColor: cor.tinta, paddingHorizontal: 9, paddingVertical: 4, borderRadius: 10, overflow: 'hidden' }}>Hoje</T> : null}
              {t?.prioridade ? <T estilo={{ fontSize: 11.5, fontFamily: letra.negrito, color: '#4C1D95', backgroundColor: '#EDE9FE', paddingHorizontal: 9, paddingVertical: 4, borderRadius: 10, overflow: 'hidden' }}>Prova {t.prioridade}</T> : null}
            </View>
          );
        })}
      </Cartao>
    </ScrollView>
  );
}

function somaDias(iso: string, n: number) {
  const d = new Date(iso + 'T12:00:00');
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}
