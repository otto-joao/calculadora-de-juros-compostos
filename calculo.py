taxa_mensal = 0.01  # exemplo: 1% ao mês
alvo = 1_000_000

print("-" * 70)
print(f"{'Fase':<30} {'Período':<15} {'Aporte':<15} {'Saldo':<15}")
print("-" * 70)

saldo = 0
meses = 0
for fase_nome, aporte_nome, meses_nome in [
    ("Anos 1-2", "R$ 300/mês", 24),
    ("Anos 3-4", "R$ 500/mês", 24),
    ("Anos 5-6", "R$ 700/mês", 24),
]:
    for _ in range(meses_nome):
        saldo = saldo * (1 + taxa_mensal) + {"R$ 300/mês": 300, "R$ 500/mês": 500, "R$ 700/mês": 700}[aporte_nome]
    meses += meses_nome
    print(f"{fase_nome:<30} {f'{meses} meses':<15} {aporte_nome:<15} R$ {saldo:>8,.2f}")

# Fase 4
n = 0
while saldo < alvo:
    saldo = saldo * (1 + taxa_mensal) + 1000
    n += 1
meses += n
print("-" * 70)
print(f"{'Anos 7+ (até 1M)':<30} {f'{n} meses':<15} {'R$ 1.000/mês':<15} R$ {saldo:>8,.2f}")
print("-" * 70)

anos = meses // 12
meses_resto = meses % 12
print(f"\nTOTAL: {anos} anos e {meses_resto} meses")
