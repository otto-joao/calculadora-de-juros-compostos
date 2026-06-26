import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

st.set_page_config(page_title="Calculadora de Juros Compostos", layout="wide")
st.title("Calculadora de Juros Compostos")
st.markdown("Dashboard interativo para simular investimentos progressivos ate R$ 1 milhao.")

# --- Sidebar com parametros ---
st.sidebar.header("Parametros da Simulacao")

taxa_pct = st.sidebar.slider("Taxa mensal (%)", 0.10, 2.50, 0.83, 0.01)
taxa_aa = ((1 + taxa_pct / 100) ** 12 - 1) * 100
st.sidebar.caption(f"{taxa_pct:.2f}% a.m. = {taxa_aa:.2f}% a.a.")

alvo = st.sidebar.number_input("Meta (R$)", 1_000, 100_000_000, 1_000_000, 10_000)

st.sidebar.markdown("---")
st.sidebar.subheader("Aportes por Fase")

col1, col2 = st.sidebar.columns(2)
with col1:
    a1 = st.number_input("Fase 1 (R$/mes)", 0, 10000, 300, 50)
    a2 = st.number_input("Fase 2 (R$/mes)", 0, 10000, 500, 50)
    a3 = st.number_input("Fase 3 (R$/mes)", 0, 10000, 700, 50)
    a4 = st.number_input("Fase 4 (R$/mes)", 0, 10000, 1000, 50)
with col2:
    m1 = st.number_input("Duracao F1 (meses)", 3, 120, 24, 3)
    m2 = st.number_input("Duracao F2 (meses)", 3, 120, 24, 3)
    m3 = st.number_input("Duracao F3 (meses)", 3, 120, 24, 3)

st.sidebar.markdown("---")
st.sidebar.subheader("Opcoes Avancadas")

estrategia = st.sidebar.selectbox(
    "Estrategia de juros",
    ["Juros primeiro, depois aporte", "Aporte primeiro, depois juros"]
)
est = "aporte_depois" if "Juros primeiro" in estrategia else "aporte_antes"

mes_ini = st.sidebar.number_input("Mes inicial", 0, 400, 0, 1)
saldo_ini = st.sidebar.number_input("Saldo inicial (R$)", 0, 1_000_000, 0, 100)

# --- Funcao de simulacao ---
def simular(taxa_mensal, alvo, fases, mes_inicial=0, saldo_inicial=0, estrategia="aporte_depois"):
    saldo = float(saldo_inicial)
    total_investido = float(saldo_inicial)
    aportes_acum = float(saldo_inicial)
    meses_total = 0
    registros = []
    marcos = {}

    for meses_qtd, aporte_valor, nome in fases:
        if meses_qtd is None:
            while saldo < alvo:
                saldo_anterior = saldo
                if estrategia == "aporte_depois":
                    rendimento = saldo * taxa_mensal
                    saldo = saldo * (1 + taxa_mensal) + aporte_valor
                else:
                    saldo = (saldo + aporte_valor) * (1 + taxa_mensal)
                    rendimento = saldo - saldo_anterior - aporte_valor
                total_investido += aporte_valor
                aportes_acum += aporte_valor
                meses_total += 1

                for pct in [0.25, 0.50, 0.75, 1.00]:
                    if pct not in marcos and saldo >= alvo * pct:
                        marcos[pct] = {"mes": meses_total, "ano": round(meses_total/12, 2),
                                       "saldo": round(saldo, 2), "pct": pct*100}

                registros.append(dict(Mes=meses_total, Ano=round(meses_total/12, 2),
                    Fase=nome, Aporte=aporte_valor, Rendimento=round(rendimento, 2),
                    Saldo=round(saldo, 2), Aportes_Acum=round(aportes_acum, 2),
                    PctMeta=round(saldo/alvo*100, 2)))
        else:
            for _ in range(int(meses_qtd)):
                saldo_anterior = saldo
                if estrategia == "aporte_depois":
                    rendimento = saldo * taxa_mensal
                    saldo = saldo * (1 + taxa_mensal) + aporte_valor
                else:
                    saldo = (saldo + aporte_valor) * (1 + taxa_mensal)
                    rendimento = saldo - saldo_anterior - aporte_valor
                total_investido += aporte_valor
                aportes_acum += aporte_valor
                meses_total += 1

                for pct in [0.25, 0.50, 0.75, 1.00]:
                    if pct not in marcos and saldo >= alvo * pct:
                        marcos[pct] = {"mes": meses_total, "ano": round(meses_total/12, 2),
                                       "saldo": round(saldo, 2), "pct": pct*100}

                registros.append(dict(Mes=meses_total, Ano=round(meses_total/12, 2),
                    Fase=nome, Aporte=aporte_valor, Rendimento=round(rendimento, 2),
                    Saldo=round(saldo, 2), Aportes_Acum=round(aportes_acum, 2),
                    PctMeta=round(saldo/alvo*100, 2)))

    df = pd.DataFrame(registros)
    return {"saldo_final": round(saldo, 2), "total_investido": round(total_investido, 2),
            "total_juros": round(saldo - total_investido, 2), "meses_total": meses_total,
            "anos": meses_total // 12, "meses_resto": meses_total % 12, "df": df, "marcos": marcos}

def continuar_de(taxa_mensal, alvo, fases, mes_atual, saldo_atual, estrategia="aporte_depois"):
    meses_acum = 0
    fases_restantes = []
    for meses_qtd, aporte_valor, nome in fases:
        if meses_qtd is None:
            if meses_acum <= mes_atual:
                fases_restantes.append((None, aporte_valor, nome))
            break
        fim_fase = meses_acum + meses_qtd
        if fim_fase > mes_atual:
            restantes = fim_fase - mes_atual
            if restantes > 0:
                fases_restantes.append((restantes, aporte_valor, nome))
        meses_acum += meses_qtd
    if not fases_restantes:
        fases_restantes = [(None, fases[-1][1], fases[-1][2])]
    return simular(taxa_mensal, alvo, fases_restantes,
                   mes_inicial=mes_atual, saldo_inicial=saldo_atual, estrategia=estrategia)

# --- Executar simulacao ---
taxa = taxa_pct / 100
fases = [(m1, a1, f"R$ {a1}/mes"), (m2, a2, f"R$ {a2}/mes"),
         (m3, a3, f"R$ {a3}/mes"), (None, a4, f"R$ {a4}/mes")]

if mes_ini > 0 and saldo_ini > 0:
    res = continuar_de(taxa, alvo, fases, mes_ini, saldo_ini, est)
else:
    res = simular(taxa, alvo, fases, estrategia=est)

df = res["df"]
marcos = res["marcos"]
sf, ti, tj = res["saldo_final"], res["total_investido"], res["total_juros"]
anos, mr = res["anos"], res["meses_resto"]

if len(df) == 0:
    st.error("Nao foi possivel atingir a meta com esses parametros.")
    st.stop()

# --- METRICAS ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Saldo Final", f"R$ {sf:,.2f}")
col2.metric("Tempo Total", f"{anos}a {mr}m")
col3.metric("Total Investido", f"R$ {ti:,.2f}")
col4.metric("Total em Juros", f"R$ {tj:,.2f}")
col5.metric("Juros %", f"{tj/sf*100:.1f}%")

# --- GRAFICO 1: EVOLUCAO ---
st.subheader("Evolucao do Patrimonio")
fig, ax = plt.subplots(figsize=(14, 6))
anos_eixo = df["Ano"].values
ax.plot(anos_eixo, df["Saldo"].values, label="Saldo acumulado", linewidth=2, color="#2196F3")
ax.plot(anos_eixo, df["Aportes_Acum"].values, label="Total aportado",
        linewidth=1.5, color="#4CAF50", linestyle="--")
ax.fill_between(anos_eixo, df["Aportes_Acum"].values, df["Saldo"].values,
                alpha=0.15, color="#2196F3", label="Juros compostos")
ax.axhline(y=alvo, color="#FF9800", linestyle="--", alpha=0.7, label=f"Meta: R$ {alvo:,.0f}")
for a in [m1/12, (m1+m2)/12, (m1+m2+m3)/12]:
    if a < anos_eixo[-1]:
        ax.axvline(x=a, color="gray", linestyle=":", alpha=0.5)
        ax.text(a, ax.get_ylim()[1]*0.95, f"{a:.0f}a", ha="center", fontsize=9, color="gray")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k"))
ax.set_xlabel("Anos"); ax.set_ylabel("Valor")
ax.legend(loc="upper left"); ax.grid(axis="y", alpha=0.3)
st.pyplot(fig)
plt.close()

# --- GRAFICO 2: COMPOSICAO ---
st.subheader("Composicao do Valor Final")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
cores = ["#4CAF50", "#2196F3"]
ax1.pie([ti, tj], labels=["Total investido", "Rendimentos (juros)"],
        autopct="%1.1f%%", startangle=90, colors=cores, explode=(0, 0.05))
ax1.set_title("Composicao do Montante Final")
barras = ax2.bar(["Total investido", "Rendimentos (juros)"], [ti, tj], color=cores, width=0.5)
for barra, valor in zip(barras, [ti, tj]):
    ax2.text(barra.get_x()+barra.get_width()/2, barra.get_height()+10000,
             f"R$ {valor:,.2f}", ha="center", fontsize=11, fontweight="bold")
ax2.set_ylabel("Valor (R$)")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k"))
ax2.set_title("Total Investido vs Rendimentos")
st.pyplot(fig)
plt.close()

# --- GRAFICO 3: INFLACAO ---
st.subheader("Impacto da Inflacao — Valor Real vs Nominal")
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(anos_eixo, df["Saldo"].values, label="Valor nominal", linewidth=2, color="#2196F3")
for taxa_inf in [0.03, 0.05, 0.08]:
    inf_mensal = (1 + taxa_inf) ** (1/12) - 1
    saldo_real = df["Saldo"].values / ((1 + inf_mensal) ** df["Mes"].values)
    ax.plot(anos_eixo, saldo_real, label=f"Valor real ({taxa_inf*100:.0f}% a.a.)",
            linewidth=1.5, linestyle="--", alpha=0.7)
ax.axhline(y=alvo, color="#FF9800", linestyle="--", alpha=0.5)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:,.0f}k"))
ax.set_xlabel("Anos"); ax.set_ylabel("Valor")
ax.legend(loc="upper left"); ax.grid(axis="y", alpha=0.3)
st.pyplot(fig)
plt.close()

# --- COMPARACAO DE CENARIOS ---
st.subheader("Comparacao de Cenarios")
cenarios = [
    ("Cenario atual", taxa, fases, est),
    ("Otimista (+0.3% a.m.)", taxa + 0.003, fases, est),
    ("Pessimista (-0.3% a.m.)", max(0.001, taxa - 0.003), fases, est),
    ("Aporte 20% maior", taxa,
     [(m1, int(a1*1.2), f"R$ {int(a1*1.2)}/mes"),
      (m2, int(a2*1.2), f"R$ {int(a2*1.2)}/mes"),
      (m3, int(a3*1.2), f"R$ {int(a3*1.2)}/mes"),
      (None, int(a4*1.2), f"R$ {int(a4*1.2)}/mes")], est),
]
dados_cen = []
for nome_cen, t_cen, f_cen, e_cen in cenarios:
    if mes_ini > 0 and saldo_ini > 0:
        r = continuar_de(t_cen, alvo, f_cen, mes_ini, saldo_ini, e_cen)
    else:
        r = simular(t_cen, alvo, f_cen, estrategia=e_cen)
    dados_cen.append(dict(Cenario=nome_cen, Tempo=f'{r["anos"]}a {r["meses_resto"]}m',
        **{k: f"R$ {r[k]:,.2f}" for k in ["saldo_final", "total_investido", "total_juros"]},
        Juros_pct=f'{r["total_juros"]/r["saldo_final"]*100:.1f}%'))
st.dataframe(pd.DataFrame(dados_cen), use_container_width=True, hide_index=True)

# --- HEATMAP ---
st.subheader("Mapa de Calor — Sensibilidade (Taxa vs Aporte)")
st.caption("Tempo em anos para atingir a meta variando taxa mensal e aporte unico (fixo).")
taxas_h = np.arange(0.003, 0.020, 0.001)
aportes_h = np.arange(200, 3000, 200)
matrix = np.full((len(aportes_h), len(taxas_h)), np.nan)
for i, ap_h in enumerate(aportes_h):
    for j, tx_h in enumerate(taxas_h):
        r_h = simular(tx_h, alvo, [(None, ap_h, "Unico")], estrategia=est)
        if r_h["meses_total"] > 0 and r_h["meses_total"] <= 1200:
            matrix[i, j] = r_h["meses_total"] / 12

fig, ax = plt.subplots(figsize=(14, 7))
cmap = plt.cm.viridis; cmap.set_bad(color="gray", alpha=0.3)
im = ax.imshow(matrix, aspect="auto", origin="lower", cmap=cmap, interpolation="nearest")
ax.set_xticks(range(len(taxas_h)))
ax.set_xticklabels([f"{t*100:.1f}%" for t in taxas_h], rotation=45, ha="right")
ax.set_yticks(range(len(aportes_h)))
ax.set_yticklabels([f"R$ {a}" for a in aportes_h])
ax.set_xlabel("Taxa mensal"); ax.set_ylabel("Aporte mensal (R$)")
ax.set_title("Anos para atingir a meta")
cbar = plt.colorbar(im, ax=ax, fraction=0.046); cbar.set_label("Anos")
for i in range(len(aportes_h)):
    for j in range(len(taxas_h)):
        v = matrix[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                    fontsize=7, color="white" if v > 15 else "black", fontweight="bold")
st.pyplot(fig)
plt.close()

# --- MARCOS ---
st.subheader("Marcos da Meta")
if marcos:
    dados_marco = []
    for pct in [0.25, 0.50, 0.75, 1.00]:
        if pct in marcos:
            m = marcos[pct]
            dados_marco.append(dict(Marco=f'{m["pct"]:.0f}%', Mes=m["mes"],
                                    Ano=f'{m["ano"]:.1f}', Saldo=f'R$ {m["saldo"]:,.2f}'))
    st.dataframe(pd.DataFrame(dados_marco), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum marco atingido.")

# --- TABELA MES A MES ---
st.subheader("Planilha Mes a Mes")
with st.expander("Clique para expandir a tabela completa"):
    df_display = df[["Mes", "Ano", "Fase", "Aporte", "Rendimento", "Saldo", "PctMeta"]].copy()
    df_display.columns = ["Mes", "Ano", "Fase", "Aporte (R$)", "Rendimento (R$)",
                          "Saldo (R$)", "% da Meta"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- EXPORT ---
st.subheader("Exportar Dados")
csv = df.to_csv(index=False, decimal=",", sep=";")
st.download_button("Download CSV", csv, "simulacao_mes_a_mes.csv", "text/csv")
