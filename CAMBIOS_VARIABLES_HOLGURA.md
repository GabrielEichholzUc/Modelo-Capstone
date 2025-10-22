# 📋 Cambios: Variables de Holgura del Modelo

## 🎯 Objetivo

Simplificar el modelo eliminando la variable `superavit` y manteniendo únicamente dos variables de holgura:

1. **`deficit`** - Holgura de riego (penalizada por `psi`)
2. **`betha`** - Holgura de volumen mínimo del lago (penalizada por `phi`)

## ✨ Cambios Realizados

### 1. Variables de Decisión

**ANTES:**

```python
# Déficit y superávit
self.deficit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="deficit")
self.superavit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="superavit")
```

**AHORA:**

```python
# Variables de holgura
self.deficit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="deficit")  # Holgura de riego
self.betha = self.model.addVars(self.W, self.T, lb=0, name="betha")  # Holgura de volumen mínimo
```

### 2. Restricciones de Balance de Riego

**ANTES (con superávit):**

```python
# Balance demanda
self.model.addConstr(
    self.QD.get((d, j, w), 0) - self.qp[d, j, w, t] == self.deficit[d, j, w, t] - self.superavit[d, j, w, t],
    name=f"balance_{d}_{j}_{w}_{t}")
```

**AHORA (sin superávit):**

```python
# Balance demanda (qp puede ser menor o igual a demanda)
self.model.addConstr(
    self.qp[d, j, w, t] + self.deficit[d, j, w, t] == self.QD.get((d, j, w), 0),
    name=f"balance_{d}_{j}_{w}_{t}")
```

**Interpretación:**

- `qp[d, j, w, t]` = Caudal provisto al regante
- `deficit[d, j, w, t]` = Déficit de riego (cuando no se cumple toda la demanda)
- `qp + deficit = demanda` → **El modelo puede entregar menos de lo demandado**

### 3. Nueva Restricción: Volumen Mínimo con Holgura

**NUEVA RESTRICCIÓN:**

```python
# V[w,t] + betha[w,t] >= V_min
# Si V[w,t] < V_min, entonces betha[w,t] > 0 (penalizado en F.O.)
for t in self.T:
    for w in self.W:
        self.model.addConstr(
            self.V[w, t] + self.betha[w, t] >= self.V_min,
            name=f"vol_min_holgura_{w}_{t}")
```

**Interpretación:**

- Si `V[w,t] >= V_min` → `betha[w,t] = 0` (no hay penalización)
- Si `V[w,t] < V_min` → `betha[w,t] > 0` (se activa penalización en F.O.)

### 4. Función Objetivo Actualizada

**ANTES:**

```python
# Solo penalización por déficit de riego
self.model.setObjective(
    generacion_total - penalidad_deficit * self.psi,
    GRB.MAXIMIZE
)
```

**AHORA:**

```python
# Penalización por déficit de riego
penalidad_deficit = gp.quicksum(
    self.deficit[d, j, w, t] * self.FS[w] / 1000000  # Convertir a hm³
    for d in self.D for j in self.J for w in self.W for t in self.T
)

# Penalización por violación de volumen mínimo
penalidad_volumen = gp.quicksum(
    self.betha[w, t]  # Ya está en hm³
    for w in self.W for t in self.T
)

# Función objetivo
self.model.setObjective(
    generacion_total - penalidad_deficit * self.psi - penalidad_volumen * self.phi,
    GRB.MAXIMIZE
)
```

**Unidades:**

- `generacion_total`: [GWh]
- `penalidad_deficit`: [hm³] → multiplicado por `psi` [GWh/hm³] → [GWh]
- `penalidad_volumen`: [hm³] → multiplicado por `phi` [GWh/hm³] → [GWh]
- **Todas las componentes están en [GWh]** ✅

### 5. Exportación de Resultados

**Cambios en `riego.csv`:**

- ❌ Eliminada columna `Superavit_m3s`
- ✅ Mantiene columnas: `Demanda_m3s`, `Provisto_m3s`, `Deficit_m3s`

**Nuevo archivo `holguras_volumen.csv`:**

```csv
Semana,Temporada,Betha_hm3
15,1,50.5
23,2,30.2
...
```

- Solo se exporta si hay violaciones de volumen mínimo (`betha > 0.001`)
- Indica en qué semanas y temporadas el lago bajó del volumen mínimo

## 📊 Interpretación de Resultados

### Variable `deficit[d, j, w, t]`

**Significado:** Déficit de riego para demanda `d` en canal `j`, semana `w`, temporada `t`

**Interpretación:**

- `deficit = 0` → ✅ Se cumplió completamente la demanda
- `deficit > 0` → ⚠️ No se cumplió la demanda (se proveyó menos de lo solicitado)

**Ejemplo:**

```
Demanda_m3s = 10.0
Provisto_m3s = 7.5
Deficit_m3s = 2.5  → Se dejó de entregar 2.5 m³/s
```

### Variable `betha[w, t]`

**Significado:** Holgura de volumen mínimo en semana `w`, temporada `t`

**Interpretación:**

- `betha = 0` → ✅ El volumen del lago cumple con `V >= V_min`
- `betha > 0` → ⚠️ El volumen del lago bajó del mínimo (`V < V_min`)

**Ejemplo:**

```
V_min = 1400 hm³
V[w,t] = 1350 hm³
betha[w,t] = 50 hm³  → Se violó el volumen mínimo en 50 hm³
```

## 🎛️ Calibración de Penalizaciones

### Parámetro `psi` (Déficit de Riego)

**Unidades:** [GWh/hm³]

**Valores sugeridos:**

- `psi = 10` → Penalización moderada (permite déficits si generan más energía)
- `psi = 100` → Penalización alta (prioriza cumplir riego sobre generación)
- `psi = 1000` → Penalización muy alta (casi nunca habrá déficit)

**Recomendación:** Ajustar según la importancia relativa del riego vs. generación.

### Parámetro `phi` (Volumen Mínimo)

**Unidades:** [GWh/hm³]

**Valores sugeridos:**

- `phi = 5` → Penalización baja (permite bajar del mínimo si genera mucha energía)
- `phi = 50` → Penalización moderada (evita bajar del mínimo salvo casos críticos)
- `phi = 500` → Penalización muy alta (nunca baja del mínimo)

**Recomendación:** Usar valores altos para garantizar sustentabilidad del lago.

## 📈 Análisis Post-Optimización

### 1. Revisar Déficits de Riego

```python
import pandas as pd

# Cargar resultados
df_riego = pd.read_csv("resultados/riego.csv")

# Filtrar solo déficits
df_deficit = df_riego[df_riego['Deficit_m3s'] > 0.01]

# Resumen por canal
print(df_deficit.groupby('Canal')['Deficit_m3s'].sum())

# Semanas críticas
print(df_deficit.sort_values('Deficit_m3s', ascending=False).head(10))
```

### 2. Revisar Violaciones de Volumen Mínimo

```python
import pandas as pd
import os

# Verificar si hay violaciones
if os.path.exists("resultados/holguras_volumen.csv"):
    df_betha = pd.read_csv("resultados/holguras_volumen.csv")

    print(f"Total de violaciones: {len(df_betha)}")
    print(f"Máxima violación: {df_betha['Betha_hm3'].max()} hm³")
    print(f"Violación total: {df_betha['Betha_hm3'].sum()} hm³")

    # Por temporada
    print(df_betha.groupby('Temporada')['Betha_hm3'].agg(['count', 'sum', 'max']))
else:
    print("✅ No hay violaciones de volumen mínimo")
```

### 3. Calcular Impacto en Función Objetivo

```python
# Componentes de la F.O.
generacion_total = df_energia['Energia_GWh'].sum()

# Penalizaciones
deficit_total_hm3 = (df_riego['Deficit_m3s'] * df_riego['FS_w'] / 1e6).sum()
penalidad_deficit_GWh = deficit_total_hm3 * psi

betha_total_hm3 = df_betha['Betha_hm3'].sum() if 'df_betha' in locals() else 0
penalidad_volumen_GWh = betha_total_hm3 * phi

# Función objetivo
FO_total = generacion_total - penalidad_deficit_GWh - penalidad_volumen_GWh

print(f"Generación total:        {generacion_total:>10.2f} GWh")
print(f"Penalización déficit:    {penalidad_deficit_GWh:>10.2f} GWh")
print(f"Penalización volumen:    {penalidad_volumen_GWh:>10.2f} GWh")
print(f"{'='*40}")
print(f"Valor función objetivo:  {FO_total:>10.2f} GWh")
```

## 🔄 Comparación: ANTES vs. AHORA

| Aspecto              | ANTES                                      | AHORA                                |
| -------------------- | ------------------------------------------ | ------------------------------------ |
| Variables de holgura | `deficit`, `superavit`                     | `deficit`, `betha`                   |
| Balance de riego     | `demanda - provisto = deficit - superavit` | `provisto + deficit = demanda`       |
| Volumen mínimo       | Restricción dura                           | Restricción blanda (con betha)       |
| Función objetivo     | `max(GEN - psi·deficit)`                   | `max(GEN - psi·deficit - phi·betha)` |
| Interpretación       | Superávit sin uso claro                    | Betha indica violaciones de V_min    |
| Archivos exportados  | `riego.csv` (con superávit)                | `riego.csv` + `holguras_volumen.csv` |

## ✅ Ventajas del Nuevo Enfoque

1. **Simplicidad:** Elimina variable `superavit` que no tenía interpretación clara
2. **Claridad:** `betha` indica explícitamente violaciones de volumen mínimo
3. **Control:** Permite ajustar penalizaciones independientes para riego (`psi`) y volumen (`phi`)
4. **Flexibilidad:** El modelo puede violar V_min si es necesario (pero penalizado)
5. **Diagnóstico:** Archivo `holguras_volumen.csv` facilita identificar períodos críticos

## 🚀 Próximos Pasos

1. ✅ **Ejecutar optimización** con los nuevos cambios
2. ✅ **Revisar resultados** de `deficit` y `betha`
3. ✅ **Ajustar penalizaciones** (`psi`, `phi`) según necesidades del caso de estudio
4. ✅ **Analizar trade-offs** entre generación, riego y sustentabilidad del lago

---

**¡El modelo ahora tiene variables de holgura más claras y útiles! 🎯**
