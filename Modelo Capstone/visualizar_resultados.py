"""
Script para visualizar los resultados de la optimización
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración general de matplotlib
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.style.use('seaborn-v0_8-darkgrid')

def grafico_generacion_anual():
    """
    Gráfico de generación anual por central
    """
    df = pd.read_csv('resultados/energia_total.csv')
    
    # Filtrar solo centrales con generación > 0
    df_generadoras = df[df['Energia_Total_MWh'] > 0].sort_values('Energia_Total_MWh', ascending=True)
    
    # Convertir a GWh
    df_generadoras['Energia_GWh'] = df_generadoras['Energia_Total_MWh'] / 1000
    
    # Nombres de centrales
    nombres_centrales = {
        1: 'El Toro',
        2: 'Abanico',
        3: 'Antuco',
        8: 'Rucue',
        9: 'Quilleco',
        13: 'Laja 1',
        15: 'El Diuto'
    }
    
    df_generadoras['Nombre'] = df_generadoras['Central'].map(nombres_centrales)
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_generadoras)))
    bars = ax.barh(df_generadoras['Nombre'], df_generadoras['Energia_GWh'], color=colors)
    
    # Agregar valores en las barras
    for i, (bar, valor) in enumerate(zip(bars, df_generadoras['Energia_GWh'])):
        ax.text(valor + 200, bar.get_y() + bar.get_height()/2, 
                f'{valor:,.0f} GWh', 
                va='center', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Energía Generada (GWh)', fontsize=13, fontweight='bold')
    ax.set_title('Generación Anual por Central Hidroeléctrica\nCuenca del Laja', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    
    # Agregar línea de total
    total = df_generadoras['Energia_GWh'].sum()
    ax.text(0.98, 0.02, f'Total: {total:,.0f} GWh', 
            transform=ax.transAxes,
            fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            ha='right')
    
    plt.tight_layout()
    plt.savefig('resultados/grafico_generacion_anual.png', dpi=300, bbox_inches='tight')
    print("✓ Gráfico de generación anual guardado: resultados/grafico_generacion_anual.png")
    plt.close()


def grafico_riego_demandantes():
    """
    Gráfico de riego por demandante a lo largo de las semanas
    """
    df = pd.read_csv('resultados/riego.csv')
    
    # Nombres de demandantes
    nombres_demandantes = {
        1: 'Primeros Regantes',
        2: 'Segundos Regantes',
        3: 'Saltos del Laja'
    }
    
    # Crear 3 subgráficos (uno por demandante)
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    
    for i, d in enumerate([1, 2, 3]):
        ax = axes[i]
        df_d = df[df['Demanda'] == d]
        
        # Agrupar por semana (sumando todos los canales)
        demanda_semanal = df_d.groupby('Semana')['Demanda_m3s'].sum()
        provisto_semanal = df_d.groupby('Semana')['Provisto_m3s'].sum()
        deficit_semanal = df_d.groupby('Semana')['Deficit_m3s'].sum()
        
        semanas = demanda_semanal.index
        
        # Graficar
        ax.plot(semanas, demanda_semanal, 'o-', label='Demanda', 
                color='royalblue', linewidth=2, markersize=4)
        ax.plot(semanas, provisto_semanal, 's-', label='Provisto', 
                color='green', linewidth=2, markersize=4)
        
        # Marcar déficits
        semanas_deficit = deficit_semanal[deficit_semanal > 0].index
        if len(semanas_deficit) > 0:
            ax.scatter(semanas_deficit, 
                      provisto_semanal[semanas_deficit],
                      color='red', s=100, zorder=5, 
                      label=f'Déficit ({len(semanas_deficit)} semanas)', 
                      marker='x', linewidths=3)
        
        ax.set_ylabel('Caudal (m³/s)', fontsize=11, fontweight='bold')
        ax.set_title(f'{nombres_demandantes[d]}', fontsize=13, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 49)
        
        # Estadísticas
        total_deficit = deficit_semanal.sum()
        incumplimientos = len(semanas_deficit)
        cumplimiento = (48 - incumplimientos) / 48 * 100
        
        stats_text = f'Cumplimiento: {cumplimiento:.1f}%\nDéficit total: {total_deficit:.1f} m³/s'
        ax.text(0.02, 0.98, stats_text,
                transform=ax.transAxes, fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    axes[2].set_xlabel('Semana Hidrológica', fontsize=12, fontweight='bold')
    fig.suptitle('Cumplimiento de Compromisos de Riego\nCuenca del Laja', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig('resultados/grafico_riego_demandantes.png', dpi=300, bbox_inches='tight')
    print("✓ Gráfico de riego por demandante guardado: resultados/grafico_riego_demandantes.png")
    plt.close()


def grafico_volumen_lago():
    """
    Gráfico de evolución del volumen del lago
    """
    df = pd.read_csv('resultados/volumenes_lago.csv')
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Graficar volumen
    ax.plot(df['Semana'], df['Volumen_hm3'], 'o-', 
            color='steelblue', linewidth=2.5, markersize=6,
            label='Volumen del Lago')
    
    # Líneas de referencia
    ax.axhline(y=5000, color='green', linestyle='--', linewidth=2, 
               alpha=0.7, label='V inicial (30 Nov): 5,000 hm³')
    ax.axhline(y=5582, color='red', linestyle='--', linewidth=2, 
               alpha=0.7, label='V máximo: 5,582 hm³')
    
    # Rellenar área bajo la curva
    ax.fill_between(df['Semana'], 0, df['Volumen_hm3'], alpha=0.3, color='skyblue')
    
    # Marcar semana 33 (1 Dic - después del 30 Nov)
    ax.axvline(x=33, color='orange', linestyle=':', linewidth=2, 
               alpha=0.7, label='Semana 33 (1 Dic)')
    
    ax.set_xlabel('Semana Hidrológica', fontsize=13, fontweight='bold')
    ax.set_ylabel('Volumen (hm³)', fontsize=13, fontweight='bold')
    ax.set_title('Evolución del Volumen del Embalse Laja\n48 Semanas Hidrológicas', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 49)
    
    # Estadísticas
    vol_min = df['Volumen_hm3'].min()
    vol_max = df['Volumen_hm3'].max()
    vol_prom = df['Volumen_hm3'].mean()
    semana_min = df.loc[df['Volumen_hm3'].idxmin(), 'Semana']
    semana_max = df.loc[df['Volumen_hm3'].idxmax(), 'Semana']
    
    stats_text = f'Mínimo: {vol_min:,.0f} hm³ (sem {semana_min:.0f})\n'
    stats_text += f'Máximo: {vol_max:,.0f} hm³ (sem {semana_max:.0f})\n'
    stats_text += f'Promedio: {vol_prom:,.0f} hm³'
    
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes, fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig('resultados/grafico_volumen_lago.png', dpi=300, bbox_inches='tight')
    print("✓ Gráfico de volumen del lago guardado: resultados/grafico_volumen_lago.png")
    plt.close()


def grafico_generacion_semanal():
    """
    Gráfico adicional: Generación semanal total
    """
    df = pd.read_csv('resultados/generacion.csv')
    
    # Agrupar por semana
    gen_semanal = df.groupby('Semana')['Caudal_m3s'].sum()
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    ax.bar(gen_semanal.index, gen_semanal.values, color='teal', alpha=0.7, edgecolor='black')
    
    ax.set_xlabel('Semana Hidrológica', fontsize=13, fontweight='bold')
    ax.set_ylabel('Caudal Total de Generación (m³/s)', fontsize=13, fontweight='bold')
    ax.set_title('Caudal Total de Generación por Semana\nTodas las Centrales', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    ax.set_xlim(0, 49)
    
    # Promedio
    promedio = gen_semanal.mean()
    ax.axhline(y=promedio, color='red', linestyle='--', linewidth=2, 
               label=f'Promedio: {promedio:.1f} m³/s')
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    plt.savefig('resultados/grafico_generacion_semanal.png', dpi=300, bbox_inches='tight')
    print("✓ Gráfico de generación semanal guardado: resultados/grafico_generacion_semanal.png")
    plt.close()


def crear_todos_graficos():
    """
    Crear todos los gráficos
    """
    print("\n" + "="*60)
    print("GENERANDO GRÁFICOS DE RESULTADOS")
    print("="*60 + "\n")
    
    try:
        print("1. Generando gráfico de generación anual...")
        grafico_generacion_anual()
        
        print("\n2. Generando gráfico de riego por demandantes...")
        grafico_riego_demandantes()
        
        print("\n3. Generando gráfico de volumen del lago...")
        grafico_volumen_lago()
        
        print("\n4. Generando gráfico de generación semanal (bonus)...")
        grafico_generacion_semanal()
        
        print("\n" + "="*60)
        print("✓ TODOS LOS GRÁFICOS GENERADOS EXITOSAMENTE")
        print("="*60)
        print("\nArchivos generados en carpeta 'resultados/':")
        print("  1. grafico_generacion_anual.png")
        print("  2. grafico_riego_demandantes.png")
        print("  3. grafico_volumen_lago.png")
        print("  4. grafico_generacion_semanal.png")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error al generar gráficos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    crear_todos_graficos()
