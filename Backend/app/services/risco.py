"""Avaliação de risco: monta as features, chama o modelo F6, classifica e aplica protocolos."""
import logging
import unicodedata
from typing import Optional

from app.config import (
    AVISO, CONTEXTO_PADRAO, MAPA_SENSOR_FEATURE, SINAIS_PADRAO, Settings,
)
from app.schemas import ResultadoRisco
from app.services.protocolos import PROTOCOLO_EMERGENCIA, PROTOCOLOS, avaliar_protocolos
from modelo.predict import carregar_modelo, prever_risco

log = logging.getLogger(__name__)

LARGURA_OLED = 21
COR_POR_FAIXA = {"baixo": "verde", "moderado": "amarelo", "alto": "vermelho"}
_PROTOCOLO_POR_CODIGO = {p.codigo: p for p in (*PROTOCOLOS, PROTOCOLO_EMERGENCIA)}
# Do mais ao menos urgente (usado só para ordenar as recomendações).
PRIORIDADE_PROTOCOLOS = (
    "estado_emergencia", "suporte_respiratorio", "protocolo_choque", "monitoramento_intensivo",
    "resposta_rapida", "protocolo_infeccioso", "triagem_emergencial", "unidades_temporarias",
    "plano_contingencia", "redistribuir_insumos",
)


class ModeloIndisponivel(RuntimeError):
    pass


def carregar() -> bool:
    """Carrega o modelo uma vez (cache do predict.py). Retorna False se falhar."""
    try:
        carregar_modelo()
        return True
    except Exception:
        log.exception("Falha ao carregar o modelo preditivo da F6")
        return False


def montar_features(
    sinais: dict[str, Optional[float]],
    contexto: Optional[dict[str, Optional[float]]] = None,
    usar_sinais_padrao: bool = False,
) -> tuple[dict[str, float], list[str]]:
    """Combina sinais do sensor + contexto + padrões. Devolve (features, features_padrao).

    Prioridade: sinal do sensor > contexto da requisição > valor padrão.
    `sinais` usa os nomes do sensor (bpm, temperatura, spo2) ou já os nomes das features.
    """
    features: dict[str, float] = {}
    for chave, valor in (contexto or {}).items():
        if valor is not None:
            features[chave] = float(valor)
    for chave, valor in sinais.items():
        if valor is not None:
            features[MAPA_SENSOR_FEATURE.get(chave, chave)] = float(valor)

    padroes = {**CONTEXTO_PADRAO, **(SINAIS_PADRAO if usar_sinais_padrao else {})}
    features_padrao = []
    for chave, valor in padroes.items():
        if chave not in features:
            features[chave] = float(valor)
            features_padrao.append(chave)
    return features, features_padrao


def classificar_faixa(risco: float, settings: Settings) -> str:
    if risco >= settings.limiar_alto:
        return "alto"
    if risco >= settings.limiar_moderado:
        return "moderado"
    return "baixo"


def _ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def linhas_oled(risco: float, faixa: str, features: dict[str, float], rotulos: list[str]) -> list[str]:
    """4 linhas de até 21 caracteres ASCII (largura de um display 128 px com fonte 6x8).

    O firmware MicroPython usa framebuf (fonte 8x8 = 16 colunas) e monta as próprias
    linhas em IoT/logica.py; estas servem para a UI ou displays com fonte menor.
    """
    linhas = [
        f"Risco {risco * 100:.0f}% {faixa.upper()}",
        f"FC{features['fc_media']:.0f} T{features['temperatura']:.1f} O2 {features['spo2_media']:.0f}",
        f"Protocolos: {len(rotulos)}",
        rotulos[0] if rotulos else "Sem protocolos",
    ]
    return [_ascii(linha)[:LARGURA_OLED] for linha in linhas]


def enriquecer_com_agentes(features: dict[str, float], resultado: ResultadoRisco) -> ResultadoRisco:
    """Enriquecimento local, determinístico e sem LLM, no papel dos agentes da F6.

    - Analista de Risco: gera `resumo` com a faixa, o risco e os sinais que dispararam protocolos.
    - Planejador de Protocolos: ordena `recomendacoes` por prioridade clínica (emergência e
      suporte respiratório primeiro). `protocolos_acionados` e o OLED não mudam.

    Mantém `aviso`, `features_padrao` e os demais campos, dos quais a UI depende. O código dos
    agentes LLM da F6 não está neste repositório; para integrá-los, substitua o corpo desta função.
    """
    sinais = []
    for codigo in resultado.protocolos_acionados:
        protocolo = _PROTOCOLO_POR_CODIGO.get(codigo)
        if protocolo and protocolo.feature in features:
            sinais.append(f"{protocolo.feature}={features[protocolo.feature]:g}")
    resumo = f"Risco {resultado.risco * 100:.0f}% ({resultado.faixa})."
    if sinais:
        resumo += " Sinais que acionaram protocolos: " + ", ".join(sinais) + "."
    else:
        resumo += " Nenhum protocolo acionado."

    ordem = {codigo: i for i, codigo in enumerate(PRIORIDADE_PROTOCOLOS)}
    pares = sorted(
        zip(resultado.protocolos_acionados, resultado.recomendacoes),
        key=lambda par: ordem.get(par[0], len(ordem)),
    )
    return resultado.model_copy(update={
        "resumo": resumo,
        "recomendacoes": [acao for _, acao in pares],
    })



def avaliar(features: dict[str, float], features_padrao: list[str], settings: Settings) -> ResultadoRisco:
    try:
        risco = prever_risco(features)
    except ValueError:
        raise
    except Exception as exc:  # arquivo ausente, versão incompatível do scikit-learn etc.
        log.exception("Falha ao executar o modelo preditivo da F6")
        raise ModeloIndisponivel("Modelo preditivo indisponível no servidor.") from exc

    faixa = classificar_faixa(risco, settings)
    protocolos = avaliar_protocolos(features, faixa)
    # No OLED só cabe um rótulo: o de emergência (último da lista) tem prioridade.
    rotulos_oled = [p.rotulo_oled for p in reversed(protocolos)] if faixa == "alto" else [
        p.rotulo_oled for p in protocolos
    ]
    resultado = ResultadoRisco(
        risco=round(risco, 4),
        faixa=faixa,
        led=COR_POR_FAIXA[faixa],
        oled=linhas_oled(risco, faixa, features, rotulos_oled),
        protocolos_acionados=[p.codigo for p in protocolos],
        recomendacoes=[p.acao for p in protocolos],
        features=features,
        features_padrao=features_padrao,
        aviso=AVISO,
    )
    return enriquecer_com_agentes(features, resultado)
