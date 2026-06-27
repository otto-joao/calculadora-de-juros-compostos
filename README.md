# Calculadora de Juros Compostos

Simulador interativo que mostra **quanto tempo leva para atingir R$ 1 milhão** ajustando aportes, taxas e fases.

## Passo a passo

### 1. Instalar

```bash
pip install ipywidgets matplotlib pandas numpy openpyxl
```

### 2. Abrir o notebook

```bash
jupyter notebook calculadora_investimentos.ipynb
```

### 3. Executar as células

No menu do Jupyter, clique em **Cell > Run All** (ou pressione Shift+Enter em cada célula).

### 4. Ajustar os parâmetros

Use os controles interativos que aparecem:

1. **Taxa mensal** — arraste o slider para a rentabilidade esperada
2. **Meta** — digite o valor que você quer atingir
3. **Aportes** — ajuste quanto aportar em cada fase
4. **Duração** — defina quantos meses dura cada fase
5. **(opcional) Mês e saldo inicial** — preencha se já tem investimentos

### 5. Interpretar os resultados

Role para baixo para ver na ordem:

1. **Resumo executivo** — saldo final, tempo total, juros gerados
2. **Gráfico de evolução** — curva do patrimônio ao longo dos anos
3. **Gráfico de composição** — pizza mostrando investido × rendimentos
4. **Impacto da inflação** — linhas tracejadas mostrando o valor real
5. **Comparação de cenários** — tabela com otimista, pessimista e aporte maior
6. **Heatmap** — matriz taxa × aporte com anos para atingir a meta
7. **Marcos** — quando atinge 25%, 50%, 75% e 100% da meta
8. **Planilha mês a mês** — primeiras e últimas linhas da simulação

### 6. Exportar (opcional)

Descomente as linhas na última célula para gerar CSV ou Excel.

## Layout da interface

```
┌─ PARÂMETROS ──────────────────────────────────────────────┐
│ Taxa: [═══●═══════] 0.83% (10.44% a.a.)   Meta: [ 1000000 ] │
│ Mês inicial: [0]   Saldo inicial: [0]                    │
│ Estratégia: [Juros primeiro, depois aporte ▼]             │
├─ APORTES POR FASE ────────────────────────────────────────┤
│ Fase 1: [300]  Fase 2: [500]   │  Duração F1: [24]       │
│ Fase 3: [700]  Fase 4: [1000]  │  Duração F2: [24]       │
│                                 │  Duração F3: [24]       │
├─ RESULTADOS (exemplo) ────────────────────────────────────┤
│ Saldo final: R$ 1.005.913,87   │  25 anos 3 meses         │
│ Total investido: R$ 267.000,00 │  Juros: R$ 738.913,87    │
│ Juros correspondem a 73,5% do montante final              │
├─ GRÁFICOS ────────────────────────────────────────────────┤
│ [Evolução do patrimônio] [Composição] [Impacto inflação]  │
├─ COMPARAÇÃO ──────────────────────────────────────────────┤
│ Cenário atual     │ 25a 3m  │ R$ 1.005.913,87             │
│ Otimista (+0,3%)  │ 18a 7m  │ R$ 1.000.115,07             │
│ Pessimista (-0,3%)│ 38a 1m  │ R$ 1.008.633,23             │
│ Aporte +20%       │ 21a 10m │ R$ 1.006.054,91             │
├─ HEATMAP ─────────────────────────────────────────────────┤
│ [Matriz taxa × aporte: anos para atingir a meta]          │
├─ MARCOS ──────────────────────────────────────────────────┤
│ 25% → 12,5a │ 50% → 18,8a │ 75% → 22,6a │ 100% → 25,3a  │
└───────────────────────────────────────────────────────────┘
```

## Para que serve cada controle

| Controle | O que faz |
|----------|-----------|
| **Taxa mensal** | Rentabilidade mensal esperada (0,10% a 2,50%) |
| **Meta** | Valor que você quer atingir |
| **Fase 1 a 4** | Quanto aportar por mês em cada fase |
| **Meses F1, F2, F3** | Duração de cada fase |
| **Mês / Saldo inicial** | Para simular a partir de onde você está hoje |
| **Estratégia** | "Juros primeiro" = rende sobre o saldo anterior; "Aporte primeiro" = rende sobre saldo + aporte do mês |

## Exemplo padrão (R$ 1 milhão em 25 anos)

| Fase | Duração | Aporte mensal |
|------|---------|---------------|
| 1 | 24 meses | R$ 300 |
| 2 | 24 meses | R$ 500 |
| 3 | 24 meses | R$ 700 |
| 4 | até a meta | R$ 1.000 |

**Taxa:** 0,83% a.m. (~10,44% a.a.)

## O que o notebook gera

- Resumo executivo com saldo, tempo e juros
- Gráfico de evolução (saldo × aportado × juros)
- Gráfico de composição (investido vs rendimentos)
- Gráfico com correção pela inflação
- Tabela comparativa de cenários
- Heatmap de sensibilidade (taxa × aporte)
- Marcos: quando atinge 25%, 50%, 75% e 100% da meta
- Planilha mês a mês completa
- Opção de exportar para CSV ou Excel
