# Análisis Comparativo: Modelo Implementado vs Formulación LaTeX

## 🔍 RESUMEN EJECUTIVO

**Estado General**: El modelo implementado en Python/Gurobi **NO coincide exactamente** con la formulación matemática del documento LaTeX. Existen diferencias significativas en la metodología de linealización y en la estructura de variables.

---

## 📊 DIFERENCIAS PRINCIPALES

### 1. **MÉTODO DE LINEALIZACIÓN DE VOLÚMENES**

#### LaTeX (Método de Zonas con Variables Delta):
```
Variables:
- φ[k,w,t] ∈ {0,1}: Zona k completa en semana w
- Δf[k,w,t]: Filtración incremental en zona k
- Δvr[k,t], Δvg[k,t]: Volumen de uso incremental

Restricciones:
qf[w,t] = f₁ + Σ Δf[k,w,t]
Δf[k,w,t] ≤ f[k+1] - f[k]
Δf[k,w,t] ≥ φ[k,w,t](f[k+1] - f[k])
V[w,t] = v₁ + Σ((v[k+1]-v[k])/(f[k+1]-f[k])) · Δf[k,w,t]
```

#### Implementación Python (Método de Cotas con Big-M):
```python
Variables:
- ca[k,w,t] ∈ {0,1}: Cota activa k en semana w
- V[w,t]: Volumen continuo
- qf[w,t]: Filtración continua

Restricciones:
# Cota única activa
Σ ca[k,w,t] = 1  ∀w,t

# Big-M para volumen
V[w,t] ≤ VC[k+1] + M(1 - ca[k,w,t])  ∀k,w,t
V[w,t] ≥ VC[k] - M(1 - ca[k,w,t])    ∀k,w,t

# Filtración directa
qf[w,t] = Σ ca[k,w,t] · FC[k]  ∀w,t
```

**🔴 DIFERENCIA CRÍTICA**: 
- LaTeX usa **linealización progresiva con deltas** (más precisa, permite volúmenes intermedios)
- Python usa **Big-M con selección de cota única** (más simple, pero fuerza volumen exacto en cotas discretas)

---

### 2. **VARIABLES DE VOLÚMENES DISPONIBLES**

#### LaTeX:
```
VR[0,t]: Volumen inicial de riego temporada t
VR[w,t]: Volumen disponible riego semana w
VG[0,t]: Volumen inicial generación temporada t
VG[w,t]: Volumen disponible generación semana w
```

#### Python:
```python
ve[u,w,t]: Volumen disponible por uso u (u=1: riego, u=2: generación)
ve_0[u,t]: Volumen inicial por uso
qe[u,w,t]: Caudal extraído por uso
```

**✅ EQUIVALENCIA**: Las variables Python son equivalentes usando indexación por uso `u`.

---

### 3. **BALANCE DE VOLUMEN DEL LAGO**

#### LaTeX:
```
V[w,1] = V[w-1,1] + (QA[1,w,1] - qg[1,w,1] - qf[w,1]) · FS[w]/10⁶
V[1,t] = V[48,t-1] + (QA[1,1,t] - qg[1,1,t] - qf[1,t]) · FS[1]/10⁶
V[w,t] = V[w-1,t] + (QA[1,w,t] - qg[1,w,t] - qf[w,t]) · FS[w]/10⁶
```

#### Python:
```python
if w == 1:
    if t == 1:
        V[w,t] == V_0 + (QA[1,w,t] - qg[1,w,t] - qf[w,t]) * FS[w] / 1000000
    else:
        V[w,t] == V[48,t-1] + (QA[1,w,t] - qg[1,w,t] - qf[w,t]) * FS[w] / 1000000
else:
    V[w,t] == V[w-1,t] + (QA[1,w,t] - qg[1,w,t] - qf[w,t]) * FS[w] / 1000000
```

**✅ COINCIDE PERFECTAMENTE** (excepto notación V_0 vs V[0,1])

---

### 4. **VOLUMEN MÍNIMO DEL LAGO**

#### LaTeX:
```
V[w,t] ≥ 1400 - M · β[w,t]
```

#### Python:
```python
V[w,t] >= V_min - M_bigM * beta[w,t]
# Donde V_min = 1400 (parámetro)
```

**✅ COINCIDE EXACTAMENTE**

---

### 5. **BALANCE DE FLUJO EN REDES**

#### LaTeX (Formulación General):
```
Σ qg[i∈Ωᵢₙ(n)] + Σ qv[i∈Ωᵢₙ(n)] + QA[Ωₐfₗ(n)] = 
Σ qg[i∈Ωₒᵤₜ(n)] + Σ qv[i∈Ωₒᵤₜ(n)] + Σ qp[d,Ωᵣᵢₑgₒ(n)]
∀n ∈ N, ∀w,t
```

#### Python (Balances Específicos):
```python
# ABANICO (Central 2)
qg[2,w,t] == QA[2,w,t] + qg[16,w,t] - qv[2,w,t]
Σ qp[d,4,w,t] == qg[2,w,t] + qv[2,w,t]

# ANTUCO (Central 3)
qg[3,w,t] == QA[3,w,t] + qg[1,w,t] + qg[2,w,t] + qv[2,w,t] - qv[3,w,t]

# RIEZACO (j=1)
Σ qp[d,1,w,t] == qg[3,w,t] + qv[3,w,t] - qv[4,w,t]

# ... (continúa para cada nodo)
```

**🟡 EQUIVALENTE PERO DIFERENTE ESTRUCTURA**:
- LaTeX usa **formulación abstracta con conjuntos topológicos**
- Python usa **balances nodo por nodo explícitamente**
- Ambos representan la misma red física, pero Python es más explícito

---

### 6. **RESTRICCIONES DE RIEGO Y BIG-M**

#### LaTeX:
```
QD[d,j,w] - qp[d,j,w,t] = def[d,j,w,t] - sup[d,j,w,t]

def[d,1,w,t] ≤ M · η[d,1,w,t]  (d ∈ {2,3})
def[1,1,w,t] ≤ M(η[1,1,w,t] + α[w,t])  (RieZaco)
def[1,4,w,t] ≤ M(1 + η[1,4,w,t] - α[w,t])  (Abanico)
def[d,3,w,t] ≤ M · η[d,3,w,t]  (Saltos)
def[d,2,w,t] ≤ M · η[d,2,w,t]  (Tucapel)
def[1,2,w,t] ≤ M(η[1,2,w,t] + α[w,t])  (Tucapel 1ros)
```

#### Python:
```python
QD[(d,j,w)] - qp[d,j,w,t] == deficit[d,j,w,t] - superavit[d,j,w,t]

# Canal Abanico (j=4)
deficit[1,4,w,t] <= M_bigM * (1 + eta[1,4,w,t] - alpha[w,t])
deficit[d,4,w,t] <= M_bigM * eta[d,4,w,t]  (d ∈ {2,3})

# Canal RieZaCo (j=1)
deficit[1,1,w,t] <= M_bigM * (eta[1,1,w,t] + alpha[w,t])
deficit[d,1,w,t] <= M_bigM * eta[d,1,w,t]  (d ∈ {2,3})

# ... (similar para j=2,3)
```

**✅ COINCIDE EXACTAMENTE** en estructura lógica

---

### 7. **ENERGÍA GENERADA**

#### LaTeX:
```
GEN[i,t] = Σ_w qg[i,w,t] · ρᵢ · FS[w]/(3600·1000)
```

#### Python:
```python
GEN[i,t] == Σ_w (qg[i,w,t] * rho[i] * FS[w] / (3600 * 1000))
```

**✅ COINCIDE EXACTAMENTE**

---

### 8. **FUNCIÓN OBJETIVO**

#### LaTeX:
```
max Σᵢ Σₜ GEN[i,t] - Σₜ Σ_w Σ_d Σⱼ η[d,j,w,t]·ψ - Σₜ Σ_w β[w,t]·ν
```

#### Python:
```python
max (
    Σᵢ Σₜ GEN[i,t] 
    - Σ_d Σⱼ Σ_w Σₜ eta[d,j,w,t]*psi 
    - Σ_w Σₜ beta[w,t]*phi
)
```

**✅ COINCIDE EXACTAMENTE** (nota: ν en LaTeX = phi en Python, ψ en LaTeX = psi en Python)

---

## 📋 TABLA COMPARATIVA DE NOMENCLATURA

| Concepto | LaTeX | Python | Coincide |
|----------|-------|--------|----------|
| Filtraciones | f_k | FC[k] | ✅ |
| Volúmenes | v_k | VC[k] | ✅ |
| Vol. riego | vr_k | VUC[(1,k)] | ✅ |
| Vol. generación | vg_k | VUC[(2,k)] | ✅ |
| Afluentes | QA_{a,w,t} | QA[(a,w,t)] | ✅ |
| Demandas | QD_{d,j,w} | QD[(d,j,w)] | ✅ |
| Rendimiento | ρ_i | rho[i] | ✅ |
| Costo convenio | ψ | psi | ✅ |
| Costo umbral | ν | phi | ✅ |
| Zona completa | φ_{k,w,t} | **NO EXISTE** | ❌ |
| Cota activa | **NO EXISTE** | ca[k,w,t] | ❌ |
| Delta filtración | Δf_{k,w,t} | **NO EXISTE** | ❌ |
| Delta vol. riego | Δvr_{k,t} | **NO EXISTE** | ❌ |
| Delta vol. gen. | Δvg_{k,t} | **NO EXISTE** | ❌ |

---

## 🎯 CONCLUSIONES

### ✅ **ASPECTOS QUE COINCIDEN:**
1. Balance hídrico del lago
2. Restricciones de convenio y Big-M
3. Definición de energía generada
4. Función objetivo
5. Volumen mínimo del lago
6. Capacidades de centrales
7. Balance de flujos (estructura equivalente)

### ❌ **DIFERENCIAS CRÍTICAS:**

1. **Método de Linealización**: 
   - LaTeX usa **linealización progresiva con variables delta** (φ, Δf, Δvr, Δvg)
   - Python usa **selección de cota única con Big-M** (ca)
   
2. **Precisión del Modelo**:
   - LaTeX permite volúmenes **intermedios entre cotas** (más realista)
   - Python fuerza volúmenes **exactamente en las cotas discretas** K (menos preciso)

3. **Complejidad Computacional**:
   - LaTeX: Más variables binarias (φ por cada k,w,t) pero linealización más precisa
   - Python: Menos variables binarias (ca única) pero necesita Big-M (numericamente menos estable)

4. **Formulación de Red**:
   - LaTeX: Abstracta con conjuntos topológicos Ω
   - Python: Explícita nodo por nodo

---

## 🔧 RECOMENDACIONES

### Para alinear el modelo implementado con LaTeX:

1. **Implementar variables φ y deltas**:
   ```python
   phi = model.addVars(K, W, T, vtype=GRB.BINARY)
   delta_f = model.addVars(K, W, T, lb=0)
   delta_vr = model.addVars(K, T, lb=0)
   delta_vg = model.addVars(K, T, lb=0)
   ```

2. **Reemplazar restricciones de cota por linealización progresiva**:
   ```python
   # En lugar de ca con Big-M
   qf[w,t] == FC[1] + gp.quicksum(delta_f[k,w,t] for k in K)
   delta_f[k,w,t] <= FC[k+1] - FC[k]
   delta_f[k,w,t] >= phi[k,w,t] * (FC[k+1] - FC[k])
   ```

3. **Mantener la formulación de red explícita** (más clara para debugging)

### Si se mantiene la implementación actual:

✅ **VENTAJAS**:
- Más simple de entender y debuggear
- Menos variables binarias
- Funciona correctamente si K tiene suficientes cotas

⚠️ **LIMITACIONES**:
- Menos preciso para volúmenes intermedios
- Dependiente de la calidad de discretización K
- Big-M puede causar problemas numéricos

---

## 📊 MÉTRICAS DEL MODELO ACTUAL

```
Variables totales:      40,403
  - Continuas:          17,855
  - Binarias:           22,548
Restricciones totales:  53,345

Dimensiones:
  T = 5 temporadas
  W = 48 semanas
  K = 78 cotas
  I = 16 centrales
  J = 4 canales
  D = 3 demandas
```

---

**Fecha de análisis**: 18 de noviembre, 2025  
**Modelo implementado**: `modelo_laja_5temporadas.py`  
**Documento de referencia**: Formulación LaTeX proporcionada
