"""
Script para diagnosticar infactibilidad del modelo LaTeX
"""

from modelo_laja_latex import ModeloLajaLatex
from cargar_datos_5temporadas import cargar_parametros_excel

print("Cargando parámetros...")
parametros = cargar_parametros_excel()

print("\nCreando modelo...")
modelo = ModeloLajaLatex()
modelo.cargar_parametros(parametros)
modelo.construir_modelo()

print("\nComputando IIS (Conjunto Irreductiblemente Infactible)...")
modelo.model.computeIIS()

print("\nEscribiendo archivo .ilp con restricciones conflictivas...")
modelo.model.write("modelo_infactible.ilp")

print("\n" + "="*70)
print("RESTRICCIONES EN CONFLICTO:")
print("="*70)

# Mostrar restricciones en conflicto
conflictos = []
for constr in modelo.model.getConstrs():
    if constr.IISConstr:
        conflictos.append(constr.ConstrName)
        print(f"  • {constr.ConstrName}")

print(f"\nTotal de restricciones en conflicto: {len(conflictos)}")
print("\nArchivo 'modelo_infactible.ilp' generado para inspección detallada")
