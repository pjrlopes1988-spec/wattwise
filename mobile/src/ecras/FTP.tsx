/** FTP manual (D-071): vale a partir de hoje; recusado fora de 1–7 W/kg; aviso se longe do eFTP. */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';

import { api, AtletaJ } from '../api';
import { Botao, Cartao, EtiquetaSecao, Heroi, Icone, Opcoes, T } from '../componentes/base';
import { cor, coresZonas, letra, sombra } from '../tema';

const LIMITES = [55, 75, 90, 105, 120, 150];

export function FTP({ atleta, voltar }: { atleta: number; voltar: () => void }) {
  const [a, setA] = useState<AtletaJ | null>(null);
  const [ftp, setFtp] = useState(250);
  const [modo, setModo] = useState('automatico');
  const [pedirConfirmacao, setPedirConfirmacao] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => { api.atleta(atleta).then((x) => { setA(x); setFtp(Math.round(x.perfil.ftp?.valor ?? 200)); setModo(x.perfil.ftp_modo); }); }, [atleta]);
  if (!a) return null;

  const peso = a.perfil.peso_kg, wkg = ftp / peso;
  const dif = a.eftp ? ((ftp - a.eftp) / a.eftp) * 100 : null;
  const impossivel = wkg < 1 || wkg > 7;

  async function guardar() {
    setMsg(null);
    try {
      if (modo !== a!.perfil.ftp_modo) await api.preferencias(atleta, { ftp_modo: modo });
      const r = await api.ftp(atleta, ftp, pedirConfirmacao);
      if (!r.guardado) { setPedirConfirmacao(true); setMsg('Bem diferente do eFTP. Toca outra vez em Guardar para confirmar.'); return; }
      voltar();
    } catch (e) { setMsg((e as Error).message); }
  }

  const passo = (d: number, rot: string) => (
    <Pressable accessibilityRole="button" accessibilityLabel={`${d > 0 ? 'Mais' : 'Menos'} ${Math.abs(d)} watts`} onPress={() => { setFtp(Math.max(30, ftp + d)); setPedirConfirmacao(false); }}
      style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: cor.heroiLinha, alignItems: 'center', justifyContent: 'center' }}>
      <T estilo={{ color: '#FFFFFF', fontFamily: letra.negrito, fontSize: Math.abs(d) > 1 ? 14 : 20 }}>{rot}</T>
    </Pressable>
  );

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: 16, gap: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pressable accessibilityRole="button" accessibilityLabel="Voltar" onPress={voltar}
          style={[{ width: 44, height: 44, borderRadius: 22, backgroundColor: cor.superficie, alignItems: 'center', justifyContent: 'center' }, sombra]}>
          <Icone nome="voltar" tamanho={20} espessura={2.2} />
        </Pressable>
        <T estilo={{ fontFamily: letra.titulo, fontSize: 22 }}>FTP e zonas</T>
      </View>
      <Heroi>
        <EtiquetaSecao claro>O MEU FTP · A PARTIR DE HOJE</EtiquetaSecao>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          {passo(-5, '−5')}{passo(-1, '−')}
          <View style={{ alignItems: 'center' }}>
            <T estilo={{ fontFamily: letra.titulo, fontSize: 46, color: '#FFFFFF', letterSpacing: -1.5 }}>{ftp}<T estilo={{ fontSize: 18, color: cor.heroiMuted }}> W</T></T>
            <T estilo={{ color: cor.lima, fontFamily: letra.negrito, fontSize: 13 }}>{wkg.toFixed(1).replace('.', ',')} W/kg</T>
          </View>
          {passo(1, '+')}{passo(5, '+5')}
        </View>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: cor.heroiLinha, paddingTop: 10 }}>
          <T estilo={{ color: cor.heroiSuave, fontSize: 12.5 }}>eFTP pelos treinos: {a.eftp ? `${a.eftp} W` : 'a calibrar'}</T>
          {dif !== null ? <T estilo={{ fontSize: 12.5, fontFamily: letra.negrito, color: Math.abs(dif) > 15 ? cor.aviso : '#86EFAC' }}>{dif >= 0 ? '+' : '−'}{Math.abs(dif).toFixed(0)}%</T> : null}
        </View>
      </Heroi>
      {impossivel ? <T estilo={{ backgroundColor: cor.perigoFundo, color: cor.perigoTexto, padding: 12, borderRadius: 16 }}>Valor impossível: tem de estar entre 1 e 7 W/kg.</T> : null}
      {msg ? <T estilo={{ backgroundColor: cor.avisoFundo, color: cor.avisoTexto, padding: 12, borderRadius: 16 }}>{msg}</T> : null}
      <Cartao>
        <EtiquetaSecao>AS TUAS ZONAS</EtiquetaSecao>
        <View style={{ flexDirection: 'row', gap: 4 }}>
          {coresZonas.map((c, i) => (
            <View key={c} style={{ flex: 1, alignItems: 'center', gap: 4 }}>
              <View style={{ width: '100%', height: 10 + i * 5, borderRadius: 4, backgroundColor: c }} />
              <T estilo={{ fontSize: 11, fontFamily: letra.negrito }}>Z{i + 1}</T>
              <T estilo={{ fontSize: 10.5, color: cor.tinta2 }}>{i < 6 ? `≤${Math.round((ftp * LIMITES[i]) / 100)}` : `>${Math.round(ftp * 1.5)}`}</T>
            </View>
          ))}
        </View>
      </Cartao>
      <Cartao>
        <T estilo={{ fontFamily: letra.negrito, fontSize: 13.5 }}>Quem gere o FTP?</T>
        <Opcoes rotulo="Modo do FTP" valores={['automatico', 'manual']} valor={modo} aoMudar={setModo} rotulos={{ automatico: 'Automático', manual: 'Manual' }} />
        <T estilo={{ fontSize: 12, color: cor.tinta3, lineHeight: 17 }}>{modo === 'automatico'
          ? 'O teu valor é respeitado. Se os treinos mostrarem que mudou, propomos um ajuste e decides tu.'
          : 'Só tu mudas o FTP. O eFTP aparece apenas como informação.'}</T>
      </Cartao>
      <Botao texto={pedirConfirmacao ? 'Confirmar e guardar' : 'Guardar FTP'} aoTocar={guardar} desativado={impossivel} />
    </ScrollView>
  );
}
