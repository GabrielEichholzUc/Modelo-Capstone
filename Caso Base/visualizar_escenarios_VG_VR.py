"""
Visualizador de Volúmenes VG/VR con Cálculos por Tramos
======================================================

Este script crea visualizaciones específicas para los volúmenes de generación (VG) 
y riego (VR) calculados usando las reglas por tramos implementadas en 
preprocesar_volumenes_uso.py.

Gráficos generados:
1. Evolución VG y VR por temporada (con límites y umbrales)
2. Comparación VG/VR calculados vs valores originales del convenio
3. Análisis de casos especiales (k=1, t≤T_TRANS, V_rini≤1370)
4. Distribución de volúmenes por tramos de V_rini
5. Impacto del límite VG ≤ 1200 hm³
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from preprocesar_volumenes_uso import (
    calcular_volumenes_iniciales_por_uso, 
    calcular_VG_VR_por_tramos,
    preprocesar_volumenes_uso_desde_parametros
)

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10

# Crear carpeta para gráficos
output_dir = 'graficos_VG_VR'
os.makedirs(output_dir, exist_ok=True)

print("="*80)
print("VISUALIZADOR DE VOLÚMENES VG/VR CON CÁLCULOS POR TRAMOS")
print("="*80)

# ============================================================
# DATOS DE EJEMPLO Y CONFIGURACIÓN
# ============================================================

# Escenarios de ejemplo para análisis
V_30Nov_escenarios = {
    'Escenario Base': {
        1: 5500,  # Temporada 1: Volumen intermedio
        2: 4000,  # Temporada 2: Volumen intermedio-alto
        3: 7000,  # Temporada 3: Volumen alto
        4: 3500,  # Temporada 4: Volumen intermedio-bajo
        5: 6300   # Temporada 5: Umbral máximo
    },
    'Escenario Seco': {
        1: 2000,  # Temporada 1: Volumen bajo
        2: 1500,  # Temporada 2: Volumen muy bajo
        3: 3000,  # Temporada 3: Volumen intermedio-bajo
        4: 800,   # Temporada 4: Volumen muy bajo
        5: 2500   # Temporada 5: Volumen bajo
    },
    'Escenario Húmedo': {
        1: 8000,  # Temporada 1: Volumen muy alto
        2: 7500,  # Temporada 2: Volumen muy alto
        3: 9000,  # Temporada 3: Volumen muy alto
        4: 6800,  # Temporada 4: Volumen alto
        5: 8500   # Temporada 5: Volumen muy alto
    }
}

# Parámetros para casos especiales
parametros_especiales = {
    'V_mixto': 10.0,      # Ajuste para el primer tramo
    'T_TRANS': 2,         # Umbral temporal de transición
    'VG_INI': 800.0,      # VG inicial para k=1
    'VR_INI': 1200.0,     # VR inicial para k=1
}

# FS simplificado
FS_ejemplo = {w: 604800 for w in range(1, 49)}  # 7 días = 604800 segundos

print(f"📊 Configuración:")
print(f"  • {len(V_30Nov_escenarios)} escenarios de análisis")
print(f"  • Carpeta de salida: {output_dir}/")
print(f"  • Parámetros especiales: V_mixto={parametros_especiales['V_mixto']}, T_TRANS={parametros_especiales['T_TRANS']}")

# ============================================================
# GRÁFICO 1: EVOLUCIÓN VG Y VR POR ESCENARIO
# ============================================================

print("\n📈 Generando Gráfico 1: Evolución VG y VR por escenario...")

fig, axes = plt.subplots(2, 2, figsize=(18, 12))
axes = axes.flatten()

colors_escenarios = ['#1f77b4', '#ff7f0e', '#2ca02c']
temporadas = [1, 2, 3, 4, 5]

# Calcular VG y VR para cada escenario
resultados_escenarios = {}
for idx, (nombre_escenario, V_valores) in enumerate(V_30Nov_escenarios.items()):
    # Calcular usando función original (convenio)
    resultado_convenio = calcular_volumenes_iniciales_por_uso(V_valores, FS_ejemplo)
    
    # Calcular usando función por tramos (nueva)
    VG_tramos = {}
    VR_tramos = {}
    
    for t in temporadas:
        V_rini_k = V_valores[t]
        V_rini_k_minus1 = V_valores.get(t-1, None) if t > 1 else None
        VG_prev = VG_tramos.get(t-1, None) if t > 1 else None
        
        vg_calc, vr_calc = calcular_VG_VR_por_tramos(
            V_rini_k=V_rini_k,
            V_rini_k_minus1=V_rini_k_minus1,
            V_mixto=parametros_especiales['V_mixto'],
            t=t,
            T_TRANS=parametros_especiales['T_TRANS'],
            k=t,
            VG_prev=VG_prev,
            VG_INI=parametros_especiales['VG_INI'] if t == 1 else None,
            VR_INI=parametros_especiales['VR_INI'] if t == 1 else None
        )
        
        # Si devuelve None (caso k=1), usar valores iniciales
        if vg_calc is None or vr_calc is None:
            if t == 1:
                vg_calc = parametros_especiales['VG_INI']
                vr_calc = parametros_especiales['VR_INI']
            else:
                # Fallback: usar cálculo del convenio
                vg_calc = resultado_convenio['VG'][t]
                vr_calc = resultado_convenio['VR'][t]
        
        VG_tramos[t] = vg_calc
        VR_tramos[t] = vr_calc
    
    resultados_escenarios[nombre_escenario] = {
        'V_30Nov': V_valores,
        'VG_convenio': resultado_convenio['VG'],
        'VR_convenio': resultado_convenio['VR'],
        'VG_tramos': VG_tramos,
        'VR_tramos': VR_tramos
    }

# Gráfico 1.1: VG por escenario
ax = axes[0]
for idx, (nombre, datos) in enumerate(resultados_escenarios.items()):
    vg_convenio = [datos['VG_convenio'][t] for t in temporadas]
    vg_tramos = [datos['VG_tramos'][t] for t in temporadas]
    
    ax.plot(temporadas, vg_convenio, '--', color=colors_escenarios[idx], 
            alpha=0.7, linewidth=2, label=f'{nombre} (Convenio)')
    ax.plot(temporadas, vg_tramos, '-', color=colors_escenarios[idx], 
            linewidth=3, marker='o', markersize=6, label=f'{nombre} (Tramos)')

ax.axhline(y=1200, color='red', linestyle='-', linewidth=2, alpha=0.8, 
           label='Límite VG = 1200 hm³')
ax.set_title('Volumen de Generación (VG) - Comparación Métodos', fontweight='bold')
ax.set_xlabel('Temporada')
ax.set_ylabel('VG (hm³)')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(temporadas)

# Gráfico 1.2: VR por escenario
ax = axes[1]
for idx, (nombre, datos) in enumerate(resultados_escenarios.items()):
    vr_convenio = [datos['VR_convenio'][t] for t in temporadas]
    vr_tramos = [datos['VR_tramos'][t] for t in temporadas]
    
    ax.plot(temporadas, vr_convenio, '--', color=colors_escenarios[idx], 
            alpha=0.7, linewidth=2, label=f'{nombre} (Convenio)')
    ax.plot(temporadas, vr_tramos, '-', color=colors_escenarios[idx], 
            linewidth=3, marker='s', markersize=6, label=f'{nombre} (Tramos)')

ax.set_title('Volumen de Riego (VR) - Comparación Métodos', fontweight='bold')
ax.set_xlabel('Temporada')
ax.set_ylabel('VR (hm³)')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(temporadas)

# Gráfico 1.3: Total extraíble (VG + VR)
ax = axes[2]
for idx, (nombre, datos) in enumerate(resultados_escenarios.items()):
    total_convenio = [datos['VG_convenio'][t] + datos['VR_convenio'][t] for t in temporadas]
    total_tramos = [datos['VG_tramos'][t] + datos['VR_tramos'][t] for t in temporadas]
    
    ax.plot(temporadas, total_convenio, '--', color=colors_escenarios[idx], 
            alpha=0.7, linewidth=2, label=f'{nombre} (Convenio)')
    ax.plot(temporadas, total_tramos, '-', color=colors_escenarios[idx], 
            linewidth=3, marker='^', markersize=6, label=f'{nombre} (Tramos)')

ax.set_title('Volumen Total Extraíble (VG + VR)', fontweight='bold')
ax.set_xlabel('Temporada')
ax.set_ylabel('Volumen Total (hm³)')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(temporadas)

# Gráfico 1.4: V_30Nov de entrada
ax = axes[3]
for idx, (nombre, datos) in enumerate(resultados_escenarios.items()):
    v_vals = [datos['V_30Nov'][t] for t in temporadas]
    ax.plot(temporadas, v_vals, '-', color=colors_escenarios[idx], 
            linewidth=3, marker='o', markersize=8, label=f'{nombre}')

# Añadir líneas de umbrales del convenio original
ax.axhline(y=3650, color='orange', linestyle='-.', linewidth=2, alpha=0.7, 
           label='V_umbral_min = 3650 hm³')
ax.axhline(y=6300, color='purple', linestyle='-.', linewidth=2, alpha=0.7, 
           label='V_umbral_max = 6300 hm³')

# Añadir líneas de los umbrales de los tramos nuevos
ax.axhline(y=1200, color='red', linestyle=':', linewidth=1.5, alpha=0.6, 
           label='Tramo 1200 hm³')
ax.axhline(y=1370, color='blue', linestyle=':', linewidth=1.5, alpha=0.6, 
           label='Tramo 1370 hm³')
ax.axhline(y=1900, color='green', linestyle=':', linewidth=1.5, alpha=0.6, 
           label='Tramo 1900 hm³')

ax.set_title('V_30Nov de Entrada - Escenarios de Análisis', fontweight='bold')
ax.set_xlabel('Temporada')
ax.set_ylabel('V_30Nov (hm³)')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xticks(temporadas)

plt.suptitle('Comparación Volúmenes VG/VR: Convenio Original vs Cálculo por Tramos', 
             fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig(f'{output_dir}/1_evolucion_VG_VR_escenarios.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/1_evolucion_VG_VR_escenarios.png")
plt.close()

# ============================================================
# GRÁFICO 2: ANÁLISIS DE TRAMOS Y CASOS ESPECIALES
# ============================================================

print("📈 Generando Gráfico 2: Análisis de tramos y casos especiales...")

# Crear rango amplio de V_rini para análisis de tramos
V_rini_range = np.linspace(0, 8000, 200)

# Calcular VG y VR para diferentes casos
casos = {
    'Normal (t>T_TRANS, V>1370)': {'t': 5, 'V_mixto': 0, 'k': 3},
    'Transición (t≤T_TRANS)': {'t': 1, 'V_mixto': 0, 'k': 2},
    'Volumen Bajo (V≤1370)': {'t': 5, 'V_mixto': 0, 'k': 3},
    'Con V_mixto=20': {'t': 5, 'V_mixto': 20, 'k': 3}
}

fig, axes = plt.subplots(2, 2, figsize=(18, 12))
axes = axes.flatten()

# Gráfico 2.1: VG por tramos
ax = axes[0]
colors_casos = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

for idx, (nombre_caso, params) in enumerate(casos.items()):
    VG_vals = []
    VR_vals = []
    
    for V in V_rini_range:
        # Determinar si aplica caso especial de volumen bajo
        if 'Volumen Bajo' in nombre_caso:
            V_test = min(V, 1370)  # Forzar V ≤ 1370 para este caso
        else:
            V_test = V
        
        vg, vr = calcular_VG_VR_por_tramos(
            V_rini_k=V_test,
            V_rini_k_minus1=None,
            V_mixto=params['V_mixto'],
            t=params['t'],
            T_TRANS=parametros_especiales['T_TRANS'],
            k=params['k'],
            VG_prev=None,
            VG_INI=parametros_especiales['VG_INI'],
            VR_INI=parametros_especiales['VR_INI']
        )
        
        # Si es k=1 y devuelve None, usar valores iniciales
        if vg is None:
            vg = parametros_especiales['VG_INI'] if params['k'] == 1 else 0
        if vr is None:
            vr = parametros_especiales['VR_INI'] if params['k'] == 1 else 0
            
        VG_vals.append(vg)
        VR_vals.append(vr)
    
    # Solo mostrar hasta donde VG no esté limitado a 1200 para ver la forma original
    V_plot = V_rini_range if 'Volumen Bajo' not in nombre_caso else V_rini_range[:np.where(V_rini_range <= 1370)[0][-1]+10]
    VG_plot = VG_vals if 'Volumen Bajo' not in nombre_caso else VG_vals[:len(V_plot)]
    
    ax.plot(V_plot, VG_plot, color=colors_casos[idx], linewidth=2.5, 
            label=nombre_caso, alpha=0.8)

# Añadir líneas verticales de los umbrales
ax.axvline(x=1200, color='red', linestyle=':', alpha=0.6, label='Umbral 1200')
ax.axvline(x=1370, color='blue', linestyle=':', alpha=0.6, label='Umbral 1370')
ax.axvline(x=1900, color='green', linestyle=':', alpha=0.6, label='Umbral 1900')
ax.axhline(y=1200, color='red', linestyle='-', alpha=0.8, label='Límite VG = 1200')

ax.set_title('VG por Tramos - Diferentes Casos', fontweight='bold')
ax.set_xlabel('V_rini (hm³)')
ax.set_ylabel('VG (hm³)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 6000)

# Gráfico 2.2: VR por tramos  
ax = axes[1]
for idx, (nombre_caso, params) in enumerate(casos.items()):
    VR_vals = []
    
    for V in V_rini_range:
        if 'Volumen Bajo' in nombre_caso:
            V_test = min(V, 1370)
        else:
            V_test = V
        
        vg, vr = calcular_VG_VR_por_tramos(
            V_rini_k=V_test,
            V_rini_k_minus1=None,
            V_mixto=params['V_mixto'],
            t=params['t'],
            T_TRANS=parametros_especiales['T_TRANS'],
            k=params['k'],
            VG_prev=None,
            VG_INI=parametros_especiales['VG_INI'],
            VR_INI=parametros_especiales['VR_INI']
        )
        
        if vr is None:
            vr = parametros_especiales['VR_INI'] if params['k'] == 1 else 0
            
        VR_vals.append(vr)
    
    V_plot = V_rini_range if 'Volumen Bajo' not in nombre_caso else V_rini_range[:np.where(V_rini_range <= 1370)[0][-1]+10]
    VR_plot = VR_vals if 'Volumen Bajo' not in nombre_caso else VR_vals[:len(V_plot)]
    
    ax.plot(V_plot, VR_plot, color=colors_casos[idx], linewidth=2.5, 
            label=nombre_caso, alpha=0.8)

ax.axvline(x=1200, color='red', linestyle=':', alpha=0.6, label='Umbral 1200')
ax.axvline(x=1370, color='blue', linestyle=':', alpha=0.6, label='Umbral 1370') 
ax.axvline(x=1900, color='green', linestyle=':', alpha=0.6, label='Umbral 1900')

ax.set_title('VR por Tramos - Diferentes Casos', fontweight='bold')
ax.set_xlabel('V_rini (hm³)')
ax.set_ylabel('VR (hm³)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 6000)

# Gráfico 2.3: Diferencias entre métodos (VG)
ax = axes[2]
V_test_range = np.linspace(3000, 8000, 100)  # Rango donde ambos métodos funcionan

# Calcular diferencias
for idx, (nombre_escenario, V_valores) in enumerate(list(V_30Nov_escenarios.items())[:2]):  # Solo 2 escenarios
    diffs_VG = []
    diffs_VR = []
    
    for V in V_test_range:
        # Método convenio (aproximado)
        if V <= 3650:
            vg_conv, vr_conv = 0, 0
        elif V <= 6300:
            aG, aR = 820/(6300-3650), 1520/(6300-3650)
            vg_conv = aG * (V - 3650)
            vr_conv = aR * (V - 3650)
        else:
            vg_conv, vr_conv = 820, 1520
        
        # Método tramos
        vg_tramos, vr_tramos = calcular_VG_VR_por_tramos(
            V_rini_k=V, V_mixto=0, t=5, T_TRANS=2, k=3
        )
        
        diffs_VG.append(vg_tramos - vg_conv)
        diffs_VR.append(vr_tramos - vr_conv)
    
    ax.plot(V_test_range, diffs_VG, color=colors_escenarios[idx], 
            linewidth=2.5, label=f'Diferencia VG', alpha=0.8)

ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
ax.set_title('Diferencia: VG(Tramos) - VG(Convenio)', fontweight='bold')
ax.set_xlabel('V_rini (hm³)')
ax.set_ylabel('Diferencia VG (hm³)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Gráfico 2.4: Impacto del límite VG ≤ 1200
ax = axes[3]
V_high_range = np.linspace(4000, 8000, 100)
VG_sin_limite = []
VG_con_limite = []

for V in V_high_range:
    # Calcular sin límite (modificar temporalmente la función)
    vg, _ = calcular_VG_VR_por_tramos(V_rini_k=V, V_mixto=0, t=5, T_TRANS=2, k=3)
    
    # VG sin límite (calculado internamente antes del min)
    if 0 <= V <= 1200:
        vg_sin_limite = 0.05 * V + 30.0
    elif 1200 <= V <= 1370:
        vg_sin_limite = 60.0 + 0.05 * (V - 1200.0)
    elif 1370 <= V <= 1900:
        vg_sin_limite = 68.5 + 0.40 * (V - 1370.0)
    elif 1900 <= V <= 5582:
        vg_sin_limite = 280.5 + 0.65 * (V - 1900.0)
    else:
        vg_sin_limite = 280.5 + 0.65 * max(0.0, (V - 1900.0))
    
    VG_sin_limite.append(vg_sin_limite)
    VG_con_limite.append(vg)  # Ya limitado a 1200

ax.plot(V_high_range, VG_sin_limite, '--', color='red', linewidth=2.5, 
        label='VG sin límite', alpha=0.8)
ax.plot(V_high_range, VG_con_limite, '-', color='blue', linewidth=2.5, 
        label='VG con límite ≤ 1200', alpha=0.8)
ax.axhline(y=1200, color='red', linestyle='-', alpha=0.8, 
           label='Límite = 1200 hm³')

ax.set_title('Impacto del Límite VG ≤ 1200 hm³', fontweight='bold')
ax.set_xlabel('V_rini (hm³)')
ax.set_ylabel('VG (hm³)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.suptitle('Análisis Detallado de Cálculos por Tramos y Casos Especiales', 
             fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig(f'{output_dir}/2_analisis_tramos_casos_especiales.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/2_analisis_tramos_casos_especiales.png")
plt.close()

# ============================================================
# GRÁFICO 3: TABLA RESUMEN DE RESULTADOS
# ============================================================

print("📈 Generando Gráfico 3: Tabla resumen de resultados...")

# Crear tabla comparativa
tabla_data = []

for nombre_escenario, datos in resultados_escenarios.items():
    for t in temporadas:
        V_30Nov = datos['V_30Nov'][t]
        VG_conv = datos['VG_convenio'][t]
        VR_conv = datos['VR_convenio'][t] 
        VG_tram = datos['VG_tramos'][t]
        VR_tram = datos['VR_tramos'][t]
        
        tabla_data.append({
            'Escenario': nombre_escenario,
            'Temporada': t,
            'V_30Nov': V_30Nov,
            'VG_Convenio': VG_conv,
            'VG_Tramos': VG_tram,
            'Diff_VG': VG_tram - VG_conv,
            'VR_Convenio': VR_conv,
            'VR_Tramos': VR_tram, 
            'Diff_VR': VR_tram - VR_conv,
            'Total_Convenio': VG_conv + VR_conv,
            'Total_Tramos': VG_tram + VR_tram,
            'Diff_Total': (VG_tram + VR_tram) - (VG_conv + VR_conv)
        })

df_tabla = pd.DataFrame(tabla_data)

# Crear gráfico de tabla
fig, ax = plt.subplots(figsize=(20, 12))
ax.axis('tight')
ax.axis('off')

# Mostrar solo algunos campos clave en la tabla visual
df_display = df_tabla[['Escenario', 'Temporada', 'V_30Nov', 'VG_Convenio', 'VG_Tramos', 
                      'Diff_VG', 'VR_Convenio', 'VR_Tramos', 'Diff_VR']].round(2)

table = ax.table(cellText=df_display.values, colLabels=df_display.columns, 
                cellLoc='center', loc='center', fontsize=9)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.5)

# Colorear filas alternadas
for i in range(len(df_display)):
    for j in range(len(df_display.columns)):
        if i % 2 == 0:
            table[(i+1, j)].set_facecolor('#f0f0f0')
        
        # Colorear diferencias
        if 'Diff' in df_display.columns[j]:
            val = df_display.iloc[i, j]
            if val > 0:
                table[(i+1, j)].set_facecolor('#d4edda')  # Verde claro
            elif val < 0:
                table[(i+1, j)].set_facecolor('#f8d7da')  # Rojo claro

plt.title('Tabla Comparativa: Volúmenes Convenio vs Tramos\n(Valores en hm³)', 
          fontsize=16, fontweight='bold', pad=20)
plt.savefig(f'{output_dir}/3_tabla_comparativa_resultados.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/3_tabla_comparativa_resultados.png")
plt.close()

# Guardar tabla en CSV
df_tabla.to_csv(f'{output_dir}/tabla_comparativa_VG_VR.csv', index=False)
print(f"  ✓ Tabla guardada: {output_dir}/tabla_comparativa_VG_VR.csv")

# ============================================================
# RESUMEN Y ESTADÍSTICAS
# ============================================================

print("\n" + "="*80)
print("📊 RESUMEN DE ANÁLISIS")
print("="*80)

print(f"\n🔸 Escenarios analizados: {len(V_30Nov_escenarios)}")
print(f"🔸 Temporadas por escenario: {len(temporadas)}")
print(f"🔸 Total de cálculos: {len(tabla_data)}")

print(f"\n📈 Estadísticas de diferencias VG (Tramos - Convenio):")
diff_vg = df_tabla['Diff_VG']
print(f"  • Media: {diff_vg.mean():.2f} hm³")
print(f"  • Desviación estándar: {diff_vg.std():.2f} hm³")
print(f"  • Mínimo: {diff_vg.min():.2f} hm³")
print(f"  • Máximo: {diff_vg.max():.2f} hm³")

print(f"\n📈 Estadísticas de diferencias VR (Tramos - Convenio):")
diff_vr = df_tabla['Diff_VR']
print(f"  • Media: {diff_vr.mean():.2f} hm³")
print(f"  • Desviación estándar: {diff_vr.std():.2f} hm³")
print(f"  • Mínimo: {diff_vr.min():.2f} hm³")
print(f"  • Máximo: {diff_vr.max():.2f} hm³")

print(f"\n📈 Casos donde VG alcanza el límite de 1200 hm³:")
casos_limite = df_tabla[df_tabla['VG_Tramos'] >= 1199.9]
print(f"  • Número de casos: {len(casos_limite)}")
if len(casos_limite) > 0:
    print(f"  • Escenarios afectados: {casos_limite['Escenario'].unique()}")

print(f"\n✅ Gráficos generados en: {output_dir}/")
print("  1. Evolución VG/VR por escenarios")
print("  2. Análisis de tramos y casos especiales") 
print("  3. Tabla comparativa de resultados")
print("  4. Archivo CSV con datos detallados")

print("\n" + "="*80)
print("🎯 ANÁLISIS COMPLETADO")
print("="*80)

# ============================================================
# FUNCIÓN PARA USO DESDE OTROS SCRIPTS
# ============================================================

def visualizar_volumenes_personalizados(V_30Nov_dict, parametros=None, output_prefix="custom"):
    """
    Función para generar visualizaciones con datos personalizados
    
    Args:
        V_30Nov_dict: dict {t: volumen} con valores por temporada
        parametros: dict opcional con parámetros especiales
        output_prefix: prefijo para nombres de archivos
    
    Returns:
        dict: Resultados calculados
    """
    if parametros is None:
        parametros = parametros_especiales.copy()
    
    # Calcular usando ambos métodos
    resultado_convenio = calcular_volumenes_iniciales_por_uso(V_30Nov_dict, FS_ejemplo)
    
    VG_tramos = {}
    VR_tramos = {}
    
    for t in sorted(V_30Nov_dict.keys()):
        V_rini_k = V_30Nov_dict[t]
        V_rini_k_minus1 = V_30Nov_dict.get(t-1, None) if t > 1 else None
        VG_prev = VG_tramos.get(t-1, None) if t > 1 else None
        
        vg_calc, vr_calc = calcular_VG_VR_por_tramos(
            V_rini_k=V_rini_k,
            V_rini_k_minus1=V_rini_k_minus1,
            V_mixto=parametros.get('V_mixto', 0),
            t=t,
            T_TRANS=parametros.get('T_TRANS', 0),
            k=t,
            VG_prev=VG_prev,
            VG_INI=parametros.get('VG_INI', None),
            VR_INI=parametros.get('VR_INI', None)
        )
        
        if vg_calc is None or vr_calc is None:
            if t == 1:
                vg_calc = parametros.get('VG_INI', resultado_convenio['VG'][t])
                vr_calc = parametros.get('VR_INI', resultado_convenio['VR'][t])
            else:
                vg_calc = resultado_convenio['VG'][t]
                vr_calc = resultado_convenio['VR'][t]
        
        VG_tramos[t] = vg_calc
        VR_tramos[t] = vr_calc
    
    return {
        'V_30Nov': V_30Nov_dict,
        'VG_convenio': resultado_convenio['VG'],
        'VR_convenio': resultado_convenio['VR'],
        'VG_tramos': VG_tramos,
        'VR_tramos': VR_tramos,
        've_0_total': {t: VG_tramos[t] + VR_tramos[t] for t in VG_tramos.keys()}
    }

if __name__ == "__main__":
    print("\n🎯 Script ejecutado como módulo principal")
    print("✅ Visualizaciones completadas exitosamente")