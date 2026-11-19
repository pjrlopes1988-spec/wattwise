/** Tokens do estilo aprovado (protótipo: grafite + verde-lima "watt"). Um só sítio para cores e letras. */
export const cor = {
  fundo: '#F3F4F6', superficie: '#FFFFFF', tinta: '#0E1116', tinta2: '#4B5563', tinta3: '#374151',
  linha: '#EEF0F3', neutro: '#E5E7EB',
  heroi: '#0E1116', heroiTexto: '#FFFFFF', heroiSuave: '#D1D6DD', heroiMuted: '#A7B0BD', heroiLinha: '#262B33',
  lima: '#CCFF33',
  ok: '#15803D', okFundo: '#ECFDF3', okTexto: '#14532D',
  aviso: '#FBBF24', avisoFundo: '#FEF3C7', avisoTexto: '#78350F',
  perigo: '#B91C1C', perigoFundo: '#FEE2E2', perigoTexto: '#7F1D1D',
};

/** Z1…Z7 — as mesmas cores em toda a app (spec 8.4). */
export const coresZonas = ['#6B7280', '#3B82F6', '#22C55E', '#FBBF24', '#F97316', '#EF4444', '#A855F7'];
const LIMITES = [55, 75, 90, 105, 120, 150];
export function zonaDe(pct: number): number {
  let z = 0;
  while (z < 6 && pct > LIMITES[z]) z++;
  return z;
}

export const letra = {
  titulo: 'InterTight_800ExtraBold', tituloBold: 'InterTight_700Bold',
  corpo: 'Inter_400Regular', medio: 'Inter_500Medium', semi: 'Inter_600SemiBold', negrito: 'Inter_700Bold',
};

export const sombra = {
  shadowColor: '#101828', shadowOpacity: 0.08, shadowRadius: 4, shadowOffset: { width: 0, height: 1 }, elevation: 1,
};

export const raio = { cartao: 20, heroi: 24, botao: 16 };
