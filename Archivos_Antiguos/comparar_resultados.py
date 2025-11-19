"""
Script para comparar resultados entre Caso Base (LP) y Modelo MIP 5 temporadas
"""
import pandas as pd

print("\n" + "="*70)
print(" "*15 + "COMPARACIÓN DE RESULTADOS")
print(" "*10 + "Caso Base (LP) vs Modelo MIP 5 Temporadas")
print("="*70 + "\n")

# Cargar datos
df_base = pd.read_csv('Caso Base/resultados_caso_base/energia_total.csv')
df_mip = pd.read_csv('resultados/energia_total.csv')

# Calcular totales
energia_base = df_base['Energia_GWh'].sum()
energia_mip = df_mip['Energia_GWh'].sum()
diferencia = energia_mip - energia_base
porcentaje = (diferencia / energia_base) * 100

print("📊 ENERGÍA TOTAL GENERADA:")
print(f"  Caso Base (LP):     {energia_base:>10,.2f} GWh")
print(f"  Modelo MIP:         {energia_mip:>10,.2f} GWh")
print(f"  Diferencia:         {diferencia:>10,.2f} GWh ({porcentaje:+.2f}%)")
print()

# Top 5 centrales por modelo
print("⚡ TOP 5 CENTRALES - CASO BASE (LP):")
top_base = df_base.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False).head(5)
for i, (central, energia) in enumerate(top_base.items(), 1):
    pct = (energia / energia_base) * 100
    print(f"  {i}. Central {int(central):2d}:  {energia:>8,.2f} GWh ({pct:>5.1f}%)")

print()
print("⚡ TOP 5 CENTRALES - MODELO MIP:")
top_mip = df_mip.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False).head(5)
for i, (central, energia) in enumerate(top_mip.items(), 1):
    pct = (energia / energia_mip) * 100
    print(f"  {i}. Central {int(central):2d}:  {energia:>8,.2f} GWh ({pct:>5.1f}%)")

print()

# Comparación por temporada
print("📅 ENERGÍA POR TEMPORADA:")
print(f"{'Temporada':<12} {'Caso Base':>12} {'Modelo MIP':>12} {'Diferencia':>12} {'%':>8}")
print("-" * 62)
for t in range(1, 6):
    base_t = df_base[df_base['Temporada'] == t]['Energia_GWh'].sum()
    mip_t = df_mip[df_mip['Temporada'] == t]['Energia_GWh'].sum()
    diff_t = mip_t - base_t
    pct_t = (diff_t / base_t) * 100 if base_t > 0 else 0
    print(f"Temp {t:<7} {base_t:>12,.2f} {mip_t:>12,.2f} {diff_t:>12,.2f} {pct_t:>7.2f}%")

print()

# Resumen de características del modelo
print("🔧 CARACTERÍSTICAS DEL MODELO:")
print(f"{'':20} {'Caso Base (LP)':>20} {'Modelo MIP':>20}")
print("-" * 62)
print(f"{'Tipo':<20} {'LP (Lineal)':>20} {'MILP (Entero Mixto)':>20}")
print(f"{'Variables totales':<20} {'15,215':>20} {'40,403':>20}")
print(f"{'Vars. binarias':<20} {'0':>20} {'22,548':>20}")
print(f"{'Restricciones':<20} {'12,335':>20} {'53,345':>20}")
print(f"{'Tiempo ejecución':<20} {'~0.06 seg':>20} {'~minutos':>20}")

print()

# Cargar datos de riego
try:
    riego_base = pd.read_csv('Caso Base/resultados_caso_base/riego.csv')
    riego_mip = pd.read_csv('resultados/riego.csv')
    
    deficits_base = (riego_base['Deficit_hm3'] > 0.01).sum()
    deficits_mip = (riego_mip['Deficit_hm3'] > 0.01).sum()
    
    print("💧 CUMPLIMIENTO DE RIEGO:")
    print(f"  Caso Base (LP):  {deficits_base} déficits detectados")
    print(f"  Modelo MIP:      {deficits_mip} déficits detectados")
    print()
except:
    print("⚠️  No se pudieron cargar datos de riego para comparación\n")

# Cargar datos de volumen
try:
    vol_base = pd.read_csv('Caso Base/resultados_caso_base/volumenes_lago.csv')
    vol_mip = pd.read_csv('resultados/volumenes_lago.csv')
    
    print("🌊 VOLUMEN DEL LAGO:")
    print(f"{'':20} {'Caso Base (LP)':>20} {'Modelo MIP':>20}")
    print("-" * 62)
    print(f"{'Vol. inicial (hm³)':<20} {vol_base['V_hm3'].iloc[0]:>20,.2f} {vol_mip['V_hm3'].iloc[0]:>20,.2f}")
    print(f"{'Vol. final (hm³)':<20} {vol_base['V_hm3'].iloc[-1]:>20,.2f} {vol_mip['V_hm3'].iloc[-1]:>20,.2f}")
    print(f"{'Vol. promedio (hm³)':<20} {vol_base['V_hm3'].mean():>20,.2f} {vol_mip['V_hm3'].mean():>20,.2f}")
    print(f"{'Vol. máximo (hm³)':<20} {vol_base['V_hm3'].max():>20,.2f} {vol_mip['V_hm3'].max():>20,.2f}")
    print(f"{'Vol. mínimo (hm³)':<20} {vol_base['V_hm3'].min():>20,.2f} {vol_mip['V_hm3'].min():>20,.2f}")
except:
    print("⚠️  No se pudieron cargar datos de volumen para comparación")

print()
print("="*70)
print()
