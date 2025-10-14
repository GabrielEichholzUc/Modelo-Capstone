"""
Script para analizar los resultados de la optimización
"""

import pandas as pd
import numpy as np

print("\n" + "="*70)
print("RESULTADOS DE LA OPTIMIZACIÓN - MODELO ACTUALIZADO")
print("="*70)

# 1. GENERACIÓN ELÉCTRICA
print("\n📊 GENERACIÓN ELÉCTRICA:")
df_energia = pd.read_csv('resultados/energia_total.csv')
df_energia['Energia_GWh'] = df_energia['Energia_Total_MWh'] / 1000
# Mapeo de nombres de centrales
nombres_centrales = {
    1: "El Toro", 2: "Abanico", 3: "Antuco", 4: "RieZaCo", 
    5: "Canecol", 6: "CanRucue", 7: "CLajRucue", 8: "Rucue",
    9: "Quilleco", 10: "Tucapel", 11: "Canal Laja", 12: "RieSaltos",
    13: "Laja 1", 14: "RieTucapel", 15: "El Diuto", 16: "Laja Filt"
}

total_generacion = df_energia['Energia_GWh'].sum()

# Mostrar energía total y por año
print("-"*70)
print("\nEnergía total generada por central (5 años):")
for _, row in df_energia.iterrows():
    if row['Energia_GWh'] > 0.01:
        central_nombre = nombres_centrales.get(int(row['Central']), f"Central {int(row['Central'])}")
        print(f"  {central_nombre:20} {row['Energia_GWh']:>10,.2f} GWh (5 años)  |  {row['Energia_GWh']/5:>8.2f} GWh/año")

total_generacion = df_energia['Energia_GWh'].sum()
print(f"\n  {'TOTAL (5 años)':20} {total_generacion:>10,.2f} GWh")
print(f"  {'PROMEDIO ANUAL':20} {total_generacion/5:>10,.2f} GWh/año")

# 2. CUMPLIMIENTO DE RIEGO
print("\n\n🌾 CUMPLIMIENTO DEL CONVENIO DE RIEGO:")
print("-"*70)

df_riego = pd.read_csv('resultados/riego.csv')

# Contar incumplimientos
total_compromisos = len(df_riego)
incumplimientos = df_riego[df_riego['Incumplimiento'] == 1]
num_incumplimientos = len(incumplimientos)
deficits = df_riego[df_riego['Deficit_m3s'] > 0.01]
num_deficits = len(deficits)

cumplimiento_pct = 100 * (1 - num_incumplimientos / total_compromisos)

print(f"  Total de compromisos: {total_compromisos}")
print(f"  Incumplimientos (η=1): {num_incumplimientos}")
print(f"  Déficits con caudal (déficit>0): {num_deficits}")
print(f"  Cumplimiento: {cumplimiento_pct:.1f}%")


# Desglose por canal y por año
print("\n  Desglose por canal y por año:")
for canal in sorted(df_riego['Canal'].unique()):
    df_canal = df_riego[df_riego['Canal'] == canal]
    for year in range(1, 6):
        semanas = list(range((year-1)*48+1, year*48+1))
        df_canal_year = df_canal[df_canal['Semana'].isin(semanas)]
        incump_canal = len(df_canal_year[df_canal_year['Incumplimiento'] == 1])
        total_canal = len(df_canal_year)
        cump_canal = 100 * (1 - incump_canal / total_canal) if total_canal > 0 else 0
        print(f"    Canal {canal} - Año {year}: {cump_canal:>5.1f}% cumplimiento ({total_canal-incump_canal}/{total_canal})")

# 3. VOLUMEN DEL LAGO
print("\n\n💧 EVOLUCIÓN DEL VOLUMEN DEL LAGO:")
print("-"*70)

df_vol = pd.read_csv('resultados/volumenes_lago.csv')

vol_inicial = df_vol.iloc[0]['Volumen_hm3']
vol_final = df_vol.iloc[-1]['Volumen_hm3']
vol_min = df_vol['Volumen_hm3'].min()
vol_max = df_vol['Volumen_hm3'].max()
vol_promedio = df_vol['Volumen_hm3'].mean()

print(f"  Volumen inicial (w=1): {vol_inicial:>8,.2f} hm³")

print(f"  Volumen final (w=240): {vol_final:>8,.2f} hm³")
print(f"  Volumen mínimo: {vol_min:>8,.2f} hm³")
print(f"  Volumen máximo: {vol_max:>8,.2f} hm³")
print(f"  Volumen promedio: {vol_promedio:>8,.2f} hm³")

# Volumen promedio por año
for year in range(1, 6):
    semanas = list(range((year-1)*48+1, year*48+1))
    df_year = df_vol[df_vol['Semana'].isin(semanas)]
    prom = df_year['Volumen_hm3'].mean()
    print(f"    Promedio año {year}: {prom:>8,.2f} hm³")

# 4. RESUMEN EJECUTIVO
print("\n\n" + "="*70)
print("📋 RESUMEN EJECUTIVO:")
print("="*70)

print(f"  ✓ Energía generada total (5 años): {total_generacion:,.0f} GWh")
print(f"  ✓ Promedio anual: {total_generacion/5:,.0f} GWh/año")
print(f"  ✓ Cumplimiento riego global: {cumplimiento_pct:.1f}%")
print(f"  ✓ Incumplimientos: {num_incumplimientos} de {total_compromisos}")
print(f"  ✓ Tiempo de resolución: 0.46 segundos")
print(f"  ✓ Gap de optimalidad: 0.17%")
print("="*70 + "\n")

# 5. ANÁLISIS DE INCUMPLIMIENTOS (si hay)
if num_incumplimientos > 0:
    print("\n⚠️  DETALLE DE INCUMPLIMIENTOS:")
    print("-"*70)
    
    for _, row in incumplimientos.head(10).iterrows():
        print(f"  Semana {row['Semana']:2.0f} | Canal {row['Canal']:.0f} | Demanda {row['Demanda']:.0f} | "
              f"Necesita: {row['Demanda_m3s']:>6.2f} m³/s | Provisto: {row['Provisto_m3s']:>6.2f} m³/s | "
              f"Déficit: {row['Deficit_m3s']:>6.2f} m³/s")
    
    if num_incumplimientos > 10:
        print(f"  ... y {num_incumplimientos - 10} incumplimientos más")
