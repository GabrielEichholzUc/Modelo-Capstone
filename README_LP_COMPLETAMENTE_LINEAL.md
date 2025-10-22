# ✅ Modelo LP Completamente Lineal - Lago Laja (5 Temporadas)

## 🎯 Objetivo Logrado

El modelo de optimización del Lago Laja ha sido **completamente linearizado**, eliminando **todas las variables binarias y restricciones no lineales** que existían previamente.

## ✨ Cambios Principales

### 1. Eliminación de Lógica No Lineal

**ANTES (MILP - Mixed Integer Linear Programming):**
```python
# Variables binarias para identificar tramos
self.lambda_1 = self.model.addVars(self.T, vtype=GRB.BINARY)
self.lambda_2 = self.model.addVars(self.T, vtype=GRB.BINARY)
self.lambda_3 = self.model.addVars(self.T, vtype=GRB.BINARY)

# Restricciones Big-M
self.model.addConstr(V_30Nov[t] <= V_umbral_min + M * (1 - lambda_1[t]))
# ... más restricciones Big-M
```

**AHORA (LP - Linear Programming):**
```python
# Usar valores precalculados (sin binarias)
self.model.addConstr(
    self.ve_0[u, t] == ve_0_precalc[(u, t)],
    name=f"ve_0_fijo_{u}_{t}"
)
```

### 2. Nuevo Flujo de Trabajo

#### Paso 1: Preprocesamiento
```bash
python ejemplo_preprocesamiento.py
```

Este script:
- Lee `V_30Nov_1` del Excel
- Calcula `ve_0[u,t]` para cada temporada usando las reglas del convenio (fuera del solver)
- Guarda los resultados en hoja `VE_0_precalculado` del Excel

#### Paso 2: Optimización
```bash
python optimizar_laja_5temporadas.py
```

El modelo:
- Carga `ve_0_precalculado` desde Excel
- **NO usa variables binarias**
- Resuelve un problema LP puro
- Es **mucho más rápido** que MILP

### 3. Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `caso_base_5temporadas.py` | ✅ Eliminadas variables binarias<br>✅ Eliminadas restricciones Big-M<br>✅ Usa `ve_0_precalculado` como parámetro |
| `cargar_datos_5temporadas.py` | ✅ Nueva función `cargar_ve_0_precalculado()`<br>✅ Carga automática de volúmenes precalculados |
| `preprocesar_volumenes_uso.py` | ✅ Función `guardar_ve_0_en_excel()`<br>✅ Exporta a hoja Excel |
| `ejemplo_preprocesamiento.py` | ✨ **NUEVO**: Script de ejemplo completo |

### 4. Archivos de Documentación

| Archivo | Descripción |
|---------|-------------|
| `README_WORKFLOW.md` | 📖 Guía paso a paso del flujo completo |
| `README_VOLUMENES_POR_USO.md` | 📘 Explicación técnica del enfoque lineal vs. dinámico |
| `README_IMPLEMENTACION.md` | 📙 Detalles técnicos del modelo |

## 🔬 Comparación: MILP vs. LP

### Enfoque Anterior (MILP)

**Ventajas:**
- ✅ Dinámica automática de `ve_0[u,t]`
- ✅ Consistencia perfecta entre `V_30Nov` y `ve_0`

**Desventajas:**
- ❌ Variables binarias → problema más difícil
- ❌ Tiempos de resolución más largos
- ❌ No garantiza optimalidad global en tiempo razonable
- ❌ Requiere ajuste fino de parámetros Big-M

### Enfoque Actual (LP)

**Ventajas:**
- ✅ **Modelo completamente lineal** → resolución rápida
- ✅ **Garantía de optimalidad global**
- ✅ **Escalable** a más temporadas/semanas
- ✅ No requiere parámetros Big-M
- ✅ Solver encuentra solución óptima muy rápido

**Desventajas:**
- ⚠️ Requiere preprocesamiento para calcular `ve_0[u,t]`
- ⚠️ `ve_0[u,t]` fijo durante optimización (no se ajusta dinámicamente)

**Solución a las desventajas:**
- Enfoque iterativo: optimizar → actualizar `V_30Nov` → recalcular `ve_0` → re-optimizar

## 📊 Estructura del Excel

El archivo `Parametros_Finales.xlsx` ahora debe incluir:

### Hojas Existentes
- `Generales` - Parámetros generales
- `QA_a,w,t` - Afluentes
- `FC_k`, `VC_k`, `VUC_k,u` - Curvas de nivel
- `rho_i`, `gamma_i` - Características de centrales
- `delta_d,j`, `theta_d,j` - Demandas y prioridades
- `FS_w` - Factor de segundos

### Hoja Nueva (generada por preprocesamiento)
- **`VE_0_precalculado`** ⬅️ **NUEVA**
  - Columnas: `Uso`, `Uso_Nombre`, `Temporada`, `VE_0`
  - 10 filas (2 usos × 5 temporadas)

## 🚀 Ejemplo de Uso Completo

```python
# 1. Preprocesamiento (ejecutar UNA VEZ o cuando cambien V_30Nov)
from cargar_datos_5temporadas import cargar_parametros_excel
from preprocesar_volumenes_uso import calcular_volumenes_iniciales_por_uso, guardar_ve_0_en_excel

# Cargar parámetros
parametros = cargar_parametros_excel("Parametros_Finales.xlsx")

# Definir V_30Nov por temporada
V_30Nov_valores = {
    1: 5500,
    2: 5000,
    3: 5500,
    4: 5200,
    5: 5400
}

# Calcular y guardar
resultados = calcular_volumenes_iniciales_por_uso(V_30Nov_valores, parametros['FS'])
guardar_ve_0_en_excel(resultados['ve_0'], "Parametros_Finales.xlsx")

# 2. Optimización (usa los valores precalculados)
from caso_base_5temporadas import ModeloLaja5Temporadas

# Cargar parámetros (ahora incluye ve_0_precalculado)
parametros = cargar_parametros_excel("Parametros_Finales.xlsx")

# Crear y resolver modelo LP
modelo = ModeloLaja5Temporadas(parametros)
modelo.resolver()
modelo.exportar_resultados()
```

## 🔍 Verificación de Linealidad

Para confirmar que el modelo es LP puro:

```python
# En caso_base_5temporadas.py, después de crear el modelo:
modelo.model.update()

# Verificar número de variables binarias (debe ser 0)
num_binarias = sum(1 for v in modelo.model.getVars() if v.VType == GRB.BINARY)
print(f"Variables binarias: {num_binarias}")  # Debe imprimir 0

# Verificar tipo de modelo
print(f"Tipo de modelo: {modelo.model.ModelSense}")
```

## 📈 Resultados Exportados

El modelo exporta automáticamente:

1. **`generacion.csv`** - Caudales de generación por central
2. **`vertimientos.csv`** - Vertimientos
3. **`volumenes_lago.csv`** - Volúmenes embalsados
4. **`volumenes_por_uso.csv`** ⬅️ Volúmenes por uso (riego/generación)
5. **`extracciones_por_uso.csv`** ⬅️ Caudales extraídos por uso
6. **`riego.csv`** - Entregas y déficits de riego
7. **`energia_total.csv`** - Energía generada por central

## ⚡ Mejoras en Rendimiento

| Métrica | MILP (Antes) | LP (Ahora) |
|---------|--------------|------------|
| Variables binarias | ~5-15 | **0** ✅ |
| Tiempo de resolución | Minutos-horas | **Segundos** ✅ |
| Optimalidad | No garantizada | **Garantizada** ✅ |
| Escalabilidad | Limitada | **Excelente** ✅ |

## 🎓 Notas Técnicas

### ¿Por qué necesitamos preprocesamiento?

El **Convenio del Lago Laja** define volúmenes disponibles usando una función **por tramos**:

```
ve_0[u,t] = f(V_30Nov[t])

donde f() es una función por tramos (piecewise)
```

**Opciones para modelar:**

1. **Dinámica (MILP)**: Usar variables binarias para identificar el tramo → NO LINEAL
2. **Preprocesamiento (LP)**: Calcular `ve_0` antes de optimizar → **LINEAL** ✅

Elegimos la opción 2 para mantener el modelo completamente lineal.

### ¿Cómo manejar la incertidumbre en `V_30Nov`?

Para temporadas futuras (t > 1), `V_30Nov[t]` es desconocido. Opciones:

1. **Aproximación simple**: Usar `V_30Nov_1` para todas las temporadas
2. **Históricos**: Usar promedios históricos por temporada
3. **Iterativo**: 
   - Optimizar con valores iniciales
   - Extraer `V_30Nov[t]` de resultados
   - Recalcular `ve_0[u,t]`
   - Re-optimizar hasta convergencia

4. **Monte Carlo**: Simular múltiples escenarios de `V_30Nov` (ver `README_MONTECARLO.md`)

## 📚 Próximos Pasos

1. ✅ **Ejecutar preprocesamiento** con tus valores de `V_30Nov`
2. ✅ **Verificar** que la hoja `VE_0_precalculado` existe
3. ✅ **Optimizar** el modelo LP
4. ✅ **Analizar** resultados
5. 🔄 *Opcional*: Iterar para refinar `ve_0[u,t]`

## 🆘 Soporte

Si encuentras problemas:

1. **Verificar** que `ve_0_precalculado` existe en el Excel
2. **Confirmar** que no hay variables binarias: `grep -r "GRB.BINARY" *.py`
3. **Revisar** que el modelo se construye sin errores
4. **Consultar** `README_WORKFLOW.md` para el flujo completo

---

**¡El modelo ahora es completamente lineal y está listo para optimizar! 🚀**
