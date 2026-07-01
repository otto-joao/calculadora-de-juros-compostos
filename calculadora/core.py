from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


MAX_MESES = 1200


@dataclass
class Fase:
    meses: int | None
    aporte: float
    nome: str

    @staticmethod
    def gerar_nome(indice: int) -> str:
        nomes = [
            "Construcao", "Aceleracao", "Consolidacao", "Maturidade",
            "Expansao", "Otimizacao", "Maximizacao", "Fase 8",
            "Fase 9", "Fase 10",
        ]
        return nomes[indice] if indice < len(nomes) else f"Fase {indice + 1}"


class SimulationStrategy(ABC):
    nome: str

    @abstractmethod
    def calcular(self, saldo: float, aporte: float, taxa: float) -> tuple[float, float]:
        pass


class AporteDepois(SimulationStrategy):
    nome = "Juros primeiro, depois aporte"

    def calcular(self, saldo, aporte, taxa):
        rendimento = saldo * taxa
        saldo_novo = saldo * (1 + taxa) + aporte
        return saldo_novo, rendimento


class AporteAntes(SimulationStrategy):
    nome = "Aporte primeiro, depois juros"

    def calcular(self, saldo, aporte, taxa):
        saldo_anterior = saldo
        saldo_novo = (saldo + aporte) * (1 + taxa)
        rendimento = saldo_novo - saldo_anterior - aporte
        return saldo_novo, rendimento


ESTRATEGIAS: dict[str, SimulationStrategy] = {
    "aporte_depois": AporteDepois(),
    "aporte_antes": AporteAntes(),
}


@dataclass
class ResultadoSimulacao:
    saldo_final: float
    total_investido: float
    total_juros: float
    meses_total: int
    anos: int
    meses_resto: int
    df: pd.DataFrame | None
    marcos: dict
    atingiu_meta: bool
    alvo: float = 0.0
    erro: str | None = None
    ultimo_aporte: float = 0.0
    ultima_taxa: float = 0.0


def validar_parametros(taxa_mensal: float, alvo: float, fases: list[Fase]) -> list[str]:
    erros: list[str] = []
    if not fases:
        erros.append("Defina pelo menos uma fase de aporte.")
        return erros
    if taxa_mensal < 0:
        erros.append("A taxa de juros nao pode ser negativa.")
    if taxa_mensal == 0:
        erros.append("Com taxa zero nao ha rendimento. A meta so sera atingida com aportes.")
    if alvo <= 0:
        erros.append("A meta deve ser um valor positivo.")
    fases_infinitas = [f for f in fases if f.meses is None]
    if len(fases_infinitas) > 1:
        erros.append("Apenas a ultima fase pode ter duracao indefinida.")
    if all(f.meses is not None and f.meses == 0 for f in fases) and not fases_infinitas:
        erros.append("Todas as fases tem duracao zero. Defina meses ou marque 'Ate a meta'.")
    if not any(f.aporte > 0 for f in fases if f.meses is None) and \
       not any(f.aporte > 0 and f.meses is not None and f.meses > 0 for f in fases) and \
       not any(f.aporte > 0 for f in fases):
        pass
    return erros


def projetar_crescimento(taxa_mensal: float, aporte_mensal: float, anos: int = 30) -> float:
    saldo = 0.0
    for _ in range(anos * 12):
        saldo = saldo * (1 + taxa_mensal) + aporte_mensal
    return saldo


def sugerir_aporte(taxa_mensal: float, alvo: float, prazo_anos: int = 30) -> float:
    n = prazo_anos * 12
    if taxa_mensal <= 0:
        return alvo / n if n > 0 else float("inf")
    return alvo * taxa_mensal / ((1 + taxa_mensal) ** n - 1)


def simular(
    taxa_mensal: float,
    alvo: float,
    fases: list[Fase],
    estrategia: SimulationStrategy | None = None,
    saldo_inicial: float = 0,
    mes_inicial: int = 0,
    max_meses: int = MAX_MESES,
) -> ResultadoSimulacao:
    if estrategia is None:
        estrategia = AporteDepois()

    erros = validar_parametros(taxa_mensal, alvo, fases)
    if erros:
        return ResultadoSimulacao(
            saldo_final=saldo_inicial,
            total_investido=saldo_inicial,
            total_juros=0,
            meses_total=mes_inicial,
            anos=mes_inicial // 12,
            meses_resto=mes_inicial % 12,
            df=None,
            marcos={},
            atingiu_meta=False,
            alvo=alvo,
            erro="; ".join(erros),
        )

    saldo = float(saldo_inicial)
    total_investido = float(saldo_inicial)
    aportes_acum = float(saldo_inicial)
    meses_total = mes_inicial
    registros: list[dict] = []
    marcos: dict[int, dict] = {}
    atingiu_meta = saldo >= alvo

    if atingiu_meta:
        for pct in [0.25, 0.50, 0.75, 1.00]:
            marcos[pct] = {
                "mes": meses_total,
                "ano": round(meses_total / 12, 2),
                "saldo": round(saldo, 2),
                "pct": pct * 100,
            }

    def processar_mes(aporte_valor: float, nome: str):
        nonlocal saldo, total_investido, aportes_acum, meses_total, atingiu_meta
        saldo, rendimento = estrategia.calcular(saldo, aporte_valor, taxa_mensal)
        total_investido += aporte_valor
        aportes_acum += aporte_valor
        meses_total += 1

        if not atingiu_meta:
            for pct in [0.25, 0.50, 0.75, 1.00]:
                if pct not in marcos and saldo >= alvo * pct:
                    marcos[pct] = {
                        "mes": meses_total,
                        "ano": round(meses_total / 12, 2),
                        "saldo": round(saldo, 2),
                        "pct": pct * 100,
                    }
            if saldo >= alvo:
                atingiu_meta = True

        registros.append({
            "Mes": meses_total,
            "Ano": round(meses_total / 12, 2),
            "Fase": nome,
            "Aporte": aporte_valor,
            "Rendimento": round(rendimento, 2),
            "Saldo": round(saldo, 2),
            "Aportes_Acum": round(aportes_acum, 2),
            "%Meta": round(saldo / alvo * 100, 2),
        })

    for fase in fases:
        if meses_total >= max_meses:
            break
        if fase.meses is None:
            while saldo < alvo and meses_total < max_meses:
                processar_mes(fase.aporte, fase.nome)
        else:
            for _ in range(int(fase.meses)):
                if meses_total >= max_meses or atingiu_meta:
                    break
                processar_mes(fase.aporte, fase.nome)

    df = pd.DataFrame(registros) if registros else None

    if not atingiu_meta and meses_total >= max_meses:
        erro = (
            f"Meta de R$ {alvo:,.2f} nao foi atingida em {max_meses} meses "
            f"({max_meses // 12} anos). Tente aumentar o aporte ou a taxa."
        )
    else:
        erro = None

    return ResultadoSimulacao(
        saldo_final=round(saldo, 2),
        total_investido=round(total_investido, 2),
        total_juros=round(saldo - total_investido, 2),
        meses_total=meses_total,
        anos=meses_total // 12,
        meses_resto=meses_total % 12,
        df=df,
        marcos=marcos,
        atingiu_meta=atingiu_meta,
        alvo=alvo,
        erro=erro,
        ultimo_aporte=fases[-1].aporte if fases else 0,
        ultima_taxa=taxa_mensal,
    )


def continuar_de(
    taxa_mensal: float,
    alvo: float,
    fases: list[Fase],
    mes_atual: int,
    saldo_atual: float,
    estrategia: SimulationStrategy | None = None,
) -> ResultadoSimulacao:
    meses_acum = 0
    fases_restantes: list[Fase] = []

    for fase in fases:
        if fase.meses is None:
            if meses_acum <= mes_atual:
                fases_restantes.append(Fase(None, fase.aporte, fase.nome))
            break
        inicio_fase = meses_acum
        fim_fase = meses_acum + fase.meses
        if fim_fase > mes_atual:
            restantes = fim_fase - mes_atual
            if restantes > 0:
                fases_restantes.append(Fase(int(restantes), fase.aporte, fase.nome))
        meses_acum += fase.meses

    if not fases_restantes:
        ultima = fases[-1]
        fases_restantes = [Fase(None, ultima.aporte, ultima.nome)]

    return simular(
        taxa_mensal,
        alvo,
        fases_restantes,
        estrategia=estrategia,
        saldo_inicial=saldo_atual,
        mes_inicial=mes_atual,
    )
