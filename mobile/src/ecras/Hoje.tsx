/** Ecrã "Hoje": responde a "o que faço hoje?" em 2 segundos (spec 8.1). */
import React, { useCallback, useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, View } from 'react-native';
import Svg, { Circle, Polyline, Rect } from 'react-native-svg';

import { api, ComCache, Hoje as HojeJ, Treino } from '../api';
import { Blocos, Botao, Cartao, EtiquetaSecao, Esqueleto, Heroi, Icone, T } from '../componentes/base';
import { cor, letra, sombra } from '../tema';

const ESTADOS = {
  verde: { palavra: 'Pronto · plano mantido', fundo: '#22C55E', icone: 'check' as const },
  amarelo: { palavra: 'Atenção · dia mais leve', fundo: cor.aviso, icone: 'aviso' as const },
  vermelho: { palavra: 'Recuperar · dia leve', fundo: '#F87171', icone: 'lua' as const },
  bloqueado: { palavra: 'Não treinar hoje', fundo: '#F87171', icone: 'alarme' as const },
};

const DIAS = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
function dataLonga(iso: string) {
  const d = new Date(iso + 'T12:00:00');
  return `${DIAS[d.getDay()]}, ${d.getDate()} de ${MESES[d.getMonth()]}`;
}

function alvoPrincipal(t: Treino): string {
  const trab = t.passos.filter((p) => !p.rampa && (p.pct_min + p.pct_max) / 2 >= 76);
  return (trab[0] ?? t.passos[Math.floor(t.passos.length / 2)])?.alvo.split(' (')[0] ?? '';
}

export function Hoje({ atleta, data, abrirManha }: { atleta: number; data?: string; abrirManha: () => void }) {
  const [r, setR] = useState<ComCache<HojeJ> | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [escolha, setEscolha] = useState<'outdoor' | 'indoor'>('outdoor');

  const carregar = useCallback(async () => {
    try {
      setErro(null);
      setR(await api.hojeComCache(atleta, data));
    } catch (e) { setErro((e as Error).message); }
  }, [atleta, data]);
  useEffect(() => { carregar(); }, [carregar]);

  if (erro) return <View style={{ padding: 20, gap: 12 }}><T>Não foi possível carregar o treino de hoje.</T><T estilo={{ color: cor.tinta2 }}>{erro}</T><Botao texto="Tentar outra vez" aoTocar={carregar} /></View>;
  if (!r) return <View style={{ padding: 20, gap: 14 }}><Esqueleto altura={44} /><Esqueleto altura={260} escuro /><Esqueleto altura={110} /><Esqueleto altura={110} /></View>;

  const h = r.dados;
  const est = ESTADOS[h.estado];
  const opcoes = h.treino?.opcoes ?? [];
  const sel = opcoes.find((o) => o.ambiente === escolha) ?? opcoes[0];

  async function escolher(amb: 'outdoor' | 'indoor') {
    setEscolha(amb);
    try { await api.escolha(atleta, amb, h.data); } catch { /* sem rede: fica no telemóvel e sincroniza depois */ }
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 14 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', minHeight: 44 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <View style={{ width: 32, height: 32, borderRadius: 10, backgroundColor: cor.tinta, alignItems: 'center', justifyContent: 'center' }}>
            <Icone nome="logo" cor={cor.lima} tamanho={18} espessura={2.6} />
          </View>
          <View>
            <T estilo={{ fontFamily: letra.titulo, fontSize: 17 }}>Hoje</T>
            <T estilo={{ fontSize: 12, color: cor.tinta2, fontFamily: letra.medio }}>{dataLonga(h.data)}</T>
          </View>
        </View>
        <Pressable accessibilityRole="button" onPress={abrirManha}
          style={[{ flexDirection: 'row', alignItems: 'center', gap: 6, minHeight: 44, paddingHorizontal: 14, borderRadius: 22, backgroundColor: cor.superficie }, sombra]}>
          <Icone nome={h.dados_em_falta.includes('questionario') ? 'lua' : 'check'} cor={h.dados_em_falta.includes('questionario') ? cor.tinta : cor.ok} tamanho={15} espessura={2.4} />
          <T estilo={{ fontFamily: letra.semi, fontSize: 12.5 }}>{h.dados_em_falta.includes('questionario') ? 'Responder à manhã' : 'Manhã respondida'}</T>
        </Pressable>
      </View>

      {r.offline ? <T estilo={{ fontSize: 12.5, color: cor.avisoTexto, backgroundColor: cor.avisoFundo, padding: 10, borderRadius: 12 }}>Sem rede: a mostrar o plano guardado.</T> : null}

      <Heroi>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, height: 28, paddingHorizontal: 10, borderRadius: 14, backgroundColor: est.fundo }}>
            <Icone nome={est.icone} cor={cor.tinta} tamanho={15} espessura={2.4} />
            <T estilo={{ fontFamily: letra.negrito, fontSize: 12 }}>{est.palavra}</T>
          </View>
          {h.treino?.prioridade ? <T estilo={{ color: cor.heroiMuted, fontSize: 12 }}>Prova {h.treino.prioridade}</T> : null}
        </View>

        {h.estado === 'bloqueado' ? (
          <T estilo={{ color: '#FFFFFF', fontSize: 17, lineHeight: 24, fontFamily: letra.semi }}>{h.explicacao}</T>
        ) : sel ? (
          <>
            <View>
              <T estilo={{ fontFamily: letra.titulo, fontSize: 34, color: '#FFFFFF', letterSpacing: -1 }}>{sel.nome}</T>
              <T estilo={{ fontSize: 14, color: cor.heroiSuave }}>{sel.subtitulo || sel.tipo}</T>
            </View>
            <Blocos passos={sel.passos} altura={54} />
            <View style={{ flexDirection: 'row', borderTopWidth: 1, borderTopColor: cor.heroiLinha, paddingTop: 10 }}>
              {[['DURAÇÃO', `${sel.minutos} min`], ['CARGA', String(Math.round(sel.carga))], ['ALVO', alvoPrincipal(sel)]].map(([k, v]) => (
                <View key={k} style={{ flex: 1, gap: 1 }}>
                  <EtiquetaSecao claro>{k}</EtiquetaSecao>
                  <T estilo={{ fontFamily: letra.tituloBold, fontSize: 17, color: '#FFFFFF' }} numberOfLines={1}>{v}</T>
                </View>
              ))}
            </View>
            <T estilo={{ fontSize: 13, lineHeight: 19, color: cor.heroiSuave }}>{h.explicacao}</T>
          </>
        ) : (
          <>
            <T estilo={{ fontFamily: letra.titulo, fontSize: 30, color: '#FFFFFF' }}>Descanso</T>
            <T estilo={{ fontSize: 13, lineHeight: 19, color: cor.heroiSuave }}>{h.explicacao}</T>
          </>
        )}
      </Heroi>

      {opcoes.length > 1 ? (
        <View style={{ gap: 8 }}>
          <EtiquetaSecao>ESCOLHE A VERSÃO</EtiquetaSecao>
          <View style={{ flexDirection: 'row', gap: 10 }}>
            {opcoes.map((o) => {
              const ativo = o.ambiente === escolha;
              return (
                <Pressable key={o.ambiente} accessibilityRole="radio" accessibilityState={{ checked: ativo }} onPress={() => escolher(o.ambiente)}
                  style={[{ flex: 1, padding: 14, borderRadius: 20, backgroundColor: cor.superficie, gap: 4, borderWidth: 2,
                    borderColor: ativo ? cor.tinta : 'transparent' }, sombra]}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Icone nome={o.ambiente === 'indoor' ? 'casa' : 'bicicleta'} tamanho={17} />
                      <T estilo={{ fontFamily: letra.negrito, fontSize: 13 }}>{o.ambiente === 'indoor' ? 'Indoor' : 'Outdoor'}</T>
                    </View>
                    <View style={{ width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center',
                      backgroundColor: ativo ? cor.lima : 'transparent', borderWidth: ativo ? 0 : 1.5, borderColor: '#D1D5DB' }}>
                      {ativo ? <Icone nome="check" tamanho={12} espessura={3.5} /> : null}
                    </View>
                  </View>
                  <T estilo={{ fontFamily: letra.tituloBold, fontSize: 17 }}>{alvoPrincipal(o)}</T>
                  <T estilo={{ fontSize: 12, color: cor.tinta2 }}>{o.ambiente === 'indoor' ? 'fixo · modo ERG' : 'intervalo · estrada'}</T>
                </Pressable>
              );
            })}
          </View>
        </View>
      ) : null}

      {sel && h.treino?.papel !== 'prova' ? (
        <Botao icone="descarregar" texto={sel.ambiente === 'indoor' ? 'Enviar para o rolo (ZWO)' : 'Descarregar o treino (ZWO)'}
          aoTocar={() => Linking.openURL(api.urlExportar(atleta, h.data, 'zwo', sel.ambiente))} />
      ) : null}

      {h.frescura_pct !== null ? (
        <Cartao>
          <EtiquetaSecao>FRESCURA</EtiquetaSecao>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
            <View>
              <T estilo={{ fontFamily: letra.titulo, fontSize: 26 }}>{h.frescura_pct > 0 ? '+' : ''}{Math.round(h.frescura_pct)}%</T>
              <T estilo={{ fontSize: 12, fontFamily: letra.semi, color: h.frescura_pct < -30 ? cor.avisoTexto : cor.ok }}>
                {h.frescura_pct < -30 ? 'muita fadiga' : h.frescura_pct < -10 ? 'zona ótima' : h.frescura_pct < 5 ? 'neutra' : 'fresco'}
              </T>
            </View>
            <Svg width={200} height={40} accessibilityLabel={`Frescura ${Math.round(h.frescura_pct)}%`}>
              <Rect x={0} y={8} width={200} height={24} rx={4} fill={cor.okFundo} />
              <Circle cx={Math.max(6, Math.min(194, 100 + h.frescura_pct * 2))} cy={20} r={6} fill={cor.tinta} />
              <Polyline points="100,4 100,36" stroke="#9CA3AF" strokeWidth={1} />
            </Svg>
          </View>
        </Cartao>
      ) : null}
    </ScrollView>
  );
}
