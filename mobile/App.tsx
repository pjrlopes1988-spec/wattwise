/** Wattwise — app do atleta. Separadores: Hoje, Semana, Progresso, Perfil (spec 8.3). */
import { InterTight_700Bold, InterTight_800ExtraBold } from '@expo-google-fonts/inter-tight';
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, useFonts } from '@expo-google-fonts/inter';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import { api } from './src/api';
import { Icone, T } from './src/componentes/base';
import { FTP } from './src/ecras/FTP';
import { Hoje } from './src/ecras/Hoje';
import { Manha } from './src/ecras/Manha';
import { Perfil } from './src/ecras/Perfil';
import { Progresso } from './src/ecras/Progresso';
import { Semana } from './src/ecras/Semana';
import { cor, letra } from './src/tema';

type Separador = 'hoje' | 'semana' | 'progresso' | 'perfil';
const SEPARADORES: [Separador, string, 'relogio' | 'calendario' | 'grafico' | 'pessoa'][] = [
  ['hoje', 'Hoje', 'relogio'], ['semana', 'Semana', 'calendario'], ['progresso', 'Progresso', 'grafico'], ['perfil', 'Perfil', 'pessoa'],
];

// Até haver o registo inicial (onboarding), a app cria um atleta de demonstração no servidor de desenvolvimento.
const PERFIL_DEMO = {
  nome: 'Bruno Matos', data_nascimento: '1985-06-02', sexo: 'M', peso_kg: 74, nivel: 'intermedio', disciplina: 'estrada',
  objetivo: { tipo: 'ftp' }, disponibilidade: [60, 90, 0, 90, 60, 180, 240], dia_longo: 6,
  equipamento: { potenciometro: true, rolo_inteligente: true, cinta_fc: true },
  ftp: { valor: 258, fonte: 'atleta' }, fc_limiar: { valor: 168, fonte: 'atleta' }, fc_max: { valor: 186, fonte: 'atleta' },
  fc_repouso: { valor: 48, fonte: 'atleta' },
};

export default function App() {
  const [fontes] = useFonts({ Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, InterTight_700Bold, InterTight_800ExtraBold });
  const [atleta, setAtleta] = useState<number | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [sep, setSep] = useState<Separador>('hoje');
  const [sobreposto, setSobreposto] = useState<'manha' | 'ftp' | null>(null);
  const [versao, setVersao] = useState(0);   // força recarregar depois de guardar

  useEffect(() => {
    (async () => {
      try {
        const guardado = await AsyncStorage.getItem('wattwise:atleta').catch(() => null);
        if (guardado) { setAtleta(Number(guardado)); return; }
        const { id } = await api.criar(PERFIL_DEMO);
        await AsyncStorage.setItem('wattwise:atleta', String(id)).catch(() => {});
        setAtleta(id);
      } catch (e) { setErro((e as Error).message); }
    })();
  }, []);

  if (!fontes) return <View style={{ flex: 1, backgroundColor: cor.fundo }} />;
  const fechar = () => { setSobreposto(null); setVersao((v) => v + 1); };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={{ flex: 1, backgroundColor: cor.fundo }} edges={['top']}>
        <StatusBar style="dark" />
        <View style={{ flex: 1 }}>
          {erro ? <T estilo={{ padding: 20 }}>Sem ligação ao servidor: {erro}</T> : null}
          {atleta !== null && sobreposto === 'manha' ? <Manha atleta={atleta} voltar={fechar} /> : null}
          {atleta !== null && sobreposto === 'ftp' ? <FTP atleta={atleta} voltar={fechar} /> : null}
          {atleta !== null && !sobreposto ? (
            <View style={{ flex: 1 }} key={`${sep}-${versao}`}>
              {sep === 'hoje' ? <Hoje atleta={atleta} abrirManha={() => setSobreposto('manha')} /> : null}
              {sep === 'semana' ? <Semana atleta={atleta} /> : null}
              {sep === 'progresso' ? <Progresso atleta={atleta} /> : null}
              {sep === 'perfil' ? <Perfil atleta={atleta} abrirFTP={() => setSobreposto('ftp')} /> : null}
            </View>
          ) : null}
        </View>
        {!sobreposto ? (
          <SafeAreaView edges={['bottom']} style={{ backgroundColor: cor.superficie, borderTopWidth: 1, borderTopColor: cor.neutro }}>
            <View accessibilityRole="tablist" style={{ flexDirection: 'row', height: 66 }}>
              {SEPARADORES.map(([id, rot, ic]) => {
                const ativo = id === sep;
                return (
                  <Pressable key={id} accessibilityRole="tab" accessibilityState={{ selected: ativo }} onPress={() => setSep(id)}
                    style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 3 }}>
                    <View style={{ width: 44, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: ativo ? cor.lima : 'transparent' }}>
                      <Icone nome={ic} cor={ativo ? cor.tinta : cor.tinta2} tamanho={20} espessura={ativo ? 2.2 : 2} />
                    </View>
                    <T estilo={{ fontSize: 11, fontFamily: ativo ? letra.negrito : letra.semi, color: ativo ? cor.tinta : cor.tinta2 }}>{rot}</T>
                  </Pressable>
                );
              })}
            </View>
          </SafeAreaView>
        ) : null}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}
