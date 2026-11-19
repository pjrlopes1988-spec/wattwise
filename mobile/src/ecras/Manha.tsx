/** Questionário da manhã: 30 segundos (spec 8.3). Sinais de alarme → mensagem para procurar médico. */
import React, { useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';

import { api } from '../api';
import { Botao, Cartao, Icone, Opcoes, T } from '../componentes/base';
import { cor, letra, sombra } from '../tema';

const PERGUNTAS: [string, string, string][] = [
  ['cansaco', 'Cansaço', '1 fresco · 5 exausto'], ['dores', 'Dores musculares', '1 nada · 5 muitas'],
  ['stress', 'Stress', '1 calmo · 5 muito'], ['humor', 'Humor e motivação', '1 em baixo · 5 ótimo'],
];

export function Manha({ atleta, voltar }: { atleta: number; voltar: () => void }) {
  const [v, setV] = useState<Record<string, number>>({ cansaco: 2, dores: 2, stress: 2, humor: 4 });
  const [sono, setSono] = useState<number | null>(7);
  const [doenca, setDoenca] = useState<'Não' | 'Sintomas' | 'Febre'>('Não');
  const [alarme, setAlarme] = useState<'Não' | 'Sim'>('Não');
  const [aGuardar, setAGuardar] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function guardar() {
    setAGuardar(true); setErro(null);
    try {
      await api.manha(atleta, { ...v, sono_h: sono, doenca: doenca !== 'Não', febre: doenca === 'Febre',
        alarmes: alarme === 'Sim' ? ['dor_peito'] : [] });
      voltar();
    } catch (e) { setErro((e as Error).message); } finally { setAGuardar(false); }
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={voltar}
          style={[{ width: 44, height: 44, borderRadius: 22, backgroundColor: cor.superficie, alignItems: 'center', justifyContent: 'center' }, sombra]}>
          <Icone nome="voltar" tamanho={20} espessura={2.2} />
        </Pressable>
        <View>
          <T estilo={{ fontFamily: letra.titulo, fontSize: 22 }}>Bom dia</T>
          <T estilo={{ fontSize: 12.5, color: cor.tinta2 }}>30 segundos para ajustar o treino de hoje</T>
        </View>
      </View>

      <Cartao>
        <T estilo={{ fontFamily: letra.negrito }}>Horas de sono</T>
        <Opcoes rotulo="Horas de sono" valores={[5, 6, 7, 8, 9]} valor={sono} aoMudar={setSono}
          rotulos={{ 5: '≤ 5', 9: '9 +' }} />
      </Cartao>

      <Cartao estilo={{ gap: 0, paddingVertical: 6 }}>
        {PERGUNTAS.map(([k, titulo, legenda], i) => (
          <View key={k} style={{ gap: 8, paddingVertical: 10, borderTopWidth: i ? 1 : 0, borderTopColor: cor.linha }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <T estilo={{ fontFamily: letra.negrito }}>{titulo}</T>
              <T estilo={{ fontSize: 11.5, color: cor.tinta2 }}>{legenda}</T>
            </View>
            <Opcoes rotulo={titulo} valores={[1, 2, 3, 4, 5]} valor={v[k]} aoMudar={(n) => setV({ ...v, [k]: n })} />
          </View>
        ))}
      </Cartao>

      <Cartao estilo={{ gap: 12 }}>
        <T estilo={{ fontFamily: letra.negrito }}>Sentes-te doente?</T>
        <Opcoes rotulo="Sentes-te doente?" valores={['Não', 'Sintomas', 'Febre'] as const as unknown as string[]} valor={doenca}
          aoMudar={(x) => setDoenca(x as typeof doenca)} perigo={(x) => x !== 'Não'} />
        <View style={{ borderTopWidth: 1, borderTopColor: cor.linha, paddingTop: 12, gap: 8 }}>
          <T estilo={{ fontFamily: letra.negrito, lineHeight: 19 }}>Dor no peito, desmaio, palpitações ou falta de ar fora do normal?</T>
          <Opcoes rotulo="Sinais de alarme" valores={['Não', 'Sim']} valor={alarme} aoMudar={(x) => setAlarme(x as typeof alarme)} perigo={(x) => x === 'Sim'} />
          {alarme === 'Sim' ? (
            <View accessibilityRole="alert" style={{ flexDirection: 'row', gap: 10, padding: 12, borderRadius: 14, backgroundColor: cor.perigoFundo }}>
              <Icone nome="alarme" cor={cor.perigo} tamanho={22} espessura={2.2} />
              <T estilo={{ flex: 1, fontSize: 13.5, lineHeight: 19, color: cor.perigoTexto }}>
                <T estilo={{ fontFamily: letra.negrito, color: cor.perigoTexto, fontSize: 13.5 }}>Não treines hoje. </T>
                Procura um médico. Se for agora e for forte, liga 112.
              </T>
            </View>
          ) : null}
        </View>
      </Cartao>

      {erro ? <T estilo={{ color: cor.perigoTexto }}>{erro}</T> : null}
      <Botao texto={aGuardar ? 'A guardar…' : 'Guardar e ver o treino de hoje'} aoTocar={guardar} desativado={aGuardar} />
    </ScrollView>
  );
}
