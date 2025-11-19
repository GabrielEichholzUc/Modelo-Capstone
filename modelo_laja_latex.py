"""
Modelo de Optimización - Convenio Hidroeléctricas y Riegos Cuenca Laja
Formulación según documento LaTeX (Linealización por Zonas)
Maximizar generación sujeto a cumplir compromisos de riego
Horizonte: 5 Temporadas
Solver: Gurobi
"""

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

class ModeloLajaLatex:
    def __init__(self):
        """
        Inicializa el modelo de optimización para la cuenca del Laja
        Siguiendo formulación LaTeX con linealización por zonas
        """
        self.model = gp.Model("Convenio_Laja_5Temporadas_LaTeX")
        
        # Conjuntos
        self.S = None  # Simulaciones
        self.T = list(range(1, 6))  # Temporadas (1-5)
        self.W = list(range(1, 49))  # Semanas hidrológicas por temporada
        self.D = [1, 2, 3]  # Demandas (1:Primeros, 2:Segundos, 3:Saltos del Laja)
        self.I = list(range(1, 17))  # Centrales (1-16)
        self.J = [1, 2, 3, 4]  # Puntos de retiro (1:RieZaCo, 2:RieTucapel, 3:RieSaltos, 4:Abanico)
        self.A = list(range(1, 7))  # Afluentes (1:ElToro, 2:Abanico, 3:Antuco, 4:Tucapel, 5:Canecol, 6:Laja_I)
        self.K = None  # Zonas de linealización (se definirá con datos)
        
        # Parámetros
        self.V_30Nov_1 = None  # V_{30Nov,1}: Volumen al 30 Nov previo a temporada 1 [hm³]
        self.V_0 = None  # V_0: Volumen al inicio de la planificación [hm³]
        self.V_MIN = None  # V_MIN: Volumen mínimo del lago [hm³]
        self.V_MAX = None  # V_MAX: Volumen máximo del lago [hm³]
        self.V_F = None  # V_F: Volumen final esperado al término del horizonte [hm³]
        self.f_k = {}  # f_k: Filtraciones en zona k [m³/s]
        self.v_k = {}  # v_k: Volumen en zona k [hm³]
        self.vr_k = {}  # vr_k: Volumen de uso de riego en zona k [hm³]
        self.vg_k = {}  # vg_k: Volumen de uso de generación en zona k [hm³]
        self.QA = {}  # QA_{a,w,t}: Caudal afluente a en semana w de temporada t [m³/s]
        self.QD = {}  # QD_{d,j,w}: Caudal demandado por d en canal j en semana w [m³/s]
        self.gamma = {}  # γ_i: Caudal máximo central i [m³/s]
        self.rho = {}  # ρ_i: Rendimiento central i [MW/(m³/s)]
        self.FS = {}  # FS_w: Factor segundos en semana w [segundos]
        self.psi = None  # ψ: Costo incumplir convenio [GWh]
        self.nu = None  # ν: Costo bajar umbral de V_MIN [GWh]
        self.M_bigM = None  # Parámetro Big-M
        
        # Variables (Formulación LaTeX)
        self.V = {}  # V_{w,t}: Volumen del lago al final de semana w, temporada t [hm³]
        self.V_30Nov = {}  # V_30Nov_{t}: Volumen del lago al 30 Nov (inicio temporada t) [hm³]
        
        # Variables de linealización (zonas)
        self.phi_var = {}  # φ_{k,w,t}: Binaria, 1 si zona k completa en semana w, temporada t
        self.phi_30 = {}  # φ_30_{k,t}: Binaria para linealización al 30 Nov
        self.delta_f = {}  # Δf_{k,w,t}: Filtración incremental en zona k [m³/s]
        self.delta_v30 = {}  # Δv30_{k,t}: Incremento de volumen al 30 Nov en zona k, temporada t [hm³]
        
        # Volúmenes disponibles
        self.VR = {}  # VR_{w,t}: Volumen disponible para riego [hm³]
        self.VR_0 = {}  # VR_{0,t}: Volumen inicial riego temporada t [hm³]
        self.VG = {}  # VG_{w,t}: Volumen disponible para generación [hm³]
        self.VG_0 = {}  # VG_{0,t}: Volumen inicial generación temporada t [hm³]
        
        # Caudales
        self.qer = {}  # qer_{w,t}: Caudal extraído para riego [m³/s]
        self.qeg = {}  # qeg_{w,t}: Caudal extraído para generación [m³/s]
        self.qf = {}  # qf_{w,t}: Caudal de filtración [m³/s]
        self.qg = {}  # qg_{i,w,t}: Caudal generación central i [m³/s]
        self.qv = {}  # qv_{i,w,t}: Caudal vertimiento central i [m³/s]
        self.qp = {}  # qp_{d,j,w,t}: Caudal provisto para demanda d en canal j [m³/s]
        
        # Déficit y superávit
        self.deficit = {}  # def_{d,j,w,t}: Déficit de riego [m³/s]
        self.superavit = {}  # sup_{d,j,w,t}: Superávit de riego [m³/s]
        
        # Variables binarias de decisión
        self.eta = {}  # η_{d,j,w,t}: Binaria incumplimiento convenio
        self.alpha = {}  # α_{w,t}: Binaria Abanico(1) vs Tucapel(0)
        self.beta = {}  # β_{w,t}: Binaria bajar de V_MIN
        self.delta = {}  # δ_{w,t}: Binaria sobrepasar V_MAX
        
        # Energía generada
        self.GEN = {}  # GEN_{i,t}: Energía generada [GWh] por central i en temporada t
        
    def cargar_parametros(self, dict_parametros):
        """Carga los parámetros del modelo"""
        self.V_30Nov_1 = dict_parametros.get('V_30Nov_1', dict_parametros.get('V_30Nov'))
        self.V_0 = dict_parametros.get('V_0')
        self.V_MIN = dict_parametros.get('V_MIN', 1400)
        self.V_MAX = dict_parametros.get('V_MAX')
        self.V_F = dict_parametros.get('V_F', 1400)
        
        # Cargar filtraciones, volúmenes y volúmenes de uso
        FC_dict = dict_parametros.get('FC', {})
        VC_dict = dict_parametros.get('VC', {})
        VUC_dict = dict_parametros.get('VUC', {})
        
        # Convertir a formato LaTeX (f_k, v_k, vr_k, vg_k)
        K_list = sorted(FC_dict.keys())
        self.K = list(range(1, len(K_list) + 1))  # Zonas 1, 2, ..., K
        
        for idx, k_original in enumerate(K_list):
            k = idx + 1  # Zona 1-indexada
            self.f_k[k] = FC_dict[k_original]
            self.v_k[k] = VC_dict[k_original]
            self.vr_k[k] = VUC_dict.get((1, k_original), 0)  # Riego (u=1)
            self.vg_k[k] = VUC_dict.get((2, k_original), 0)  # Generación (u=2)
        
        self.QA = dict_parametros.get('QA', {})
        self.QD = dict_parametros.get('QD', {})
        self.gamma = dict_parametros.get('gamma', {})
        self.rho = dict_parametros.get('rho', {})
        self.FS = dict_parametros.get('FS', {})
        self.psi = dict_parametros.get('psi', 1000)
        self.nu = dict_parametros.get('nu', dict_parametros.get('phi', 1000))  # ν en LaTeX
        self.M_bigM = dict_parametros.get('M', 10000)
        
        print("✓ Parámetros cargados correctamente (Formulación LaTeX)")
        print(f"  Zonas de linealización: {len(self.K)}")
        
    def crear_variables(self):
        """Crea todas las variables según formulación LaTeX"""
        print("Creando variables de decisión (Formulación LaTeX)...")
        
        K_zonas = self.K[:-1]  # Zonas 1 a K-1 (la última zona no necesita variables delta)
        
        # Volúmenes del lago (sin límite superior estricto, controlado por delta)
        self.V = self.model.addVars(self.W, self.T, lb=0, name="V")
        
        # Volumen al 30 de Noviembre (inicio de cada temporada)
        self.V_30Nov = self.model.addVars(self.T, lb=0, name="V_30Nov")
        
        # Variables de linealización (phi y deltas)
        self.phi_var = self.model.addVars(K_zonas, self.W, self.T, vtype=GRB.BINARY, name="phi")
        self.phi_30 = self.model.addVars(K_zonas, self.T, vtype=GRB.BINARY, name="phi_30")
        self.delta_f = self.model.addVars(K_zonas, self.W, self.T, lb=0, name="delta_f")
        self.delta_v30 = self.model.addVars(K_zonas, self.T, lb=0, name="delta_v30")
        
        # Volúmenes disponibles por uso
        self.VR_0 = self.model.addVars(self.T, lb=0, name="VR_0")
        self.VR = self.model.addVars(self.W, self.T, lb=0, name="VR")
        self.VG_0 = self.model.addVars(self.T, lb=0, name="VG_0")
        self.VG = self.model.addVars(self.W, self.T, lb=0, name="VG")
        
        # Caudales
        self.qer = self.model.addVars(self.W, self.T, lb=0, name="qer")
        self.qeg = self.model.addVars(self.W, self.T, lb=0, name="qeg")
        self.qf = self.model.addVars(self.W, self.T, lb=0, name="qf")
        self.qg = self.model.addVars(self.I, self.W, self.T, lb=0, name="qg")
        self.qv = self.model.addVars(self.I, self.W, self.T, lb=0, name="qv")
        self.qp = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="qp")
        
        # Déficit y superávit
        self.deficit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="deficit")
        self.superavit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="superavit")
        
        # Variables binarias
        self.eta = self.model.addVars(self.D, self.J, self.W, self.T, vtype=GRB.BINARY, name="eta")
        self.alpha = self.model.addVars(self.W, self.T, vtype=GRB.BINARY, name="alpha")
        self.beta = self.model.addVars(self.W, self.T, vtype=GRB.BINARY, name="beta")
        self.delta = self.model.addVars(self.W, self.T, vtype=GRB.BINARY, name="delta")
        
        # Energía generada
        self.GEN = self.model.addVars(self.I, self.T, lb=0, name="GEN")
        
        print("✓ Variables creadas correctamente")
        print(f"  Variables phi (filtraciones): {len(K_zonas) * 48 * 5:,}")
        print(f"  Variables phi_30 (30 Nov): {len(K_zonas) * 5:,}")
        print(f"  Variables delta_f: {len(K_zonas) * 48 * 5:,}")
        print(f"  Variables delta_v30: {len(K_zonas) * 5:,}")

    def crear_restricciones(self):
        """Crea todas las restricciones según formulación LaTeX"""
        print("\nCreando restricciones (Formulación LaTeX)...")
        
        K_zonas = self.K[:-1]  # Zonas 1 a K-1
        
        # ========== 1. DEFINICIÓN DE FILTRACIONES ==========
        print("  1. Definición de filtraciones...")
        for t in self.T:
            for w in self.W:
                # qf[w,t] = f_1 + Σ delta_f[k,w,t]
                self.model.addConstr(
                    self.qf[w, t] == self.f_k[1] + gp.quicksum(
                        self.delta_f[k, w, t] for k in K_zonas
                    ),
                    name=f"def_qf_{w}_{t}")
                
                for k in K_zonas:
                    f_k = self.f_k[k]
                    f_k_next = self.f_k[k + 1]
                    
                    # Δf[k,w,t] ≤ f_{k+1} - f_k
                    self.model.addConstr(
                        self.delta_f[k, w, t] <= f_k_next - f_k,
                        name=f"delta_f_upper_{k}_{w}_{t}")
                    
                    # Δf[k,w,t] ≥ φ[k,w,t] * (f_{k+1} - f_k)
                    self.model.addConstr(
                        self.delta_f[k, w, t] >= self.phi_var[k, w, t] * (f_k_next - f_k),
                        name=f"delta_f_lower_{k}_{w}_{t}")
                    
                    # Δf[k,w,t] ≤ φ[k-1,w,t] * (f_{k+1} - f_k)  (si k > 1)
                    if k > 1:
                        self.model.addConstr(
                            self.delta_f[k, w, t] <= self.phi_var[k-1, w, t] * (f_k_next - f_k),
                            name=f"delta_f_prev_{k}_{w}_{t}")
                    else:
                        # Para k=1, φ[0] = 1 implícito
                        pass
                
                # V[w,t] = v_1 + Σ ((v_{k+1} - v_k)/(f_{k+1} - f_k)) * Δf[k,w,t]
                v_expr = self.v_k[1]
                for k in K_zonas:
                    v_k = self.v_k[k]
                    v_k_next = self.v_k[k + 1]
                    f_k = self.f_k[k]
                    f_k_next = self.f_k[k + 1]
                    
                    if abs(f_k_next - f_k) > 1e-6:
                        coef = (v_k_next - v_k) / (f_k_next - f_k)
                        v_expr += coef * self.delta_f[k, w, t]
                
                # V[w,t] definido por filtración para TODAS las semanas
                self.model.addConstr(
                    self.V[w, t] == v_expr,
                    name=f"vol_from_f_{w}_{t}")
        
        # ========== 2. DEFINICIÓN DE VOLÚMENES DE RIEGO Y GENERACIÓN (30 NOV) ==========
        print("  2. Volúmenes disponibles de riego y generación (30 Nov)...")
        
        # Definir V_30Nov[t] para cada temporada
        for t in self.T:
            if t == 1:
                # V_30Nov[1] = V_30Nov_1 (parámetro conocido)
                self.model.addConstr(
                    self.V_30Nov[t] == self.V_30Nov_1,
                    name=f"def_V30Nov_1")
            else:
                # V_30Nov[t] = V[32, t-1] (volumen al 30 Nov de temporada anterior)
                self.model.addConstr(
                    self.V_30Nov[t] == self.V[32, t-1],
                    name=f"def_V30Nov_{t}")
        
        # Linealización CONJUNTA de V_30Nov[t], VR_0[t] y VG_0[t]
        # Todas usan las MISMAS variables Δv30[k,t] y φ_30[k,t]
        for t in self.T:
            # V_30Nov[t] = v_1 + Σ (v_{k+1} - v_k) × Δv30[k,t]
            v_expr = self.v_k[1]
            for k in K_zonas:
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                v_expr += (v_k_next - v_k) * self.delta_v30[k, t]
            
            self.model.addConstr(
                self.V_30Nov[t] == v_expr,
                name=f"V30Nov_from_v_{t}")
            
            # VR_0[t] = vr_1 + Σ (vr_{k+1} - vr_k) × Δv30[k,t]
            vr_expr = self.vr_k[1]
            for k in K_zonas:
                vr_k = self.vr_k[k]
                vr_k_next = self.vr_k[k + 1]
                vr_expr += (vr_k_next - vr_k) * self.delta_v30[k, t]
            
            self.model.addConstr(
                self.VR_0[t] == vr_expr,
                name=f"VR0_from_v_{t}")
            
            # VG_0[t] = vg_1 + Σ (vg_{k+1} - vg_k) × Δv30[k,t]
            vg_expr = self.vg_k[1]
            for k in K_zonas:
                vg_k = self.vg_k[k]
                vg_k_next = self.vg_k[k + 1]
                vg_expr += (vg_k_next - vg_k) * self.delta_v30[k, t]
            
            self.model.addConstr(
                self.VG_0[t] == vg_expr,
                name=f"VG0_from_v_{t}")
            
            # Restricciones de linealización para Δv30[k,t]
            for k in K_zonas:
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                
                # Δv30[k,t] ≤ v_{k+1} - v_k
                self.model.addConstr(
                    self.delta_v30[k, t] <= v_k_next - v_k,
                    name=f"delta_v30_upper_{k}_{t}")
                
                # Δv30[k,t] ≥ φ_30[k,t] * (v_{k+1} - v_k)
                self.model.addConstr(
                    self.delta_v30[k, t] >= self.phi_30[k, t] * (v_k_next - v_k),
                    name=f"delta_v30_lower_{k}_{t}")
                
                # Δv30[k,t] ≤ φ_30[k-1,t] * (v_{k+1} - v_k)
                if k > 1:
                    self.model.addConstr(
                        self.delta_v30[k, t] <= self.phi_30[k-1, t] * (v_k_next - v_k),
                        name=f"delta_v30_prev_{k}_{t}")
                # Para k=1, φ_30[0,t] = 1 implícito (siempre se incluye zona base)
        
        # ========== 3. GENERACIÓN EN EL TORO ==========
        print("  3. Generación en El Toro...")
        for t in self.T:
            for w in self.W:
                # qg[1,w,t] = qer[w,t] + qeg[w,t]
                self.model.addConstr(
                    self.qg[1, w, t] == self.qer[w, t] + self.qeg[w, t],
                    name=f"gen_eltoro_{w}_{t}")
        
        # ========== 4. BALANCE DE VOLUMEN EN EL LAGO ==========
        print("  4. Balance de volumen del lago...")
        for t in self.T:
            for w in self.W:
                if w == 1 and t == 1:
                    # V[1,1] = V_0 + (QA[1,1,1] - qg[1,1,1] - qf[1,1]) * FS[1] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V_0 + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                        name=f"balance_vol_11")
                elif w == 1 and t > 1:
                    # V[1,t] = V[48,t-1] + (QA[1,1,t] - qg[1,1,t] - qf[1,t]) * FS[1] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V[48, t-1] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                        name=f"balance_vol_1{t}")
                else:
                    # V[w,t] = V[w-1,t] + (QA[1,w,t] - qg[1,w,t] - qf[w,t]) * FS[w] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V[w-1, t] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                        name=f"balance_vol_{w}_{t}")
        
        # ========== 5. VOLÚMENES MÍNIMOS Y MÁXIMOS DEL LAGO ==========
        print("  5. Volúmenes mínimos y máximos del lago...")
        for t in self.T:
            for w in self.W:
                # V[w,t] ≥ V_MIN - M * β[w,t]
                self.model.addConstr(
                    self.V[w, t] >= self.V_MIN - self.M_bigM * self.beta[w, t],
                    name=f"vol_min_{w}_{t}")
                
                # V[w,t] ≤ V_MAX + M * δ[w,t]
                self.model.addConstr(
                    self.V[w, t] <= self.V_MAX + self.M_bigM * self.delta[w, t],
                    name=f"vol_max_{w}_{t}")
        
        # V[48,5] ≥ V_F (Volumen final esperado)
        self.model.addConstr(
            self.V[48, 5] >= self.V_F,
            name="vol_final")
        
        # ========== 6. INCLUSIÓN DE FILTRACIONES ==========
        print("  6. Inclusión de filtraciones en Laja...")
        for t in self.T:
            for w in self.W:
                # qg[16,w,t] = qf[w,t]
                self.model.addConstr(
                    self.qg[16, w, t] == self.qf[w, t],
                    name=f"laja_filt_{w}_{t}")
        
        # ========== 7. BALANCE DE FLUJO EN REDES (Explícito por nodo) ==========
        print("  7. Balance de flujo en redes...")
        for t in self.T:
            for w in self.W:
                # ABANICO (Central 2)
                self.model.addConstr(
                    self.qg[2, w, t] == self.QA[2, w, t] + self.qg[16, w, t] - self.qv[2, w, t],
                    name=f"abanico_{w}_{t}")
                
                # Distribución a canal Abanico (j=4)
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 4, w, t] for d in self.D) == self.qg[2, w, t] + self.qv[2, w, t],
                    name=f"abanico_canal_{w}_{t}")
                
                # ANTUCO (Central 3)
                self.model.addConstr(
                    self.qg[3, w, t] == self.QA[3, w, t] + self.qg[1, w, t] + self.qg[2, w, t] + self.qv[2, w, t] - self.qv[3, w, t],
                    name=f"antuco_{w}_{t}")
                
                # RIEZACO (Canal j=1)
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 1, w, t] for d in self.D) == self.qg[3, w, t] + self.qv[3, w, t] - self.qv[4, w, t],
                    name=f"riezaco_{w}_{t}")
                
                # CANECOL (Central 5)
                self.model.addConstr(
                    self.qg[5, w, t] == self.QA[5, w, t] - self.qv[5, w, t],
                    name=f"canecol_{w}_{t}")
                
                # CANRUCUE (Central 6)
                self.model.addConstr(
                    self.qg[6, w, t] == self.qv[5, w, t] - self.qv[6, w, t],
                    name=f"canrucue_{w}_{t}")
                
                # CLAJRUCUE (Central 7)
                self.model.addConstr(
                    self.qg[7, w, t] == self.qv[4, w, t] - self.qv[7, w, t],
                    name=f"clajrucue_{w}_{t}")
                
                # RUCUE (Central 8)
                self.model.addConstr(
                    self.qg[8, w, t] == self.qg[6, w, t] + self.qg[7, w, t] - self.qv[8, w, t],
                    name=f"rucue_{w}_{t}")
                
                # QUILLECO (Central 9)
                self.model.addConstr(
                    self.qg[9, w, t] == self.qg[8, w, t] + self.qv[8, w, t] - self.qv[9, w, t],
                    name=f"quilleco_{w}_{t}")
                
                # TUCAPEL (Central 10)
                self.model.addConstr(
                    self.qg[10, w, t] == self.qg[5, w, t] + self.qv[6, w, t] + self.qv[7, w, t] + self.qg[9, w, t] + self.qv[9, w, t] + self.QA[4, w, t] - self.qv[10, w, t],
                    name=f"tucapel_{w}_{t}")
                
                # CANAL LAJA (Central 11)
                self.model.addConstr(
                    self.qg[11, w, t] == self.qg[10, w, t] + self.qv[10, w, t] - self.qv[11, w, t],
                    name=f"canal_laja_{w}_{t}")
                
                # RIESALTOS (Canal j=3)
                self.model.addConstr(
                    self.qp[3, 3, w, t] == self.qv[11, w, t],
                    name=f"riesaltos_{w}_{t}")
                
                # LAJA 1 (Central 13)
                afluente_6 = self.QA.get((6, w, t), 0)
                self.model.addConstr(
                    self.qg[13, w, t] + self.qv[13, w, t] == self.qv[11, w, t] + afluente_6,
                    name=f"laja1_{w}_{t}")
                
                # EL DIUTO (Central 15)
                self.model.addConstr(
                    self.qg[15, w, t] == self.qg[11, w, t] - self.qv[15, w, t],
                    name=f"el_diuto_{w}_{t}")
                
                # RIETUCAPEL (Canal j=2)
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 2, w, t] for d in self.D) == self.qg[15, w, t] + self.qv[15, w, t],
                    name=f"rietucapel_{w}_{t}")
                
                # VERTIMIENTO EL TORO = 0
                self.model.addConstr(
                    self.qv[1, w, t] == 0,
                    name=f"no_vert_eltoro_{w}_{t}")
        
        # ========== 8. CUMPLIMIENTO DE DEMANDAS DE RIEGO ==========
        print("  8. Cumplimiento de demandas de riego...")
        for t in self.T:
            for w in self.W:
                for d in self.D:
                    for j in self.J:
                        # QD[d,j,w] - qp[d,j,w,t] = def[d,j,w,t] - sup[d,j,w,t]
                        self.model.addConstr(
                            self.QD.get((d, j, w), 0) - self.qp[d, j, w, t] == self.deficit[d, j, w, t] - self.superavit[d, j, w, t],
                            name=f"balance_riego_{d}_{j}_{w}_{t}")
        
        # ========== 9. ACTIVACIÓN DE PENALIZACIONES POR CONVENIO ==========
        print("  9. Activación de penalizaciones por convenio...")
        for t in self.T:
            for w in self.W:
                # Canal Abanico (j=4)
                # Primeros regantes: def[1,4,w,t] ≤ M * (1 + η[1,4,w,t] - α[w,t])
                self.model.addConstr(
                    self.deficit[1, 4, w, t] <= self.M_bigM * (1 + self.eta[1, 4, w, t] - self.alpha[w, t]),
                    name=f"bigM_abanico_1_{w}_{t}")
                
                # Segundos y emergencia en Abanico
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 4, w, t] <= self.M_bigM * self.eta[d, 4, w, t],
                        name=f"bigM_abanico_{d}_{w}_{t}")
                
                # Canal RieZaCo (j=1)
                # Primeros regantes: def[1,1,w,t] ≤ M * (η[1,1,w,t] + α[w,t])
                self.model.addConstr(
                    self.deficit[1, 1, w, t] <= self.M_bigM * (self.eta[1, 1, w, t] + self.alpha[w, t]),
                    name=f"bigM_riezaco_1_{w}_{t}")
                
                # Segundos y emergencia en RieZaCo
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 1, w, t] <= self.M_bigM * self.eta[d, 1, w, t],
                        name=f"bigM_riezaco_{d}_{w}_{t}")
                
                # Canal RieTucapel (j=2)
                # Primeros regantes: def[1,2,w,t] ≤ M * (η[1,2,w,t] + α[w,t])
                self.model.addConstr(
                    self.deficit[1, 2, w, t] <= self.M_bigM * (self.eta[1, 2, w, t] + self.alpha[w, t]),
                    name=f"bigM_tucapel_1_{w}_{t}")
                
                # Segundos y emergencia en RieTucapel
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 2, w, t] <= self.M_bigM * self.eta[d, 2, w, t],
                        name=f"bigM_tucapel_{d}_{w}_{t}")
                
                # Canal RieSaltos (j=3)
                for d in self.D:
                    self.model.addConstr(
                        self.deficit[d, 3, w, t] <= self.M_bigM * self.eta[d, 3, w, t],
                        name=f"bigM_saltos_{d}_{w}_{t}")
        
        # ========== 10. CAPACIDADES ==========
        print("  10. Capacidades de centrales...")
        for t in self.T:
            for i in self.I:
                for w in self.W:
                    # qg[i,w,t] ≤ γ_i
                    self.model.addConstr(
                        self.qg[i, w, t] <= self.gamma[i],
                        name=f"cap_max_{i}_{w}_{t}")
        
        # ========== 11. DEFINICIÓN DE ENERGÍA GENERADA ==========
        print("  11. Definición de energía generada...")
        for t in self.T:
            for i in self.I:
                # GEN[i,t] = Σ_w qg[i,w,t] * ρ_i * FS_w / (3600 * 1000)
                self.model.addConstr(
                    self.GEN[i, t] == gp.quicksum(
                        self.qg[i, w, t] * self.rho[i] * self.FS[w] / (3600 * 1000)
                        for w in self.W
                    ),
                    name=f"def_energia_{i}_{t}")
        
        print("✓ Restricciones creadas correctamente")
        
    def crear_funcion_objetivo(self):
        """Define la función objetivo según formulación LaTeX"""
        print("\nCreando función objetivo (Formulación LaTeX)...")
        
        # max Σ_i Σ_t GEN[i,t] - Σ_t Σ_w Σ_d Σ_j η[d,j,w,t]*ψ - Σ_t Σ_w β[w,t]*ν
        generacion_total = gp.quicksum(
            self.GEN[i, t]
            for i in self.I for t in self.T
        )
        
        penalidad_incumplimiento = gp.quicksum(
            self.eta[d, j, w, t] * self.psi
            for d in self.D for j in self.J for w in self.W for t in self.T
        )
        
        penalidad_umbral_min = gp.quicksum(
            self.beta[w, t] * self.nu
            for w in self.W for t in self.T
        )
        
        penalidad_umbral_max = gp.quicksum(
            self.delta[w, t] * self.nu  # Mismo costo para sobrepasar V_MAX
            for w in self.W for t in self.T
        )

        penalidad_alejamiento = gp.quicksum(
            self.deficit[d, j, w, t]
            for d in self.D for j in self.J for w in self.W for t in self.T
        )

        self.model.setObjective(
            generacion_total - penalidad_incumplimiento - penalidad_umbral_min - penalidad_umbral_max - penalidad_alejamiento,
            GRB.MAXIMIZE
        )
        
        print("✓ Función objetivo creada correctamente")
        
    def construir_modelo(self):
        """Construye el modelo completo"""
        print("\n" + "="*70)
        print("CONSTRUYENDO MODELO - FORMULACIÓN LATEX")
        print("="*70 + "\n")
        
        self.crear_variables()
        self.crear_restricciones()
        self.crear_funcion_objetivo()
        
        self.model.update()
        
        print("\n" + "="*70)
        print("MODELO CONSTRUIDO EXITOSAMENTE")
        print("="*70)
        print(f"Temporadas: {len(self.T)}")
        print(f"Variables: {self.model.NumVars:,}")
        print(f"Restricciones: {self.model.NumConstrs:,}")
        print(f"Variables binarias: {self.model.NumBinVars:,}")
        print("="*70 + "\n")
        
    def optimizar(self, time_limit=None, mip_gap=None):
        """Resuelve el modelo"""
        print("\n" + "="*70)
        print("INICIANDO OPTIMIZACIÓN")
        print("="*70 + "\n")
        
        if time_limit:
            self.model.Params.TimeLimit = time_limit
        if mip_gap:
            self.model.Params.MIPGap = mip_gap
        else:
            self.model.Params.MIPGap = 0.02  # 2% por defecto
        
        self.model.optimize()
        
        print("\n" + "="*70)
        print("RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*70)
        
        if self.model.status == GRB.OPTIMAL:
            print("✓ Solución óptima encontrada")
            print(f"Valor objetivo: {self.model.ObjVal:,.2f} GWh")
            print(f"Gap de optimalidad: {self.model.MIPGap*100:.4f}%")
            print(f"Tiempo de resolución: {self.model.Runtime:.2f} segundos")
        elif self.model.status == GRB.TIME_LIMIT:
            print("⚠ Tiempo límite alcanzado")
            if hasattr(self.model, 'ObjVal'):
                print(f"Mejor solución encontrada: {self.model.ObjVal:,.2f} GWh")
                print(f"Gap de optimalidad: {self.model.MIPGap*100:.2f}%")
        else:
            print(f"✗ Estado de optimización: {self.model.status}")
        
        print("="*70 + "\n")
        
    def exportar_resultados(self, carpeta_salida="resultados"):
        """Exporta los resultados a archivos CSV"""
        import os
        
        if self.model.status not in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
            print("No hay solución factible para exportar")
            return
        
        if not hasattr(self.model, 'ObjVal'):
            print("No hay solución factible para exportar")
            return
            
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"\nExportando resultados a carpeta '{carpeta_salida}'...")
        
        # 1. Generación por central
        df_generacion = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Temporada': t, 'Caudal_m3s': self.qg[i, w, t].X}
            for i in self.I for w in self.W for t in self.T
        ])
        df_generacion.to_csv(f"{carpeta_salida}/generacion.csv", index=False)
        
        # 2. Vertimientos
        df_vertimientos = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Temporada': t, 'Caudal_m3s': self.qv[i, w, t].X}
            for i in self.I for w in self.W for t in self.T if self.qv[i, w, t].X > 0.01
        ])
        df_vertimientos.to_csv(f"{carpeta_salida}/vertimientos.csv", index=False)
        
        # 3. Volúmenes del lago
        df_volumenes = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Volumen_hm3': self.V[w, t].X}
            for w in self.W for t in self.T
        ])
        df_volumenes.to_csv(f"{carpeta_salida}/volumenes_lago.csv", index=False)
        
        # 3b. Volúmenes al 30 de Noviembre
        df_v30nov = pd.DataFrame([
            {'Temporada': t, 'V_30Nov_hm3': self.V_30Nov[t].X}
            for t in self.T
        ])
        df_v30nov.to_csv(f"{carpeta_salida}/volumenes_30nov.csv", index=False)
        
        # 3c. Volúmenes disponibles por uso
        df_volumenes_uso = pd.DataFrame([
            {'Temporada': t, 'VR_0_hm3': self.VR_0[t].X, 'VG_0_hm3': self.VG_0[t].X}
            for t in self.T
        ])
        df_volumenes_uso.to_csv(f"{carpeta_salida}/volumenes_por_uso.csv", index=False)
        
        # 4. Riego
        df_riego = pd.DataFrame([
            {
                'Demanda': d,
                'Canal': j,
                'Semana': w,
                'Temporada': t,
                'Demanda_m3s': self.QD.get((d, j, w), 0),
                'Provisto_m3s': self.qp[d, j, w, t].X,
                'Deficit_m3s': self.deficit[d, j, w, t].X,
                'Incumplimiento': self.eta[d, j, w, t].X
            }
            for d in self.D for j in self.J for w in self.W for t in self.T
        ])
        df_riego.to_csv(f"{carpeta_salida}/riego.csv", index=False)
        
        # 5. Variables de decisión
        df_alpha = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Alpha': self.alpha[w, t].X}
            for w in self.W for t in self.T
        ])
        df_alpha.to_csv(f"{carpeta_salida}/decision_alpha.csv", index=False)
        
        df_beta = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Beta': self.beta[w, t].X}
            for w in self.W for t in self.T
        ])
        df_beta.to_csv(f"{carpeta_salida}/decision_beta.csv", index=False)
        
        df_delta = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Delta': self.delta[w, t].X}
            for w in self.W for t in self.T
        ])
        df_delta.to_csv(f"{carpeta_salida}/decision_delta.csv", index=False)
        
        # 6. Energía generada
        df_energia = pd.DataFrame([
            {
                'Central': i,
                'Temporada': t,
                'Energia_GWh': self.GEN[i, t].X,
                'Energia_MWh': self.GEN[i, t].X * 1000
            }
            for i in self.I for t in self.T
        ])
        df_energia.to_csv(f"{carpeta_salida}/energia_total.csv", index=False)
        
        # 7. Variables de linealización (phi)
        K_zonas = self.K[:-1]
        df_phi = pd.DataFrame([
            {'Zona': k, 'Semana': w, 'Temporada': t, 'Phi': self.phi_var[k, w, t].X}
            for k in K_zonas for w in self.W for t in self.T if self.phi_var[k, w, t].X > 0.5
        ])
        if len(df_phi) > 0:
            df_phi.to_csv(f"{carpeta_salida}/phi_zonas.csv", index=False)
        
        # 8. Filtraciones
        df_filtraciones = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Filtracion_m3s': self.qf[w, t].X}
            for w in self.W for t in self.T
        ])
        df_filtraciones.to_csv(f"{carpeta_salida}/filtraciones.csv", index=False)
        
        # 9. Filtraciones incrementales por zona (delta_f)
        df_delta_f = pd.DataFrame([
            {'Zona': k, 'Semana': w, 'Temporada': t, 'Delta_f_m3s': self.delta_f[k, w, t].X}
            for k in K_zonas for w in self.W for t in self.T if self.delta_f[k, w, t].X > 0.001
        ])
        if len(df_delta_f) > 0:
            df_delta_f.to_csv(f"{carpeta_salida}/filtraciones_incrementales.csv", index=False)
        
        print("✓ Resultados exportados exitosamente")
