/** Perfil: provas A–D, escolhas do atleta (onde treina, ciclos, intensidade) e acesso ao FTP (spec 8.3). */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';

import { api, AtletaJ } from '../api';
import { Cartao, EtiquetaSecao, Esqueleto, Icone, Opcoes, T } from '../componentes/base';
import { cor, letra } from '../tema';

const SELO: Record<string, [string, string]> = { A: [cor.tinta, cor.lima], B: ['#1D4ED8', '#FFFFFF'], C: ['#15803D', '#FFFFFF'], D: ['#E5E7EB', '#374151'] };
const NIVEL: Record<string, string> = { iniciante: 'Iniciante', intermedio: 'Intermédio', avancado: 'Avançado', competicao: 'Competição' };

export function Perfil({ atleta, abrirFTP }: { atleta: number; abrirFTP: () => void }) {
  const [a, setA] = useState<AtletaJ | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const carregar = () => api.atleta(atleta).then(setA).catch((e) => setErro(e.message));
  useEffect(() => { carregar(); }, [atleta]);
  if (erro) return <T estilo={{ padding: 20 }}>{erro}</T>;
  if (!a) return <View style={{ padding: 20, gap: 14 }}><Esqueleto altura={52} /><Esqueleto altura={220} /><Esqueleto altura={200} /></View>;
  const p = a.perfil;
  const iniciais = p.nome.split(' ').map((x) => x[0]).slice(0, 2).join('');

  async function mudar(campo: string, valor: unknown) {
    try { await api.preferencias(atleta, { [campo]: valor }); await carregar(); } catch (e) { setErro((e as Error).message); }
  }
  const onde = p.onde_treina ?? (a.ambientes.length > 1 ? 'ambos' : a.ambientes[0]);

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52 }}>
        <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: cor.tinta, alignItems: 'center', justifyContent: 'center' }}>
          <T estilo={{ fontFamily: letra.titulo, fontSize: 18, color: cor.lima }}>{iniciais}</T>
        </View>
        <View style={{ flex: 1 }}>
          <T estilo={{ fontFamily: letra.titulo, fontSize: 20 }}>{p.nome}</T>
          <T estilo={{ fontSize: 12.5, color: cor.tinta2 }}>{NIVEL[p.nivel] ?? p.nivel} · {p.disciplina} · FTP {p.ftp ? Math.round(p.ftp.valor) : '—'} W</T>
        </View>
      </View>

      <Cartao estilo={{ gap: 0 }}>
        <EtiquetaSecao>AS MINHAS PROVAS</EtiquetaSecao>
        {p.provas.length === 0 ? <T estilo={{ color: cor.tinta2, paddingVertical: 10 }}>Ainda sem provas. Adiciona as tuas provas A a D.</T> : null}
        {p.provas.map((x, i) => (
          <View key={x.nome + x.data} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 50, borderTopWidth: i ? 1 : 0, borderTopColor: cor.linha }}>
            <View style={{ width: 30, height: 30, borderRadius: 9, alignItems: 'center', justifyContent: 'center', backgroundColor: SELO[x.prioridade][0] }}>
              <T estilo={{ fontFamily: letra.titulo, fontSize: 15, color: SELO[x.prioridade][1] }}>{x.prioridade}</T>
            </View>
            <View style={{ flex: 1 }}>
              <T estilo={{ fontFamily: letra.negrito }}>{x.nome}</T>
              <T estilo={{ fontSize: 12, color: cor.tinta2 }}>{x.data}{x.etapas.length ? ` · ${x.etapas.length} etapas` : x.duracao_h ? ` · ${x.duracao_h} h` : ''}</T>
            </View>
          </View>
        ))}
      </Cartao>

      <Cartao estilo={{ gap: 14 }}>
        <View style={{ gap: 7 }}><T estilo={{ fontFamily: letra.negrito, fontSize: 13.5 }}>Onde vais treinar?</T>
          <Opcoes rotulo="Onde vais treinar" valores={['outdoor', 'indoor', 'ambos']} valor={onde} aoMudar={(v) => mudar('onde_treina', v)}
            rotulos={{ outdoor: 'Outdoor', indoor: 'Indoor', ambos: 'Ambos' }} /></View>
        <View style={{ gap: 7 }}><T estilo={{ fontFamily: letra.negrito, fontSize: 13.5 }}>Ciclos de treino</T>
          <Opcoes rotulo="Ciclos" valores={['3+1', '2+1']} valor={p.ciclo ?? '3+1'} aoMudar={(v) => mudar('ciclo', v)} rotulos={{ '3+1': '3 + 1', '2+1': '2 + 1' }} /></View>
        <View style={{ gap: 7 }}><View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <T estilo={{ fontFamily: letra.negrito, fontSize: 13.5 }}>Intensidade que preferes</T>
          <T estilo={{ fontSize: 11.5, color: cor.tinta2 }}>1 suave · 5 agressivo</T></View>
          <Opcoes rotulo="Intensidade" valores={[1, 2, 3, 4, 5]} valor={a.intensidade} aoMudar={(v) => mudar('agressividade', v)} /></View>
      </Cartao>

      <Pressable accessibilityRole="button" onPress={abrirFTP}>
        <Cartao estilo={{ flexDirection: 'row', alignItems: 'center', minHeight: 52 }}>
          <T estilo={{ flex: 1, fontFamily: letra.semi }}>FTP e zonas</T>
          <T estilo={{ color: cor.tinta2, fontSize: 12.5 }}>{p.ftp ? `${Math.round(p.ftp.valor)} W · editar` : 'definir'}</T>
          <Icone nome="seta" cor="#9CA3AF" tamanho={16} espessura={2.2} />
        </Cartao>
      </Pressable>
    </ScrollView>
  );
}
