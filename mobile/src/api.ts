/**
 * Ligação ao servidor. Os cálculos são todos feitos no servidor (spec 8.2); a app só mostra.
 * Cada leitura fica guardada no telemóvel: sem rede, a app mostra a última versão (offline).
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

export const BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ErroApi extends Error {
  constructor(public estado: number, mensagem: string) { super(mensagem); }
}

async function pedir<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const r = await fetch(BASE + caminho, {
    ...opcoes, headers: { 'Content-Type': 'application/json', ...(opcoes.headers ?? {}) },
  });
  if (!r.ok) {
    let msg = `Erro ${r.status}`;
    try { const j = await r.json(); msg = typeof j.detail === 'string' ? j.detail : msg; } catch { /* sem corpo */ }
    throw new ErroApi(r.status, msg);
  }
  return r.status === 204 ? (undefined as T) : r.json();
}

export interface ComCache<T> { dados: T; offline: boolean; guardadoEm?: string }

/** Lê do servidor e guarda; sem rede, devolve a última cópia guardada. */
export async function comCache<T>(chave: string, ler: () => Promise<T>): Promise<ComCache<T>> {
  try {
    const dados = await ler();
    await AsyncStorage.setItem('cache:' + chave, JSON.stringify({ dados, em: new Date().toISOString() })).catch(() => {});
    return { dados, offline: false };
  } catch (e) {
    if (e instanceof ErroApi) throw e;               // o servidor respondeu com erro: não é falta de rede
    const guardado = await AsyncStorage.getItem('cache:' + chave).catch(() => null);
    if (!guardado) throw e;
    const { dados, em } = JSON.parse(guardado);
    return { dados, offline: true, guardadoEm: em };
  }
}

// ------------------------------------------------------------ tipos (subconjunto das respostas)
export interface Passo { segundos: number; pct_min: number; pct_max: number; rampa: string | null; cadencia: number[] | null; alvo: string }
export interface Treino { id: string; nome: string; subtitulo: string; titulo: string; tipo: string; ambiente: 'indoor' | 'outdoor'; minutos: number; carga: number; descricao: string; passos: Passo[] }
export interface TreinoDia { data: string; papel: string; alta_intensidade: boolean; prioridade: string | null; escolhido: boolean; opcoes: Treino[] }
export interface Sinal { codigo: string; valor: unknown; limiar: unknown; forte: boolean }
export interface Hoje {
  data: string; estado: 'verde' | 'amarelo' | 'vermelho' | 'bloqueado'; explicacao: string; procurar_medico: boolean;
  sinais: Sinal[]; dados_em_falta: string[]; regras: string[]; treino_original: TreinoDia | null; treino: TreinoDia | null;
  frescura_pct: number | null; condicao: number;
}
export interface Semana { numero: number; inicio: string; fase: string; carga_alvo: number; carga_planeada: number; condicao_fim: number; notas: string[]; treinos: TreinoDia[] }
export interface Plano { inicio: string; fim: string; semanas: Semana[] }
export interface ProvaJ { nome: string; data: string; prioridade: string; duracao_h: number | null; etapas: { data: string; duracao_h: number | null; descricao: string }[] }
export interface PerfilJ {
  nome: string; peso_kg: number; nivel: string; disciplina: string; ftp: { valor: number; fonte: string } | null;
  fc_limiar: { valor: number } | null; provas: ProvaJ[]; onde_treina: string | null; ciclo: string | null;
  agressividade: number | null; ftp_modo: string; historico_ftp: { data: string; valor: number; fonte: string }[];
}
export interface AtletaJ { id: number; perfil: PerfilJ; eftp: number | null; ambientes: string[]; intensidade: number }

// ------------------------------------------------------------ rotas
export const api = {
  atleta: (id: number) => pedir<AtletaJ>(`/atletas/${id}`),
  hoje: (id: number, data?: string) => pedir<Hoje>(`/atletas/${id}/hoje${data ? `?data=${data}` : ''}`),
  plano: (id: number) => pedir<Plano>(`/atletas/${id}/plano`),
  manha: (id: number, corpo: Record<string, unknown>) => pedir(`/atletas/${id}/manha`, { method: 'POST', body: JSON.stringify(corpo) }),
  escolha: (id: number, ambiente: string, data: string) =>
    pedir(`/atletas/${id}/hoje/escolha`, { method: 'POST', body: JSON.stringify({ ambiente, data }) }),
  preferencias: (id: number, corpo: Record<string, unknown>) =>
    pedir(`/atletas/${id}/preferencias`, { method: 'PUT', body: JSON.stringify(corpo) }),
  ftp: (id: number, valor: number, confirmar = false) =>
    pedir<{ guardado: boolean; avisos: string[] }>(`/atletas/${id}/ftp`, { method: 'PUT', body: JSON.stringify({ valor, confirmar }) }),
  criar: (perfil: Record<string, unknown>) =>
    pedir<{ id: number }>(`/atletas`, { method: 'POST', body: JSON.stringify({ perfil, consentimento_dados_saude: true }) }),
  hojeComCache: (id: number, data?: string) => comCache(`hoje:${id}:${data ?? 'hoje'}`, () => api.hoje(id, data)),
  planoComCache: (id: number) => comCache(`plano:${id}`, () => api.plano(id)),
  atletaComCache: (id: number) => comCache(`atleta:${id}`, () => api.atleta(id)),
  urlExportar: (id: number, data: string, formato: string, ambiente: string) =>
    `${BASE}/atletas/${id}/treinos/${data}/exportar?formato=${formato}&ambiente=${ambiente}`,
};
