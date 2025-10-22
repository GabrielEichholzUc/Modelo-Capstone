# Cálculo Dinámico de Volúmenes por Uso (ve_0)

## Problema Original

En el modelo de 5 temporadas, necesitamos calcular `ve_0[u,t]` (volumen disponible inicial para uso `u` en temporada `t`) basándonos en el volumen al 30 de noviembre previo a cada temporada (`V_30Nov[t]`).

### Dependencia Circular

Para la temporada 2 en adelante:
- `ve_0[u,2]` depende de `V_30Nov[2]`
- `V_30Nov[2] = V[32,1]` (volumen en semana 32 de temporada 1)
- `V[32,1]` depende de las extracciones realizadas en temporada 1
- Las extracciones dependen de `ve_0[u,1]`

**Por lo tanto, no podemos precalcular `ve_0[u,t]` para todas las temporadas antes de la optimización.**

## Solución Implementada: Restricciones Dinámicas con Variables Binarias

### Modelo del Convenio del Lago Laja

El Convenio establece una función por tramos para calcular los volúmenes disponibles:

```
Si V_30Nov ≤ 3650 hm³:
    VR = 0
    VG = 0

Si 3650 < V_30Nov ≤ 6300 hm³:
    VR = aR × (V_30Nov - 3650)
    VG = aG × (V_30Nov - 3650)
    donde:
        aR = 1520 / (6300 - 3650) ≈ 0.5736
        aG = 820 / (6300 - 3650) ≈ 0.3094

Si V_30Nov > 6300 hm³:
    VR = 1520 hm³ (máximo para riego)
    VG = 820 hm³ (máximo para generación)
```

### Implementación en el Modelo

#### 1. Variables Binarias para Identificar Tramos

Para cada temporada `t`, creamos 3 variables binarias:
- `λ₁[t]`: Activa si V_30Nov[t] está en Tramo 1 (≤ 3650)
- `λ₂[t]`: Activa si V_30Nov[t] está en Tramo 2 (3650 < V ≤ 6300)
- `λ₃[t]`: Activa si V_30Nov[t] está en Tramo 3 (> 6300)

#### 2. Restricciones del Modelo

**a) Exactamente un tramo activo:**
```
λ₁[t] + λ₂[t] + λ₃[t] = 1  ∀t
```

**b) Límites de cada tramo (usando Big-M):**
```
Tramo 1: V_30Nov[t] ≤ 3650 + M×(1 - λ₁[t])

Tramo 2: V_30Nov[t] ≥ 3650 - M×(1 - λ₂[t])
         V_30Nov[t] ≤ 6300 + M×(1 - λ₂[t])

Tramo 3: V_30Nov[t] ≥ 6300 - M×(1 - λ₃[t])
```

**c) Cálculo de ve_0 para riego (u=1):**
```
ve_0[1,t] = λ₁[t]×0 + λ₂[t]×aR×(V_30Nov[t] - 3650) + λ₃[t]×1520
```

**d) Cálculo de ve_0 para generación (u=2):**
```
ve_0[2,t] = λ₁[t]×0 + λ₂[t]×aG×(V_30Nov[t] - 3650) + λ₃[t]×820
```

## Ventajas de esta Solución

### ✅ Consistencia Temporal
- `ve_0[u,t]` se calcula automáticamente en función del volumen real al 30 de noviembre
- Para temporada 1: usa `V_30Nov_1` (parámetro de entrada)
- Para temporadas 2-5: usa `V_30Nov[t] = V[32, t-1]` (calculado por el modelo)

### ✅ Correctitud del Convenio
- Implementa fielmente las reglas del Convenio del Lago Laja
- La función por tramos se modela exactamente con variables binarias

### ✅ Optimización Integrada
- El solver puede tomar decisiones óptimas considerando cómo las extracciones de una temporada afectan las disponibilidades futuras
- Elimina la necesidad de iteraciones o aproximaciones

## Flujo de Cálculo en el Modelo

```
Temporada 1:
    V_30Nov[1] = V_30Nov_1 (parámetro fijo)
    → λ[1] determina el tramo según V_30Nov[1]
    → ve_0[u,1] se calcula según el tramo
    → Se optimizan extracciones qe[u,w,1]
    → V[w,1] evoluciona según balance de masa
    → V[32,1] determina V_30Nov[2]

Temporada 2:
    V_30Nov[2] = V[32,1] (resultado de temp 1)
    → λ[2] determina el tramo según V_30Nov[2]
    → ve_0[u,2] se calcula según el tramo
    → ... y así sucesivamente

Temporadas 3-5:
    Similar a temporada 2
```

## Ejemplo Numérico

Supongamos que al optimizar el modelo, obtenemos:

```
Temporada 1:
    V_30Nov[1] = 5500 hm³ (parámetro de entrada)
    → Está en Tramo 2: 3650 < 5500 ≤ 6300
    → λ₁[1] = 0, λ₂[1] = 1, λ₃[1] = 0
    → ve_0[1,1] = 0.5736 × (5500 - 3650) = 1061.16 hm³ (riego)
    → ve_0[2,1] = 0.3094 × (5500 - 3650) = 572.39 hm³ (generación)
    
    Después de optimizar semana a semana:
    → V[32,1] = 4200 hm³

Temporada 2:
    V_30Nov[2] = V[32,1] = 4200 hm³
    → Está en Tramo 2: 3650 < 4200 ≤ 6300
    → λ₁[2] = 0, λ₂[2] = 1, λ₃[2] = 0
    → ve_0[1,2] = 0.5736 × (4200 - 3650) = 315.48 hm³ (riego)
    → ve_0[2,2] = 0.3094 × (4200 - 3650) = 170.17 hm³ (generación)
```

## Código Relevante

### Restricciones (en `crear_restricciones()`)

```python
# Parámetros del convenio
VG_max = 820.0  # hm³
VR_max = 1520.0  # hm³
V_umbral_min = 3650.0  # hm³
V_umbral_max = 6300.0  # hm³
aG = VG_max / (V_umbral_max - V_umbral_min)  # ≈ 0.3094
aR = VR_max / (V_umbral_max - V_umbral_min)  # ≈ 0.5736

# Variables binarias
self.lambda_1 = self.model.addVars(self.T, vtype=GRB.BINARY, name="lambda_1")
self.lambda_2 = self.model.addVars(self.T, vtype=GRB.BINARY, name="lambda_2")
self.lambda_3 = self.model.addVars(self.T, vtype=GRB.BINARY, name="lambda_3")

for t in self.T:
    # Un solo tramo activo
    self.model.addConstr(
        self.lambda_1[t] + self.lambda_2[t] + self.lambda_3[t] == 1)
    
    # Límites de tramos
    self.model.addConstr(
        self.V_30Nov[t] <= V_umbral_min + M_grande * (1 - self.lambda_1[t]))
    # ... más restricciones
    
    # Cálculo de ve_0
    self.model.addConstr(
        self.ve_0[1, t] == 
        self.lambda_1[t] * 0 +
        self.lambda_2[t] * aR * (self.V_30Nov[t] - V_umbral_min) +
        self.lambda_3[t] * VR_max)
```

## Impacto en Variables Binarias

**Variables binarias añadidas:** 3 × 5 temporadas = 15 variables binarias

Esto es mucho menos que las miles de variables binarias que se eliminaron al remover:
- Variables de cota `ca[k,w,t]`
- Variables de incumplimiento `eta[d,j,w,t]`
- Variables de decisión `alpha[w,t]`
- Variables de umbral `beta[w,t]`

## Notas de Implementación

1. **Big-M:** Se usa `M_grande = V_MAX × 10` para asegurar que las restricciones Big-M no sean limitantes cuando el tramo no está activo

2. **Encadenamiento Temporal:** La restricción `V_30Nov[t] = V[32, t-1]` para t > 1 asegura la continuidad entre temporadas

3. **No Requiere Preprocesamiento:** El archivo `preprocesar_volumenes_uso.py` ahora es opcional y solo sirve para análisis preliminar

## Archivo de Preprocesamiento (Opcional)

El archivo `preprocesar_volumenes_uso.py` se mantiene para:
- Análisis preliminar de escenarios
- Validación de cálculos
- Generación de reportes sobre el Convenio

Pero **NO** se usa en el modelo de optimización principal.
