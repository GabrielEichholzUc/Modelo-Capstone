"""
Script ejemplo: Preprocesamiento de volúmenes iniciales desde Excel
Este script muestra cómo calcular ve_0[u,t] para el modelo de optimización
"""

from cargar_datos_5temporadas import cargar_parametros_excel
from preprocesar_volumenes_uso import calcular_volumenes_iniciales_por_uso, guardar_ve_0_en_excel

def main():
    """
    Flujo completo de preprocesamiento:
    1. Cargar parámetros desde Excel
    2. Definir V_30Nov para cada temporada
    3. Calcular ve_0[u,t]
    4. Guardar en Excel
    """
    
    print("="*80)
    print(" " * 15 + "PREPROCESAMIENTO DE VOLÚMENES INICIALES")
    print("="*80)
    
    # 1. Cargar parámetros base desde Excel
    print("\n[1/4] Cargando parámetros base desde Excel...")
    parametros = cargar_parametros_excel("Parametros_Finales.xlsx")
    
    # 2. Definir V_30Nov para cada temporada
    print("\n[2/4] Definiendo valores de V_30Nov por temporada...")
    print("\nOPCIONES:")
    print("  A) Usar V_30Nov_1 para todas las temporadas (aproximación simple)")
    print("  B) Definir valores personalizados por temporada")
    print("  C) Usar valores históricos/estimados")
    
    # Opción A: Usar el mismo valor para todas
    V_30Nov_1 = parametros['V_30Nov_1']
    
    # EDITAR AQUÍ: Puedes cambiar estos valores según tu caso de estudio
    # Opción simple: todas las temporadas con el mismo V_30Nov_1
    usar_mismo_valor = True
    
    if usar_mismo_valor:
        print(f"\n  → Usando V_30Nov_1 = {V_30Nov_1:,.0f} hm³ para todas las temporadas")
        V_30Nov_valores = {
            1: V_30Nov_1,
            2: V_30Nov_1,
            3: V_30Nov_1,
            4: V_30Nov_1,
            5: V_30Nov_1
        }
    else:
        # Opción personalizada: definir valor por temporada
        print("\n  → Usando valores personalizados por temporada:")
        V_30Nov_valores = {
            1: 5500,  # Temporada 1: Otoño (abr-jun) - volumen intermedio
            2: 4500,  # Temporada 2: Invierno (jul-sep) - recarga esperada
            3: 6000,  # Temporada 3: Primavera (oct-dic) - alta demanda riego
            4: 5000,  # Temporada 4: Verano 1 (ene-mar) - alta evaporación
            5: 4800   # Temporada 5: Verano 2 (abr-jun) - uso intensivo
        }
        for t, v in V_30Nov_valores.items():
            print(f"     Temporada {t}: {v:,.0f} hm³")
    
    # 3. Calcular volúmenes disponibles
    print("\n[3/4] Calculando volúmenes disponibles por uso (ve_0)...")
    resultados = calcular_volumenes_iniciales_por_uso(V_30Nov_valores, parametros['FS'])
    
    # 4. Guardar en Excel
    print("\n[4/4] Guardando resultados en Excel...")
    df_guardado = guardar_ve_0_en_excel(resultados['ve_0'], "Parametros_Finales.xlsx")
    
    # Mostrar tabla final
    print("\n" + "="*80)
    print("TABLA FINAL DE VOLÚMENES PRECALCULADOS")
    print("="*80)
    print("\n" + df_guardado.to_string(index=False))
    
    # Resumen por temporada
    print("\n" + "="*80)
    print("RESUMEN POR TEMPORADA")
    print("="*80)
    
    for t in sorted(V_30Nov_valores.keys()):
        VR = resultados['VR'][t]
        VG = resultados['VG'][t]
        total = VR + VG
        print(f"\nTemporada {t}:")
        print(f"  V_30Nov[{t}]              = {V_30Nov_valores[t]:>8,.0f} hm³")
        print(f"  VR (Riego)               = {VR:>8,.2f} hm³  ({VR/1520*100:5.1f}% del máximo)")
        print(f"  VG (Generación)          = {VG:>8,.2f} hm³  ({VG/820*100:5.1f}% del máximo)")
        print(f"  Total extraíble          = {total:>8,.2f} hm³")
    
    # Estadísticas globales
    print("\n" + "="*80)
    print("ESTADÍSTICAS GLOBALES (5 TEMPORADAS)")
    print("="*80)
    
    VR_total = sum(resultados['VR'].values())
    VG_total = sum(resultados['VG'].values())
    VR_promedio = VR_total / 5
    VG_promedio = VG_total / 5
    
    print(f"\nRiego:")
    print(f"  Total 5 temporadas       = {VR_total:>8,.2f} hm³")
    print(f"  Promedio por temporada   = {VR_promedio:>8,.2f} hm³")
    print(f"  Máximo posible (1520×5)  = {1520*5:>8,.0f} hm³")
    print(f"  Utilización promedio     = {VR_promedio/1520*100:>8.1f}%")
    
    print(f"\nGeneración:")
    print(f"  Total 5 temporadas       = {VG_total:>8,.2f} hm³")
    print(f"  Promedio por temporada   = {VG_promedio:>8,.2f} hm³")
    print(f"  Máximo posible (820×5)   = {820*5:>8,.0f} hm³")
    print(f"  Utilización promedio     = {VG_promedio/820*100:>8.1f}%")
    
    print(f"\nTotal:")
    print(f"  Total extraíble (5 temp) = {VR_total + VG_total:>8,.2f} hm³")
    print(f"  Promedio por temporada   = {(VR_promedio + VG_promedio):>8,.2f} hm³")
    
    print("\n" + "="*80)
    print("✅ PREPROCESAMIENTO COMPLETADO")
    print("="*80)
    print("\nPróximos pasos:")
    print("  1. Verificar que la hoja 'VE_0_precalculado' existe en Parametros_Finales.xlsx")
    print("  2. Ejecutar: python optimizar_laja_5temporadas.py")
    print("  3. El modelo LP usará estos valores precalculados (sin variables binarias)")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
