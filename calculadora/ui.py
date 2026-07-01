from __future__ import annotations

import ipywidgets as widgets
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from IPython.display import clear_output, display

from calculadora.core import (
    ESTRATEGIAS,
    Fase,
    ResultadoSimulacao,
    continuar_de,
    projetar_crescimento,
    simular,
    sugerir_aporte,
    validar_parametros,
)

ultimo_df: pd.DataFrame | None = None

# =============================================================================
# Widgets de fases dinamicas
# =============================================================================


class FaseRow(widgets.HBox):
    def __init__(self, index: int, fase: Fase | None = None, on_remove=None):
        self._index = index
        self._on_remove = on_remove

        if fase:
            aporte_val = fase.aporte
            meses_val = fase.meses if fase.meses is not None else 12
            indefinido = fase.meses is None
        else:
            aporte_val = 300.0
            meses_val = 12
            indefinido = False

        self.aporte_input = widgets.FloatText(
            value=aporte_val,
            min=0,
            description="Aporte R$:",
            style={"description_width": "80px"},
            layout=widgets.Layout(width="170px"),
        )
        self.meses_input = widgets.IntText(
            value=meses_val,
            min=0,
            description="Meses:",
            style={"description_width": "55px"},
            layout=widgets.Layout(width="130px"),
        )
        self.indefinido_cb = widgets.Checkbox(
            value=indefinido,
            description="Ate a meta",
            layout=widgets.Layout(width="110px"),
            indent=False,
        )
        self.indefinido_cb.observe(self._toggle_meses, names="value")

        self._nome_label = widgets.HTML(
            f"<b>{Fase.gerar_nome(index)}</b>",
            layout=widgets.Layout(width="120px"),
        )
        self.remove_btn = widgets.Button(
            description="\u2715",
            layout=widgets.Layout(width="32px"),
            button_style="danger",
        )
        self.remove_btn.on_click(self._on_remove_clicked)

        children = [self._nome_label, self.aporte_input, self.meses_input, self.indefinido_cb]
        if on_remove:
            children.append(self.remove_btn)

        super().__init__(children)

        self._toggle_meses({"new": indefinido})

    def _toggle_meses(self, change):
        if change["new"]:
            self.meses_input.layout.display = "none"
        else:
            self.meses_input.layout.display = None

    def _on_remove_clicked(self, _):
        if self._on_remove:
            self._on_remove(self)

    def atualizar_indice(self, novo_indice: int):
        self._index = novo_indice
        self._nome_label.value = f"<b>{Fase.gerar_nome(novo_indice)}</b>"

    def to_fase(self) -> Fase:
        if self.indefinido_cb.value:
            meses = None
        else:
            meses = self.meses_input.value if self.meses_input.value > 0 else None
        return Fase(meses=meses, aporte=self.aporte_input.value, nome=Fase.gerar_nome(self._index))


class FasesWidget(widgets.VBox):
    def __init__(self, fases_iniciais: list[Fase] | None = None, **kwargs):
        self._rows: list[FaseRow] = []
        self._container = widgets.VBox([])

        self._add_btn = widgets.Button(
            description="+ Adicionar Fase",
            layout=widgets.Layout(width="180px"),
            button_style="success",
        )
        self._add_btn.on_click(self._add_row)

        super().__init__([self._container, self._add_btn], **kwargs)

        if fases_iniciais:
            for f in fases_iniciais:
                self._add_row_from_fase(f)
        else:
            self._add_row()
            self._add_row()
            self._add_row()
            self._add_row()

    def _add_row_from_fase(self, fase: Fase):
        row = FaseRow(len(self._rows), fase=fase, on_remove=self._remove_row)
        self._rows.append(row)
        self._refresh()

    def _add_row(self, _=None):
        row = FaseRow(len(self._rows), on_remove=self._remove_row)
        self._rows.append(row)
        self._refresh()

    def _remove_row(self, row: FaseRow):
        if len(self._rows) <= 1:
            return
        self._rows.remove(row)
        for i, r in enumerate(self._rows):
            r.atualizar_indice(i)
        self._refresh()

    def _refresh(self):
        self._container.children = tuple(self._rows)

    @property
    def fases(self) -> list[Fase]:
        return [row.to_fase() for row in self._rows]


# =============================================================================
# Funcao principal de atualizacao / display
# =============================================================================


def _mostrar_erros(erros: list[str]):
    html = '<div style="background:#fff0f0;padding:12px;border-radius:6px;border:1px solid #fcc;font-family:monospace">'
    html += "<h4 style='color:#c33;margin:0 0 8px 0'>Corrija os seguintes erros:</h4>"
    for e in erros:
        html += f"<p style='margin:2px 0'>&#9888; {e}</p>"
    html += "</div>"
    display(widgets.HTML(html))


def _mostrar_feedback_meta_nao_atingida(res: ResultadoSimulacao):
    html = (
        '<div style="background:#fff8e1;padding:15px;border-radius:8px;border:1px solid #ffe082;'
        'font-family:monospace;margin-bottom:15px">'
    )
    html += f"<h4 style='color:#e65100;margin:0 0 10px 0'>Meta de R$ {res.alvo:,.2f} nao atingida em {res.meses_total} meses ({res.anos}a {res.meses_resto}m)</h4>"
    html += f"<p><b>Saldo final:</b> R$ {res.saldo_final:,.2f} ({res.saldo_final / res.alvo * 100:.1f}% da meta)</p>"

    html += "<p><b>Projecao com aporte atual (ultima fase):</b></p>"
    html += "<ul>"
    for anos in [10, 20, 30]:
        proj = projetar_crescimento(res.ultima_taxa, res.ultimo_aporte, anos)
        html += f"<li>Em {anos} anos: R$ {proj:,.2f}</li>"
    html += "</ul>"

    aporte_necessario = sugerir_aporte(res.ultima_taxa, res.alvo)
    html += f"<p><b>Para atingir R$ {res.alvo:,.2f} em 30 anos:</b> aporte de <b>R$ {aporte_necessario:,.2f}/mes</b></p>"
    html += "</div>"
    display(widgets.HTML(html))


def _mostrar_resumo_executivo(res: ResultadoSimulacao):
    sf = res.saldo_final
    ti = res.total_investido
    tj = res.total_juros
    juros_pct = tj / sf * 100 if sf > 0 else 0
    invest_pct = 100 - juros_pct
    display(widgets.HTML(f"""
    <div style="background:#f0f8ff;padding:15px;border-radius:8px;border:1px solid #bcd;
                font-family:monospace;margin-bottom:20px">
      <h3 style="margin:0 0 10px 0;color:#1565C0">Resumo Executivo</h3>
      <table>
        <tr><td><b>Saldo final:</b></td><td style="padding-left:15px;color:#2e7d32">
            <b>R$ {sf:,.2f}</b></td></tr>
        <tr><td><b>Tempo total:</b></td><td style="padding-left:15px">
            {res.anos} anos e {res.meses_resto} meses ({res.meses_total} meses)</td></tr>
        <tr><td><b>Total investido:</b></td><td style="padding-left:15px">
            R$ {ti:,.2f}</td></tr>
        <tr><td><b>Total em juros:</b></td><td style="padding-left:15px;color:#1565C0">
            R$ {tj:,.2f}</td></tr>
      </table>
      <div style="margin-top:8px;display:flex;height:22px;border-radius:4px;overflow:hidden;font-size:11px;font-weight:bold">
        <div style="width:{invest_pct:.1f}%;background:#4CAF50;display:flex;align-items:center;justify-content:center;color:white">
          {invest_pct:.0f}% aportes
        </div>
        <div style="width:{juros_pct:.1f}%;background:#2196F3;display:flex;align-items:center;justify-content:center;color:white">
          {juros_pct:.0f}% juros
        </div>
      </div>
    </div>
    """))


def _plot_evolucao(df: pd.DataFrame, alvo: float, fases: list[Fase]):
    display(widgets.HTML("<h3>Evolucao do Patrimonio</h3>"))
    fig, ax = plt.subplots(figsize=(14, 6))
    anos_eixo = df["Ano"].values

    ax.plot(anos_eixo, df["Saldo"].values, label="Saldo acumulado",
            linewidth=2, color="#2196F3")
    ax.plot(anos_eixo, df["Aportes_Acum"].values,
            label="Total aportado", linewidth=1.5, color="#4CAF50", linestyle="--")
    ax.fill_between(anos_eixo, df["Aportes_Acum"].values, df["Saldo"].values,
                    alpha=0.15, color="#2196F3", label="Juros compostos")
    ax.axhline(y=alvo, color="#FF9800", linestyle="--", alpha=0.7,
               label=f"Meta: R$ {alvo:,.0f}")

    acum = 0
    for f in fases:
        if f.meses is None:
            break
        acum += f.meses
        ano = acum / 12
        if ano < anos_eixo[-1]:
            ax.axvline(x=ano, color="gray", linestyle=":", alpha=0.5)
            ax.text(ano, ax.get_ylim()[1] * 0.95, f"{ano:.0f}a",
                    ha="center", fontsize=9, color="gray")

    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k" if x >= 1000 else f"R$ {x:,.0f}"))
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor")
    ax.set_title("Evolucao do Patrimonio ao Longo do Tempo")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def _plot_composicao(ti: float, tj: float):
    display(widgets.HTML("<h3>Composicao do Valor Final</h3>"))
    labels = ["Total investido", "Rendimentos (juros)"]
    valores = [ti, tj]
    cores = ["#4CAF50", "#2196F3"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.pie(valores, labels=labels, autopct="%1.1f%%", startangle=90,
            colors=cores, explode=(0, 0.05))
    ax1.set_title("Composicao do Montante Final")

    barras = ax2.bar(labels, valores, color=cores, width=0.5)
    offset = max(valores) * 0.02 if max(valores) > 0 else 100
    for barra, valor in zip(barras, valores):
        ax2.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + offset,
                 f"R$ {valor:,.2f}", ha="center", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Valor (R$)")
    ax2.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k" if x >= 1000 else f"R$ {x:,.0f}"))
    ax2.set_title("Total Investido vs Rendimentos")
    plt.tight_layout()
    plt.show()


def _plot_inflacao(df: pd.DataFrame, alvo: float):
    display(widgets.HTML("<h3>Inflacao \u2014 Valor Real vs Nominal</h3>"))
    fig, ax = plt.subplots(figsize=(14, 6))
    anos_eixo = df["Ano"].values

    ax.plot(anos_eixo, df["Saldo"].values, label="Valor nominal",
            linewidth=2, color="#2196F3")

    for taxa_inf in [0.003, 0.005, 0.007]:
        inf_mensal = (1 + taxa_inf) ** (1 / 12) - 1
        saldo_real = df["Saldo"].values / ((1 + inf_mensal) ** df["Mes"].values)
        nome = f"Valor real ({taxa_inf * 100:.1f}% a.a.)"
        ax.plot(anos_eixo, saldo_real, label=nome, linewidth=1.5, linestyle="--",
                alpha=0.7)

    ax.axhline(y=alvo, color="#FF9800", linestyle="--", alpha=0.5,
               label=f"Meta: R$ {alvo:,.0f}")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k" if x >= 1000 else f"R$ {x:,.0f}"))
    ax.set_xlabel("Anos")
    ax.set_ylabel("Valor")
    ax.set_title("Impacto da Inflacao no Poder de Compra")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def _plot_heatmap(alvo: float, estrategia_nome: str, fases_usuario: list[Fase] | None = None):
    display(widgets.HTML("<h3>Mapa de Calor \u2014 Sensibilidade (Taxa vs Aporte)</h3>"))
    display(widgets.HTML(
        "<p>Tempo em <b>anos</b> para atingir a meta variando taxa mensal "
        "e aporte unico (aporte fixo, sem fases).</p>"))

    aportes_usuario = [f.aporte for f in (fases_usuario or []) if f.aporte > 0]
    aporte_ref = max(aportes_usuario) if aportes_usuario else 1000

    aporte_min = max(50, int(aporte_ref * 0.2 / 100) * 100)
    aporte_max = max(aporte_min + 500, int(aporte_ref * 2.0 / 100) * 100)
    passo = max(100, (aporte_max - aporte_min) // 12 // 100 * 100)
    if passo < 1:
        passo = 100

    taxas_h = np.arange(0.003, 0.020, 0.001)
    aportes_h = np.arange(aporte_min, aporte_max + 1, passo)
    matrix = np.full((len(aportes_h), len(taxas_h)), np.nan)

    for i, ap_h in enumerate(aportes_h):
        for j, tx_h in enumerate(taxas_h):
            r_h = simular(tx_h, alvo, [Fase(None, ap_h, "Unico")],
                          estrategia=ESTRATEGIAS.get(estrategia_nome))
            if r_h.meses_total > 0 and r_h.meses_total <= 1200:
                matrix[i, j] = r_h.meses_total / 12

    fig, ax = plt.subplots(figsize=(14, 7))
    cmap = plt.cm.viridis
    cmap.set_bad(color="gray", alpha=0.3)
    im = ax.imshow(matrix, aspect="auto", origin="lower", cmap=cmap,
                   interpolation="nearest")

    ax.set_xticks(range(len(taxas_h)))
    ax.set_xticklabels([f"{t * 100:.1f}%" for t in taxas_h], rotation=45, ha="right")
    ax.set_yticks(range(len(aportes_h)))
    ax.set_yticklabels([f"R$ {a}" for a in aportes_h])
    ax.set_xlabel("Taxa mensal")
    ax.set_ylabel("Aporte mensal (R$)")
    ax.set_title(f"Anos para atingir R$ {alvo:,.0f}")

    cbar = plt.colorbar(im, ax=ax, fraction=0.046)
    cbar.set_label("Anos")

    for i in range(len(aportes_h)):
        for j in range(len(taxas_h)):
            v = matrix[i, j]
            if not np.isnan(v):
                color = "white" if v > 15 else "black"
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=7, color=color, fontweight="bold")

    plt.tight_layout()
    plt.show()


def _mostrar_planilha(df: pd.DataFrame, marcos: dict | None = None):
    display(widgets.HTML("<h3>Planilha Mes a Mes</h3>"))

    df_display = df[["Mes", "Ano", "Fase", "Aporte", "Rendimento", "Saldo", "%Meta"]].copy()

    if marcos:
        marco_meses = {}
        for m in marcos.values():
            marco_meses[m["mes"]] = m
        marco_col = []
        for mes in df_display["Mes"]:
            if mes in marco_meses:
                marco_col.append(f'MARCO {marco_meses[mes]["pct"]:.0f}%')
            else:
                marco_col.append("")
        df_display.insert(0, "Marco", marco_col)

    df_display.columns = (
        ["Marco", "Mes", "Ano", "Fase", "Aporte (R$)", "Rendimento (R$)", "Saldo (R$)", "% da Meta"]
        if marcos else
        ["Mes", "Ano", "Fase", "Aporte (R$)", "Rendimento (R$)", "Saldo (R$)", "% da Meta"]
    )

    with pd.option_context("display.max_rows", 60,
                           "display.float_format", "{:,.2f}".format):
        if len(df_display) <= 60:
            display(df_display)
        else:
            display(widgets.HTML("<p><b>Primeiras 30 linhas:</b></p>"))
            display(df_display.head(30))
            if marcos:
                df_marcos_linhas = df_display[df_display.iloc[:, 0] != ""]
                if len(df_marcos_linhas) > 0:
                    display(widgets.HTML("<p><b>Linhas dos marcos:</b></p>"))
                    display(df_marcos_linhas)
            display(widgets.HTML("<p><b>Ultimas 30 linhas:</b></p>"))
            display(df_display.tail(30))

    display(widgets.HTML(f"<p><b>Total de linhas:</b> {len(df)}</p>"))


def _mostrar_comparacao_cenarios(
    taxa: float,
    fases: list[Fase],
    alvo: float,
    mes_ini: int,
    saldo_ini: float,
    est_nome: str,
):
    def _sim_cenario(t, f, e):
        if mes_ini > 0 and saldo_ini > 0:
            return continuar_de(t, alvo, f, mes_ini, saldo_ini,
                                estrategia=ESTRATEGIAS.get(e))
        return simular(t, alvo, f, estrategia=ESTRATEGIAS.get(e))

    cenarios = [
        ("Atual", taxa, fases, est_nome),
        ("Otimista (+0,3% a.m.)", taxa + 0.003, fases, est_nome),
        ("Pessimista (-0,3% a.m.)", max(0.001, taxa - 0.003), fases, est_nome),
        ("Aporte +20%", taxa,
         [Fase(f.meses, f.aporte * 1.2, f.nome) for f in fases], est_nome),
    ]

    resultados = [(_sim_cenario(t, f, e), n) for n, t, f, e in cenarios]
    r_base = resultados[0][0]

    dados_cen = []
    for r, nome_cen in resultados:
        dm = r.meses_total - r_base.meses_total
        ds = r.saldo_final - r_base.saldo_final
        if dm == 0:
            dt = "—"
        else:
            da, dr = abs(dm) // 12, abs(dm) % 12
            dt = f"+{da}a{dr}m" if dm > 0 else f"-{da}a{dr}m"

        dados_cen.append({
            "Cenario": nome_cen,
            "Tempo": f'{r.anos}a{r.meses_resto}m',
            "Δ Tempo": dt,
            "Saldo": f"R$ {r.saldo_final:,.2f}",
            "Δ Saldo": "—" if dm == 0 else f"R$ {ds:+,.2f}",
        })

    df_cen = pd.DataFrame(dados_cen)
    display(widgets.HTML("<h3>Comparacao de Cenarios</h3>"))
    display(df_cen.style.hide(axis="index"))


# =============================================================================
# Funcao de atualizacao principal
# =============================================================================


def atualizar(
    taxa_pct: float,
    alvo: float,
    fases: list[Fase],
    mes_ini: int,
    saldo_ini: float,
    est_nome: str,
):
    if isinstance(est_nome, str):
        estrategia = ESTRATEGIAS.get(est_nome, ESTRATEGIAS["aporte_depois"])
    else:
        estrategia = est_nome

    erros = validar_parametros(taxa_pct / 100, alvo, fases)
    if erros:
        _mostrar_erros(erros)
        return

    taxa = taxa_pct / 100

    if mes_ini > 0 and saldo_ini > 0:
        res = continuar_de(taxa, alvo, fases, mes_ini, saldo_ini,
                           estrategia=estrategia)
    else:
        res = simular(taxa, alvo, fases, estrategia=estrategia)

    if res.erro and not res.atingiu_meta:
        _mostrar_feedback_meta_nao_atingida(res)
        if res.df is not None and len(res.df) > 0:
            _plot_evolucao(res.df, alvo, fases)
            _mostrar_planilha(res.df, res.marcos)
        return

    if res.df is None or len(res.df) == 0:
        display(widgets.HTML('<h3 style="color:red">Nenhum dado gerado na simulacao.</h3>'))
        return

    global ultimo_df
    ultimo_df = res.df

    _mostrar_resumo_executivo(res)

    fases_visiveis = [f for f in fases if f.meses is not None]
    _plot_evolucao(res.df, alvo, fases_visiveis)
    _mostrar_comparacao_cenarios(taxa, fases, alvo, mes_ini, saldo_ini, est_nome)
    _plot_inflacao(res.df, alvo)
    _plot_heatmap(alvo, est_nome, fases)
    _mostrar_planilha(res.df, res.marcos)


# =============================================================================
# Construcao da interface
# =============================================================================


def criar_interface() -> widgets.VBox:
    taxa_input = widgets.FloatText(
        value=0.83,
        description="Taxa mensal (%):",
        style={"description_width": "130px"},
        layout=widgets.Layout(width="250px"),
    )
    taxa_aa_label = widgets.Label("(10.44% a.a.)")

    alvo_input = widgets.FloatText(
        value=1_000_000,
        description="Meta (R$):",
        style={"description_width": "130px"},
        layout=widgets.Layout(width="250px"),
    )

    mes_ini = widgets.IntText(
        value=0,
        min=0,
        description="Mes inicial:",
        style={"description_width": "100px"},
        layout=widgets.Layout(width="180px"),
    )
    saldo_ini = widgets.FloatText(
        value=0,
        min=0,
        description="Saldo inicial (R$):",
        style={"description_width": "130px"},
        layout=widgets.Layout(width="220px"),
    )

    estrategia_dd = widgets.Dropdown(
        options=[(v.nome, k) for k, v in ESTRATEGIAS.items()],
        value="aporte_depois",
        description="Estrategia:",
        style={"description_width": "100px"},
        layout=widgets.Layout(width="400px"),
    )

    fases_widget = FasesWidget()

    def fmt_taxa_aa(change):
        pct = change["new"] if isinstance(change, dict) else taxa_input.value
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            pct = 0
        aa = ((1 + pct / 100) ** 12 - 1) * 100
        taxa_aa_label.value = f"({aa:.2f}% a.a.)"

    taxa_input.observe(fmt_taxa_aa, names="value")
    fmt_taxa_aa({"new": taxa_input.value})

    simular_btn = widgets.Button(
        description="\u25b6 Simular",
        layout=widgets.Layout(width="150px"),
        button_style="primary",
    )
    output = widgets.Output()

    def on_simular(_):
        with output:
            clear_output()
            fases = fases_widget.fases
            atualizar(
                taxa_pct=taxa_input.value,
                alvo=alvo_input.value,
                fases=fases,
                mes_ini=mes_ini.value,
                saldo_ini=saldo_ini.value,
                est_nome=estrategia_dd.value,
            )

    simular_btn.on_click(on_simular)

    config_box = widgets.VBox([
        widgets.HBox([taxa_input, taxa_aa_label]),
        alvo_input,
        widgets.HBox([mes_ini, saldo_ini]),
        estrategia_dd,
    ])

    interface = widgets.VBox([
        widgets.HTML("<h2>Parametros da Simulacao</h2>"),
        config_box,
        widgets.HTML("<hr><h3>Aportes por Fase</h3>"),
        widgets.HTML("<p>Defina os aportes de cada fase. Marque 'Ate a meta' para a fase que deve durar ate o objetivo ser atingido.</p>"),
        fases_widget,
        simular_btn,
        output,
    ])

    return interface
