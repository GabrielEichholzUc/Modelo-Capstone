# Flujo de Trabajo: Modelo de Optimización Lago Laja (5 Temporadas)

## 📋 Resumen

Este documento describe el flujo de trabajo completo para ejecutar el modelo de optimización del Lago Laja con 5 temporadas, **manteniendo el modelo completamente lineal (LP)**.

## 🔑 Conceptos Clave

### Problema de Linealidad

El **Convenio del Lago Laja** define los volúmenes disponibles para extracción (riego y generación) usando una **función por tramos** basada en el volumen al 30 de noviembre (V_30Nov):

```
Si V_30Nov ≤ 3650 hm³:
    VR = 0, VG = 0

Si 3650 < V_30Nov ≤ 6300 hm³:
    VR = 0.5736 × (V_30Nov - 3650)
    VG = 0.3094 × (V_30Nov - 3650)

Si V_30Nov > 6300 hm³:
    VR = 1520 hm³
    VG = 820 hm³
```

### Solución Adoptada: Preprocesamiento

Para **evitar variables binarias y restricciones Big-M** (que convertirían el modelo en MILP), adoptamos el enfoque de **preprocesamiento**:

1. **Calcular `ve_0[u,t]` ANTES de la optimización** usando valores estimados/históricos de `V_30Nov[t]`
2. **Fijar estos valores** como parámetros en el modelo de optimización
3. El modelo LP usa estos valores precalculados sin necesidad de lógica por tramos

## 🔄 Flujo de Trabajo

### Paso 1: Preparar Parámetros Base

Asegúrate de que el archivo `Parametros_Finales.xlsx` contiene todos los parámetros necesarios:

- **Hoja `Generales`**: V_0, V_MAX, V_min, V_30Nov_1, Qf, psi, phi
- **Hoja `QA_a,w,t`**: Afluentes por semana y temporada
- **Hoja `FC_k`**: Filtraciones por cota
- **Hoja `VC_k`**: Volúmenes por cota
- **Hoja `VUC_k,u`**: Volúmenes por uso y cota
- **Hoja `rho_i`**: Caudales de retiro
- **Hoja `gamma_i`**: Productividades
- **Hoja `delta_d,j`**: Demandas de riego
- **Hoja `theta_d,j`**: Prioridades de riego
- **Hoja `FS_w`**: Factor de segundos por semana

### Paso 2: Ejecutar Preprocesamiento

Ejecuta el script de preprocesamiento para calcular `ve_0[u,t]`:

```powershell
python preprocesar_volumenes_uso.py
```

Este script:
- Lee `V_30Nov_1` del archivo Excel
- Calcula `ve_0[u,t]` para cada temporada usando las reglas del convenio
- **Guarda los resultados** en una nueva hoja `VE_0_precalculado` en el mismo archivo Excel

**Salida esperada:**
```
PREPROCESAMIENTO: CÁLCULO DE VOLÚMENES DISPONIBLES POR USO
...
Temporada 1:
  V_30Nov[1] = 5500.00 hm³
  → ve_0[u=1 (riego), t=1] = 1061.28 hm³
  → ve_0[u=2 (generación), t=1] = 572.49 hm³
...
✅ Volúmenes precalculados guardados en 'Parametros_Finales.xlsx'
```

### Paso 3: Ejecutar Optimización

Ahora puedes ejecutar el modelo de optimización:

```powershell
python optimizar_laja_5temporadas.py
```

El modelo:
- Carga los parámetros desde `Parametros_Finales.xlsx`
- **Lee los valores precalculados de `ve_0[u,t]`** desde la hoja `VE_0_precalculado`
- Construye y resuelve el modelo LP (sin variables binarias)
- Exporta los resultados

**Salida esperada:**
```
CARGANDO PARÁMETROS DESDE EXCEL (5 TEMPORADAS)
...
✅ Cargados 10 valores precalculados de ve_0
...
CONSTRUYENDO MODELO DE OPTIMIZACIÓN (5 TEMPORADAS)
...
✓ Modelo lineal construido (LP, no MILP)
...
Gurobi Optimizer version...
Optimize a model with XXXX rows, YYYY columns and ZZZZ nonzeros
Model fingerprint: ...
Coefficient statistics:
...
Optimal solution found (tolerance 1.00e-04)
Best objective X.XXXXE+XX, best bound X.XXXXE+XX, gap 0.0000%
```

### Paso 4: Visualizar Resultados

Ejecuta el script de visualización:

```powershell
python visualizar_resultados_5temporadas.py
```

Genera gráficos de:
- Evolución de volúmenes embalsados
- Generación por central y temporada
- Extracciones por uso
- Entregas de riego
- Balance hídrico

## 📊 Archivos Generados

Después de ejecutar el workflow completo, tendrás:

### En el archivo Excel (`Parametros_Finales.xlsx`):
- **Hoja nueva: `VE_0_precalculado`** - Volúmenes iniciales por uso calculados

### En archivos separados:
- `resultados_5temporadas.xlsx` - Resultados detallados de la optimización
- `resumen_5temporadas.txt` - Resumen de KPIs
- Gráficos en formato PNG

## ⚙️ Parámetros Configurables

### En `preprocesar_volumenes_uso.py`:

Puedes ajustar los valores de `V_30Nov` para cada temporada editando el script:

```python
# Valores de ejemplo - EDITAR AQUÍ
V_30Nov_valores = {
    1: 5500,  # Temporada 1: tu estimación
    2: 5000,  # Temporada 2: tu estimación
    3: 5500,  # Temporada 3: tu estimación
    4: 5200,  # Temporada 4: tu estimación
    5: 5400   # Temporada 5: tu estimación
}
```

### Parámetros del Convenio:

Los parámetros del convenio están definidos en `preprocesar_volumenes_uso.py`:

```python
VG_max = 820.0        # hm³ - Volumen máximo para generación
VR_max = 1520.0       # hm³ - Volumen máximo para riego
V_umbral_min = 3650.0 # hm³ - Umbral mínimo
V_umbral_max = 6300.0 # hm³ - Umbral máximo
```

## 🔬 Enfoque Avanzado: Iteración Multi-Temporada

Si deseas mayor precisión, puedes:

1. **Ejecutar optimización** con valores iniciales de `V_30Nov`
2. **Extraer `V_30Nov[t]` de los resultados** de la optimización
3. **Re-ejecutar preprocesamiento** con estos nuevos valores
4. **Re-optimizar** con los nuevos `ve_0[u,t]`
5. **Repetir hasta convergencia**

Este enfoque iterativo mejora la consistencia entre los volúmenes asumidos y los resultados, sin necesidad de variables binarias.

## 🚨 Troubleshooting

### Error: "No se encontraron valores precalculados de ve_0"

**Causa:** No se ejecutó el preprocesamiento, o no se guardó correctamente.

**Solución:**
```powershell
python preprocesar_volumenes_uso.py
```

Verifica que el archivo `Parametros_Finales.xlsx` ahora tiene una hoja `VE_0_precalculado`.

### Error: "Model is infeasible"

**Causas posibles:**
- Volúmenes iniciales incompatibles con restricciones
- Demandas no satisfacibles con afluentes disponibles
- Restricciones de volumen mínimo muy estrictas

**Solución:**
- Revisa los parámetros de entrada (V_0, V_min, demandas)
- Ajusta `V_30Nov` en el preprocesamiento
- Usa `modelo.model.computeIIS()` para identificar restricciones conflictivas

### Modelo tarda mucho en resolver

**Causa:** Aunque el modelo es LP, puede ser grande.

**Solución:**
- Verifica que NO hay variables binarias en el modelo
- Reduce el número de semanas si es necesario (para pruebas)
- Ajusta parámetros de Gurobi (tolerancias, método, etc.)

## 📚 Referencias

- `README_VOLUMENES_POR_USO.md` - Explicación detallada del enfoque lineal vs. dinámico
- `README_IMPLEMENTACION.md` - Detalles técnicos del modelo
- `README_MONTECARLO.md` - Análisis de incertidumbre con Monte Carlo

## ✅ Checklist Rápido

Antes de ejecutar la optimización:

- [ ] Archivo `Parametros_Finales.xlsx` actualizado con todos los parámetros
- [ ] Ejecutado `preprocesar_volumenes_uso.py`
- [ ] Hoja `VE_0_precalculado` existe en el Excel
- [ ] Valores de `V_30Nov` son realistas para tu caso de estudio
- [ ] Gurobi instalado y con licencia válida
- [ ] Python 3.8+ con pandas, numpy, gurobipy, openpyxl instalados

¡Ahora estás listo para optimizar! 🚀
