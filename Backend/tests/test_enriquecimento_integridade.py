"""Enriquecimento local (agentes) e verificação de integridade do modelo."""
import pytest

from app.config import get_settings
from app.services import risco as servico_risco
from modelo import predict


def _avaliar(**features):
    feats, padrao = servico_risco.montar_features(features, usar_sinais_padrao=True)
    return servico_risco.avaliar(feats, padrao, get_settings())


def test_resumo_e_prioridade_das_recomendacoes():
    r = _avaliar(spo2_media=80, fc_media=150, temperatura=39)
    assert r.resumo and "spo2_media=80" in r.resumo
    assert r.recomendacoes[0] == "Ativar estado de emergência" or "respirat" in r.recomendacoes[0]
    assert len(r.recomendacoes) == len(r.protocolos_acionados)


def test_resumo_sem_protocolos():
    r = _avaliar()
    assert r.resumo and r.aviso


def test_integridade_ok_e_adulterado(tmp_path):
    modelo = tmp_path / "m.joblib"
    modelo.write_bytes(b"conteudo")
    predict._verificar_integridade(modelo)  # sem .sha256: só avisa
    (tmp_path / "m.joblib.sha256").write_text("0" * 64)
    with pytest.raises(RuntimeError, match="Integridade"):
        predict._verificar_integridade(modelo)


def test_hash_do_modelo_versionado_confere():
    predict._verificar_integridade(predict.CAMINHO_MODELO)
