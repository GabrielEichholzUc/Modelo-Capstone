"""
Análisis del error de aproximación del modelo linealizado de filtraciones
vs. la función polinomial real del Embalse El Toro
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cargar_datos_5temporadas import cargar_parametros_excel

# ============================================================================
# FUNCIONES DEL MODELO REAL (ElToro.txt)
# ============================================================================

def filt_eltoro(cota):
    """
    Función polinomial de orden 4 para filtraciones en El Toro
    Entrada: Cota [m.s.n.m]
    Salida: Filtraciones [m³/s]
    """
    a0 = -133471.205667
    a1 = 251.668765787
    a2 = -0.112314280288
    a3 = -0.000031180464
    a4 = 0.000000022628942
    
    filt = a0 + (a1 * cota) + (a2 * cota**2) + (a3 * cota**3) + (a4 * cota**4)
    return filt


def cot_eltoro(volumen):
    """
    Función para calcular cota a partir de volumen
    Usa interpolación lineal de tabla empírica
    Entrada: Volumen [hm³]
    Salida: Cota [m.s.n.m]
    """
    # Tabla empírica Volumen -> Cota (índice i corresponde a cota 1301 + i - 2)
    datos = np.array([
        0., 48.28954, 97.47766, 147.26746, 197.35679, 248.04517,
        299.43508, 351.82341, 405.0131, 459.20122, 514.48761, 570.97736,
        628.56274, 687.35149, 747.53804, 808.92531, 871.61054, 935.59635,
        1000.88273, 1067.4697, 1135.25477, 1204.23795, 1274.32464, 1345.60945,
        1417.89268, 1491.07712, 1565.25999, 1640.4439, 1716.42655, 1793.41026,
        1871.19533, 1949.97619, 2029.56105, 2110.14171, 2191.52373, 2273.9068,
        2357.18845, 2441.47116, 2526.65244, 2612.83215, 2700.01554, 2788.19472,
        2877.37496, 2967.75593, 3059.03548, 3151.31608, 3244.69758, 3339.17471,
        3434.65552, 3531.13476, 3628.71226, 3727.4905, 3827.36962, 3928.44686,
        4030.62499, 4133.90402, 4238.58084, 4344.35855, 4451.33437, 4559.61076,
        4668.98805, 4779.66329, 4891.53927, 5004.41367, 5118.38896, 5233.46515,
        5349.83928, 5467.31431, 5585.88761, 5705.66164, 5826.53656
    ])
    
    # Interpolación lineal
    if volumen <= 0:
        cota = 1301.0
    elif volumen >= datos[-1]:
        cota = 1371.0
    else:
        # Encontrar índice donde insertar
        i = np.searchsorted(datos, volumen)
        
        # Interpolación lineal
        d1 = volumen - datos[i-1]
        d2 = datos[i] - datos[i-1]
        dc = d1 / d2
        
        cota = 1301.0 + i - 2 + dc
    
    # Limitar rango
    cota = np.clip(cota, 1301.0, 1371.0)
    
    return cota


def filtraciones_desde_volumen(volumen):
    """
    Calcula filtraciones desde volumen usando el modelo real
    Volumen [hm³] -> Cota [m.s.n.m] -> Filtraciones [m³/s]
    """
    cota = cot_eltoro(volumen)
    filt = filt_eltoro(cota)
    return filt, cota


# ============================================================================
# MODELO LINEALIZADO POR ZONAS
# ============================================================================

def filtraciones_linealizadas(volumen, v_k, f_k):
    """
    Calcula filtraciones usando el modelo linealizado por zonas progresivas
    
    Parámetros:
    - volumen: volumen del lago [hm³]
    - v_k: dict con volúmenes por zona {k: v_k}
    - f_k: dict con filtraciones por zona {k: f_k}
    
    Retorna:
    - filtracion: filtración aproximada [m³/s]
    - zona_activa: última zona k activa
    """
    K_zonas = sorted([k for k in v_k.keys() if k < max(v_k.keys())])
    
    # Iniciar desde zona 1
    filtracion = f_k[1]
    zona_activa = 1
    
    # Recorrer zonas progresivamente
    for k in K_zonas:
        v_k_val = v_k[k]
        v_k_next = v_k[k + 1]
        f_k_val = f_k[k]
        f_k_next = f_k[k + 1]
        
        if volumen > v_k_next:
            # Zona completamente activa
            filtracion += (f_k_next - f_k_val)
            zona_activa = k + 1
        elif volumen > v_k_val:
            # Zona parcialmente activa (interpolación lineal)
            delta_v = volumen - v_k_val
            delta_f_max = f_k_next - f_k_val
            delta_v_max = v_k_next - v_k_val
            
            if delta_v_max > 0:
                delta_f = (delta_v / delta_v_max) * delta_f_max
                filtracion += delta_f
            zona_activa = k
            break
        else:
            # No se alcanza esta zona
            break
    
    return filtracion, zona_activa


# ============================================================================
# ANÁLISIS DE ERROR
# ============================================================================

def analizar_error_filtraciones():
    """
    Compara el modelo linealizado contra el modelo real y calcula errores
    """
    print("\n" + "="*80)
    print("ANÁLISIS DE ERROR - MODELO DE FILTRACIONES")
    print("="*80 + "\n")
    
    # 1. Cargar parámetros del modelo linealizado
    print("Cargando parámetros del modelo linealizado...")
    parametros = cargar_parametros_excel()
    
    v_k = parametros['VC']
    f_k = parametros['FC']
    
    print(f"  Zonas cargadas: {len(v_k)}")
    print(f"  Rango volumen: {min(v_k.values()):.2f} - {max(v_k.values()):.2f} hm³")
    print(f"  Rango filtraciones: {min(f_k.values()):.2f} - {max(f_k.values()):.2f} m³/s\n")
    
    # 2. Generar rango de volúmenes para análisis
    v_min = 0
    v_max = 5900  # Cobertura completa
    volumenes = np.linspace(v_min, v_max, 1000)
    
    # 3. Calcular filtraciones con ambos modelos
    print("Calculando filtraciones con ambos modelos...")
    
    resultados = []
    for vol in volumenes:
        # Modelo real
        filt_real, cota = filtraciones_desde_volumen(vol)
        
        # Modelo linealizado
        filt_lin, zona = filtraciones_linealizadas(vol, v_k, f_k)
        
        # Error
        error_abs = filt_lin - filt_real
        error_rel = (error_abs / filt_real * 100) if filt_real != 0 else 0
        
        resultados.append({
            'Volumen_hm3': vol,
            'Cota_msnm': cota,
            'Filt_Real_m3s': filt_real,
            'Filt_Lineal_m3s': filt_lin,
            'Zona_Activa': zona,
            'Error_Abs_m3s': error_abs,
            'Error_Rel_pct': error_rel
        })
    
    df = pd.DataFrame(resultados)
    
    # 4. Estadísticas de error
    print("\n" + "="*80)
    print("ESTADÍSTICAS DE ERROR")
    print("="*80 + "\n")
    
    # Filtrar rango operativo (V_MIN a V_MAX típicamente)
    V_MIN = parametros.get('V_MIN', 0)
    V_MAX = parametros.get('V_MAX', 5826)
    
    df_operativo = df[(df['Volumen_hm3'] >= V_MIN) & (df['Volumen_hm3'] <= V_MAX)]
    
    print("RANGO COMPLETO (0 - 5900 hm³):")
    print(f"  Error absoluto máximo: {df['Error_Abs_m3s'].abs().max():.4f} m³/s")
    print(f"  Error absoluto promedio: {df['Error_Abs_m3s'].abs().mean():.4f} m³/s")
    print(f"  Error relativo máximo: {df['Error_Rel_pct'].abs().max():.4f} %")
    print(f"  Error relativo promedio: {df['Error_Rel_pct'].abs().mean():.4f} %")
    
    print(f"\nRANGO OPERATIVO ({V_MIN:.0f} - {V_MAX:.0f} hm³):")
    print(f"  Error absoluto máximo: {df_operativo['Error_Abs_m3s'].abs().max():.4f} m³/s")
    print(f"  Error absoluto promedio: {df_operativo['Error_Abs_m3s'].abs().mean():.4f} m³/s")
    print(f"  Error relativo máximo: {df_operativo['Error_Rel_pct'].abs().max():.4f} %")
    print(f"  Error relativo promedio: {df_operativo['Error_Rel_pct'].abs().mean():.4f} %")
    
    # Identificar puntos de mayor error
    idx_max_abs = df_operativo['Error_Abs_m3s'].abs().idxmax()
    punto_max = df_operativo.loc[idx_max_abs]
    
    print(f"\nPUNTO DE ERROR MÁXIMO (rango operativo):")
    print(f"  Volumen: {punto_max['Volumen_hm3']:.2f} hm³")
    print(f"  Cota: {punto_max['Cota_msnm']:.2f} m.s.n.m")
    print(f"  Filtración real: {punto_max['Filt_Real_m3s']:.4f} m³/s")
    print(f"  Filtración lineal: {punto_max['Filt_Lineal_m3s']:.4f} m³/s")
    print(f"  Error absoluto: {punto_max['Error_Abs_m3s']:.4f} m³/s")
    print(f"  Error relativo: {punto_max['Error_Rel_pct']:.4f} %")
    print(f"  Zona activa: {punto_max['Zona_Activa']:.0f}")
    
    # 5. Guardar resultados
    df.to_csv('resultados/analisis_error_filtraciones.csv', index=False)
    print(f"\n✓ Resultados guardados en 'resultados/analisis_error_filtraciones.csv'")
    
    return df, df_operativo, v_k, f_k


# ============================================================================
# VISUALIZACIÓN
# ============================================================================

def graficar_comparacion(df, df_operativo, v_k, f_k, V_MIN, V_MAX):
    """
    Genera gráficas de comparación entre modelo real y linealizado
    """
    print("\nGenerando gráficas...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análisis de Error - Modelo de Filtraciones Linealizado', 
                 fontsize=16, fontweight='bold')
    
    # 1. Filtraciones vs Volumen
    ax1 = axes[0, 0]
    ax1.plot(df['Volumen_hm3'], df['Filt_Real_m3s'], 'b-', 
             linewidth=2, label='Modelo Real (Polinomial)')
    ax1.plot(df['Volumen_hm3'], df['Filt_Lineal_m3s'], 'r--', 
             linewidth=2, label='Modelo Linealizado (Zonas)')
    
    # Marcar puntos de linealización
    v_vals = sorted(v_k.values())
    f_vals = [filtraciones_linealizadas(v, v_k, f_k)[0] for v in v_vals]
    ax1.plot(v_vals, f_vals, 'ro', markersize=8, 
             label=f'Puntos de Linealización (n={len(v_k)})', zorder=5)
    
    # Rango operativo
    ax1.axvline(V_MIN, color='g', linestyle=':', linewidth=1.5, alpha=0.7, label=f'V_MIN = {V_MIN:.0f} hm³')
    ax1.axvline(V_MAX, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label=f'V_MAX = {V_MAX:.0f} hm³')
    
    ax1.set_xlabel('Volumen [hm³]', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Filtraciones [m³/s]', fontsize=12, fontweight='bold')
    ax1.set_title('Filtraciones vs Volumen', fontsize=13, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # 2. Filtraciones vs Cota
    ax2 = axes[0, 1]
    ax2.plot(df['Cota_msnm'], df['Filt_Real_m3s'], 'b-', 
             linewidth=2, label='Modelo Real (Polinomial)')
    ax2.plot(df['Cota_msnm'], df['Filt_Lineal_m3s'], 'r--', 
             linewidth=2, label='Modelo Linealizado (Zonas)')
    
    # Cotas correspondientes a puntos de linealización
    cotas_lin = [cot_eltoro(v) for v in v_vals]
    ax2.plot(cotas_lin, f_vals, 'ro', markersize=8, 
             label=f'Puntos de Linealización', zorder=5)
    
    ax2.set_xlabel('Cota [m.s.n.m]', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Filtraciones [m³/s]', fontsize=12, fontweight='bold')
    ax2.set_title('Filtraciones vs Cota', fontsize=13, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Error Absoluto
    ax3 = axes[1, 0]
    ax3.plot(df['Volumen_hm3'], df['Error_Abs_m3s'], 'purple', linewidth=2)
    ax3.axhline(0, color='black', linestyle='-', linewidth=0.8)
    ax3.axvline(V_MIN, color='g', linestyle=':', linewidth=1.5, alpha=0.7)
    ax3.axvline(V_MAX, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
    
    # Sombrear rango operativo
    ax3.axvspan(V_MIN, V_MAX, alpha=0.1, color='green', label='Rango Operativo')
    
    # Estadísticas en el gráfico
    error_max_op = df_operativo['Error_Abs_m3s'].abs().max()
    error_prom_op = df_operativo['Error_Abs_m3s'].abs().mean()
    ax3.text(0.02, 0.98, f'Error máx (operativo): {error_max_op:.4f} m³/s\n'
                          f'Error prom (operativo): {error_prom_op:.4f} m³/s',
             transform=ax3.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax3.set_xlabel('Volumen [hm³]', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Error Absoluto [m³/s]', fontsize=12, fontweight='bold')
    ax3.set_title('Error Absoluto (Linealizado - Real)', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Error Relativo
    ax4 = axes[1, 1]
    
    # Filtrar errores muy grandes en zonas de filtraciones muy bajas
    df_plot = df[df['Filt_Real_m3s'].abs() > 0.01].copy()
    
    ax4.plot(df_plot['Volumen_hm3'], df_plot['Error_Rel_pct'], 'darkred', linewidth=2)
    ax4.axhline(0, color='black', linestyle='-', linewidth=0.8)
    ax4.axvline(V_MIN, color='g', linestyle=':', linewidth=1.5, alpha=0.7)
    ax4.axvline(V_MAX, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
    
    # Sombrear rango operativo
    ax4.axvspan(V_MIN, V_MAX, alpha=0.1, color='green', label='Rango Operativo')
    
    # Estadísticas en el gráfico
    error_max_rel_op = df_operativo['Error_Rel_pct'].abs().max()
    error_prom_rel_op = df_operativo['Error_Rel_pct'].abs().mean()
    ax4.text(0.02, 0.98, f'Error máx (operativo): {error_max_rel_op:.4f} %\n'
                          f'Error prom (operativo): {error_prom_rel_op:.4f} %',
             transform=ax4.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    ax4.set_xlabel('Volumen [hm³]', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Error Relativo [%]', fontsize=12, fontweight='bold')
    ax4.set_title('Error Relativo Porcentual', fontsize=13, fontweight='bold')
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('resultados/comparacion_filtraciones.png', dpi=300, bbox_inches='tight')
    print("✓ Gráfica guardada en 'resultados/comparacion_filtraciones.png'")
    
    plt.show()


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Análisis
    df, df_operativo, v_k, f_k = analizar_error_filtraciones()
    
    # Obtener V_MIN y V_MAX
    parametros = cargar_parametros_excel()
    V_MIN = parametros.get('V_MIN', 0)
    V_MAX = parametros.get('V_MAX', 5826)
    
    # Gráficas
    graficar_comparacion(df, df_operativo, v_k, f_k, V_MIN, V_MAX)
    
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
