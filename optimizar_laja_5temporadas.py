"""
Script principal para optimizar el modelo de 5 temporadas de la cuenca del Laja
Utiliza la formulación LaTeX con linealización por zonas progresivas
"""

from modelo_laja_latex import ModeloLajaLatex
from cargar_datos_5temporadas import cargar_parametros_excel
import time

def main():
    """
    Función principal para ejecutar la optimización de 5 temporadas
    """
    print("\n" + "="*70)
    print(" "*10 + "OPTIMIZACIÓN CUENCA DEL LAJA - 5 TEMPORADAS")
    print(" "*10 + "Convenio Hidroeléctricas y Riegos")
    print("="*70 + "\n")
    
    # 1. Cargar datos desde Excel
    print("PASO 1: Cargando datos desde Excel...")
    print("-" * 70)
    parametros = cargar_parametros_excel()
    
    # 2. Crear instancia del modelo
    print("\n" + "="*70)
    print("PASO 2: Inicializando modelo de optimización...")
    print("-" * 70)
    modelo = ModeloLajaLatex()
    
    # 3. Cargar parámetros en el modelo
    print("\nCargando parámetros en el modelo...")
    modelo.cargar_parametros(parametros)
    
    # 4. Construir modelo
    print("\n" + "="*70)
    print("PASO 3: Construyendo modelo matemático...")
    print("-" * 70)
    modelo.construir_modelo()
    
    # 5. Optimizar
    print("\n" + "="*70)
    print("PASO 4: Ejecutando optimización...")
    print("-" * 70)
    
    # Configuración de optimización (ajustada para modelo más grande)
    tiempo_limite = 3600  # 1 hora (el modelo es 5x más grande)
    gap = 0.02  # 2% de optimalidad (más permisivo por tamaño)
    
    print(f"\nConfiguración:")
    print(f"  - Tiempo límite: {tiempo_limite} segundos ({tiempo_limite/60:.0f} minutos)")
    print(f"  - Gap de optimalidad: {gap*100:.1f}%")
    print(f"  - Solver: Gurobi")
    print(f"  - Temporadas: 5")
    print(f"  - Semanas por temporada: 48")
    print(f"  - Total semanas simuladas: 240")
    print()
    
    inicio = time.time()
    modelo.optimizar(time_limit=tiempo_limite, mip_gap=gap)
    tiempo_total = time.time() - inicio
    
    # 6. Exportar resultados
    print("\n" + "="*70)
    print("PASO 5: Exportando resultados...")
    print("-" * 70)
    modelo.exportar_resultados()
    
    # Resumen final
    print("\n" + "="*70)
    print("OPTIMIZACIÓN COMPLETADA")
    print("="*70)
    print(f"\nTiempo total de ejecución: {tiempo_total:.2f} segundos ({tiempo_total/60:.2f} minutos)")
    print(f"\nArchivos generados en carpeta 'resultados/':")
    print("  ✓ generacion.csv - Caudales de generación por central, semana y temporada")
    print("  ✓ vertimientos.csv - Vertimientos en cada punto")
    print("  ✓ volumenes_lago.csv - Evolución del volumen del lago")
    print("  ✓ riego.csv - Retiros, déficits e incumplimientos de riego")
    print("  ✓ decision_alpha.csv - Decisión Abanico vs Tucapel por semana")
    print("  ✓ decision_beta.csv - Penalizaciones por umbral mínimo")
    print("  ✓ energia_total.csv - Energía total generada por central y temporada")
    print("  ✓ phi_zonas.csv - Zonas de linealización activadas (formulación LaTeX)")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Optimización interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
