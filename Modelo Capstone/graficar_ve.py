"""
Gráfico de la variable ve[u,w] - Volumen disponible por uso
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

print("\n" + "="*70)
print("GENERANDO GRÁFICO DE VOLUMEN POR USO (ve[u,w])")
print("="*70)

# Primero necesitamos extraer los valores de ve desde el modelo
# Como no se exportan por defecto, vamos a recalcularlos o leerlos del modelo

print("\nBuscando archivo con valores de ve...")

# Intentar cargar desde los resultados
try:
    # Verificar si existe archivo de volumenes por uso
    df_ve = pd.read_csv('resultados/volumenes_uso.csv')
    print("✓ Archivo volumenes_uso.csv encontrado")
except:
    print("⚠️  Archivo no encontrado. Necesitamos exportar ve desde el modelo.")
    print("    Creando script para exportar ve...")
    
    # Crear script para ejecutar el modelo y extraer ve
    script_content = """
import pandas as pd
from cargar_datos import cargar_parametros_excel
from modelo_laja import ModeloLaja

print("Cargando parámetros...")
parametros = cargar_parametros_excel()

print("Construyendo modelo...")
modelo = ModeloLaja()
modelo.cargar_parametros(parametros)
modelo.crear_variables()
modelo.crear_restricciones()
modelo.crear_funcion_objetivo()

print("Optimizando...")
modelo.model.setParam('OutputFlag', 0)  # Silenciar output
modelo.model.optimize()

if modelo.model.status == 2:
    print("Extrayendo valores de ve[u,w]...")
    
    # Extraer valores de ve
    datos_ve = []
    
    # ve_0 (inicial)
    for u in [1, 2]:
        uso_nombre = "Riego" if u == 1 else "Generación"
        datos_ve.append({
            'Uso': uso_nombre,
            'Semana': 0,
            'Volumen_hm3': modelo.ve_0[u].X
        })
    
    # Extraer ve[u,w] para cada semana
    for u in [1, 2]:
        uso_nombre = "Riego" if u == 1 else "Generación"
        for w in range(1, 241):
            datos_ve.append({
                'Uso': uso_nombre,
                'Semana': w,
                'Volumen_hm3': modelo.ve[u, w].X
            })
    
    df_ve = pd.DataFrame(datos_ve)
    df_ve.to_csv('resultados/volumenes_uso.csv', index=False)
    print("✓ Valores exportados a resultados/volumenes_uso.csv")
else:
    print("✗ Error: Modelo no optimizó correctamente")
"""
    
    with open('extraer_ve.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("    Ejecutando extracción...")
    import subprocess
    result = subprocess.run(['python', 'extraer_ve.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Extracción completada")
        df_ve = pd.read_csv('resultados/volumenes_uso.csv')
    else:
        print("✗ Error en extracción:")
        print(result.stderr)
        exit(1)

# Crear el gráfico
print("\nCreando gráfico...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Separar por uso
df_riego = df_ve[df_ve['Uso'] == 'Riego']
df_gen = df_ve[df_ve['Uso'] == 'Generación']

# Panel 1: Volumen para Riego
ax1.plot(df_riego['Semana'], df_riego['Volumen_hm3'], 
         color='#2E7D32', linewidth=2.5, marker='o', markersize=4,
         label='Volumen disponible para Riego')
ax1.fill_between(df_riego['Semana'], 0, df_riego['Volumen_hm3'], 
                  alpha=0.3, color='#66BB6A')
ax1.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax1.set_title('Volumen Disponible para Riego (ve[u=1,w])', 
              fontsize=13, fontweight='bold', pad=15)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(fontsize=10, loc='best')

# Estadísticas
vol_inicial_riego = df_riego[df_riego['Semana']==0]['Volumen_hm3'].values[0]
vol_final_riego = df_riego[df_riego['Semana']==240]['Volumen_hm3'].values[0]
vol_min_riego = df_riego['Volumen_hm3'].min()
vol_max_riego = df_riego['Volumen_hm3'].max()

stats_text = f'Inicial: {vol_inicial_riego:,.0f} hm³\nFinal: {vol_final_riego:,.0f} hm³\n'
stats_text += f'Mín: {vol_min_riego:,.0f} hm³\nMáx: {vol_max_riego:,.0f} hm³'
ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
         fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 2: Volumen para Generación
ax2.plot(df_gen['Semana'], df_gen['Volumen_hm3'], 
         color='#1565C0', linewidth=2.5, marker='s', markersize=4,
         label='Volumen disponible para Generación')
ax2.fill_between(df_gen['Semana'], 0, df_gen['Volumen_hm3'], 
                  alpha=0.3, color='#42A5F5')
ax2.set_xlabel('Semana Hidrológica', fontsize=12, fontweight='bold')
ax2.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax2.set_title('Volumen Disponible para Generación (ve[u=2,w])', 
              fontsize=13, fontweight='bold', pad=15)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(fontsize=10, loc='best')

# Estadísticas
vol_inicial_gen = df_gen[df_gen['Semana']==0]['Volumen_hm3'].values[0]
vol_final_gen = df_gen[df_gen['Semana']==240]['Volumen_hm3'].values[0]
vol_min_gen = df_gen['Volumen_hm3'].min()
vol_max_gen = df_gen['Volumen_hm3'].max()

stats_text = f'Inicial: {vol_inicial_gen:,.0f} hm³\nFinal: {vol_final_gen:,.0f} hm³\n'
stats_text += f'Mín: {vol_min_gen:,.0f} hm³\nMáx: {vol_max_gen:,.0f} hm³'
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
         fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('resultados/grafico_volumenes_uso.png', dpi=300, bbox_inches='tight')
print("✓ Gráfico guardado: resultados/grafico_volumenes_uso.png")

# Panel 3: Gráfico combinado con porcentajes
fig2, ax = plt.subplots(figsize=(14, 7))

# Calcular volumen total
df_total = df_riego.copy()
df_total['Volumen_Total'] = df_riego['Volumen_hm3'].values + df_gen['Volumen_hm3'].values
df_total['Pct_Riego'] = (df_riego['Volumen_hm3'].values / df_total['Volumen_Total'] * 100)
df_total['Pct_Gen'] = (df_gen['Volumen_hm3'].values / df_total['Volumen_Total'] * 100)

# Gráfico de áreas apiladas
ax.fill_between(df_riego['Semana'], 0, df_riego['Volumen_hm3'], 
                alpha=0.7, color='#66BB6A', label='Riego')
ax.fill_between(df_gen['Semana'], df_riego['Volumen_hm3'], 
                df_riego['Volumen_hm3'].values + df_gen['Volumen_hm3'].values,
                alpha=0.7, color='#42A5F5', label='Generación')

# Línea del total
ax.plot(df_total['Semana'], df_total['Volumen_Total'], 
        color='black', linewidth=2, linestyle='--', label='Total')

ax.set_xlabel('Semana Hidrológica', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('Distribución de Volúmenes por Uso (ve[u,w])', 
             fontsize=14, fontweight='bold', pad=15)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(fontsize=11, loc='best')

plt.tight_layout()
plt.savefig('resultados/grafico_volumenes_uso_combinado.png', dpi=300, bbox_inches='tight')
print("✓ Gráfico combinado guardado: resultados/grafico_volumenes_uso_combinado.png")

# Mostrar estadísticas
print("\n" + "="*70)
print("ESTADÍSTICAS DE VOLÚMENES POR USO")
print("="*70)

print("\n📊 RIEGO (u=1):")
print(f"  Volumen inicial (ve[1,0]): {vol_inicial_riego:>10,.2f} hm³")
print(f"  Volumen final (ve[1,240]):  {vol_final_riego:>10,.2f} hm³")
print(f"  Variación:                 {vol_final_riego - vol_inicial_riego:>10,.2f} hm³ ({(vol_final_riego/vol_inicial_riego-1)*100:+.1f}%)")
print(f"  Mínimo:                    {vol_min_riego:>10,.2f} hm³")
print(f"  Máximo:                    {vol_max_riego:>10,.2f} hm³")

print("\n⚡ GENERACIÓN (u=2):")
print(f"  Volumen inicial (ve[2,0]): {vol_inicial_gen:>10,.2f} hm³")
print(f"  Volumen final (ve[2,240]):  {vol_final_gen:>10,.2f} hm³")
print(f"  Variación:                 {vol_final_gen - vol_inicial_gen:>10,.2f} hm³ ({(vol_final_gen/vol_inicial_gen-1)*100:+.1f}%)")
print(f"  Mínimo:                    {vol_min_gen:>10,.2f} hm³")
print(f"  Máximo:                    {vol_max_gen:>10,.2f} hm³")

vol_total_inicial = vol_inicial_riego + vol_inicial_gen
vol_total_final = vol_final_riego + vol_final_gen

print(f"\n💧 TOTAL:")
print(f"  Volumen inicial:           {vol_total_inicial:>10,.2f} hm³")
print(f"  Volumen final:             {vol_total_final:>10,.2f} hm³")
print(f"  Variación total:           {vol_total_final - vol_total_inicial:>10,.2f} hm³ ({(vol_total_final/vol_total_inicial-1)*100:+.1f}%)")

print("\n" + "="*70)
print("✓ GRÁFICOS GENERADOS EXITOSAMENTE")
print("="*70)
print("\nArchivos generados:")
print("  1. resultados/grafico_volumenes_uso.png (2 paneles)")
print("  2. resultados/grafico_volumenes_uso_combinado.png (áreas apiladas)")
print("  3. resultados/volumenes_uso.csv (datos)")
print("="*70 + "\n")
