"""
Script principal para optimizar el modelo de la cuenca del Laja
"""

from modelo_laja import ModeloLaja
from cargar_datos import cargar_parametros_excel
import time

def main():
    """
    Función principal para ejecutar la optimización
    """
    print("\n" + "="*70)
    print(" "*15 + "OPTIMIZACIÓN CUENCA DEL LAJA")
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
    modelo = ModeloLaja()
    
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
    
    # Configuración de optimización
    tiempo_limite = 600  # 10 minutos
    gap = 0.01  # 1% de optimalidad
    
    print(f"\nConfiguración:")
    print(f"  - Tiempo límite: {tiempo_limite} segundos ({tiempo_limite/60:.1f} minutos)")
    print(f"  - Gap de optimalidad: {gap*100:.2f}%")
    print(f"  - Solver: Gurobi 12.0.3")
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
    print(f"\nTiempo total de ejecución: {tiempo_total:.2f} segundos")
    print(f"Archivos generados en carpeta 'resultados/':")
    print("  ✓ generacion.csv - Caudales de generación por central y semana")
    print("  ✓ vertimientos.csv - Vertimientos en cada punto")
    print("  ✓ volumenes_lago.csv - Evolución del volumen del lago")
    print("  ✓ riego.csv - Retiros, déficits e incumplimientos de riego")
    print("  ✓ energia_total.csv - Energía total generada por central")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Optimización interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
