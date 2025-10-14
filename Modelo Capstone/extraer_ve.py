
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
    
    # ve[u,w] para cada semana
    for u in [1, 2]:
        uso_nombre = "Riego" if u == 1 else "Generación"
        for w in range(1, 49):
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
