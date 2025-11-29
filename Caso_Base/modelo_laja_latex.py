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
        self.model = gp.Model("Convenio_Laja_6Temporadas_LaTeX")
        
        # Conjuntos
        self.S = None  # Simulaciones
        self.T = list(range(1, 7))  # Temporadas (1-6)
        self.W = list(range(1, 49))  # Semanas hidrológicas por temporada
        self.D = [1, 2, 3]  # Demandas (1:Primeros, 2:Segundos, 3:Saltos del Laja)
        self.I = list(range(1, 17))  # Centrales (1-16)
        self.J = [1, 2, 3, 4]  # Puntos de retiro (1:RieZaCo, 2:RieTucapel, 3:RieSaltos, 4:Abanico)
        self.A = list(range(1, 7))  # Afluentes (1:ElToro, 2:Abanico, 3:Antuco, 4:Tucapel, 5:Canecol, 6:Laja_I)
        self.K = None  # Zonas de linealización (se definirá con datos)
        
        # Definición de la Topología de Red para Balance de Masa Genérico
        self.ARCOS_RED = [
            # 1. NODO: CENTRAL EL TORO
            {'nodo': 'ElToro', 'tipo': 'in',  'var': 'qer', 'idx': None},
            {'nodo': 'ElToro', 'tipo': 'in',  'var': 'qeg', 'idx': None},
            {'nodo': 'ElToro', 'tipo': 'out', 'var': 'qg', 'idx': 1},
            
            # 2. NODO: ABANICO
            {'nodo': 'Abanico', 'tipo': 'in',  'var': 'qa', 'idx': 2},
            {'nodo': 'Abanico', 'tipo': 'in',  'var': 'qf', 'idx': None},
            {'nodo': 'Abanico', 'tipo': 'out', 'var': 'qg', 'idx': 2},
            {'nodo': 'Abanico', 'tipo': 'out', 'var': 'qv', 'idx': 2},
            
            # 3. NODO: ANTUCO
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qa', 'idx': 3},
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qg', 'idx': 1},
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qg', 'idx': 2},
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qv', 'idx': 2},
            {'nodo': 'Antuco', 'tipo': 'out', 'var': 'qg', 'idx': 3},
            {'nodo': 'Antuco', 'tipo': 'out', 'var': 'qv', 'idx': 3},
            
            # 4. NODO: RIEZACO
            {'nodo': 'RieZaco', 'tipo': 'in',  'var': 'qg', 'idx': 3},
            {'nodo': 'RieZaco', 'tipo': 'in',  'var': 'qv', 'idx': 3},
            {'nodo': 'RieZaco', 'tipo': 'out', 'var': 'qp_sum', 'idx': 1},
            {'nodo': 'RieZaco', 'tipo': 'out', 'var': 'qv', 'idx': 4},
            
            # 5. NODO: CANECOL
            {'nodo': 'Canecol', 'tipo': 'in',  'var': 'qa', 'idx': 5},
            {'nodo': 'Canecol', 'tipo': 'out', 'var': 'qg', 'idx': 5},
            {'nodo': 'Canecol', 'tipo': 'out', 'var': 'qv', 'idx': 5},
            
            # 6. NODO: CANRUCUE
            {'nodo': 'CanRucue', 'tipo': 'in',  'var': 'qv', 'idx': 5},
            {'nodo': 'CanRucue', 'tipo': 'out', 'var': 'qg', 'idx': 6},
            {'nodo': 'CanRucue', 'tipo': 'out', 'var': 'qv', 'idx': 6},
            
            # 7. NODO: CLAJRUCUE
            {'nodo': 'CLajRucue', 'tipo': 'in',  'var': 'qv', 'idx': 4},
            {'nodo': 'CLajRucue', 'tipo': 'out', 'var': 'qg', 'idx': 7},
            {'nodo': 'CLajRucue', 'tipo': 'out', 'var': 'qv', 'idx': 7},
            
            # 8. NODO: RUCUE
            {'nodo': 'Rucue', 'tipo': 'in',  'var': 'qg', 'idx': 6},
            {'nodo': 'Rucue', 'tipo': 'in',  'var': 'qg', 'idx': 7},
            {'nodo': 'Rucue', 'tipo': 'out', 'var': 'qg', 'idx': 8},
            {'nodo': 'Rucue', 'tipo': 'out', 'var': 'qv', 'idx': 8},
            
            # 9. NODO: QUILLECO
            {'nodo': 'Quilleco', 'tipo': 'in',  'var': 'qg', 'idx': 8},
            {'nodo': 'Quilleco', 'tipo': 'in',  'var': 'qv', 'idx': 8},
            {'nodo': 'Quilleco', 'tipo': 'out', 'var': 'qg', 'idx': 9},
            {'nodo': 'Quilleco', 'tipo': 'out', 'var': 'qv', 'idx': 9},
            
            # 10. NODO: TUCAPEL
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qa', 'idx': 4},
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qg', 'idx': 5},
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 6},
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 7},
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qg', 'idx': 9},
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 9},
            {'nodo': 'Tucapel', 'tipo': 'out', 'var': 'qg', 'idx': 10},
            {'nodo': 'Tucapel', 'tipo': 'out', 'var': 'qv', 'idx': 10},
            
            # 11. NODO: CANAL LAJA
            {'nodo': 'CanalLaja', 'tipo': 'in',  'var': 'qg', 'idx': 10},
            {'nodo': 'CanalLaja', 'tipo': 'in',  'var': 'qv', 'idx': 10},
            {'nodo': 'CanalLaja', 'tipo': 'out', 'var': 'qg', 'idx': 11},
            {'nodo': 'CanalLaja', 'tipo': 'out', 'var': 'qv', 'idx': 11},
            
            # 12. NODO: LAJA 1
            {'nodo': 'Laja1', 'tipo': 'in',  'var': 'qa', 'idx': 6},
            {'nodo': 'Laja1', 'tipo': 'in',  'var': 'qv', 'idx': 11},
            {'nodo': 'Laja1', 'tipo': 'out', 'var': 'qg', 'idx': 13},
            {'nodo': 'Laja1', 'tipo': 'out', 'var': 'qv', 'idx': 13},
            
            # 13. NODO: EL DIUTO
            {'nodo': 'ElDiuto', 'tipo': 'in',  'var': 'qg', 'idx': 11},
            {'nodo': 'ElDiuto', 'tipo': 'out', 'var': 'qg', 'idx': 15},
            {'nodo': 'ElDiuto', 'tipo': 'out', 'var': 'qv', 'idx': 15},
            
            # 14. NODO: RIETUCAPEL
            {'nodo': 'RieTucapel', 'tipo': 'in',  'var': 'qg', 'idx': 15},
            {'nodo': 'RieTucapel', 'tipo': 'in',  'var': 'qv', 'idx': 15},
            {'nodo': 'RieTucapel', 'tipo': 'out', 'var': 'qp_sum', 'idx': 2},
        ]
        
        # Lista de nodos de balance únicos
        self.NODOS_BALANCE = list(set(item['nodo'] for item in self.ARCOS_RED))
        
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
        self.qf_fijo = 47.0  # Filtración fija [m³/s] - CASO BASE
        
        # Variables (Formulación LaTeX - CASO BASE CON FILTRACIONES FIJAS)
        self.V = {}  # V_{w,t}: Volumen del lago al final de semana w, temporada t [hm³]
        self.V_30Nov = {}  # V_30Nov_{t}: Volumen del lago al 30 Nov (inicio temporada t) [hm³]
        
        # Variables de linealización (zonas) - SOLO PARA VOLÚMENES DE USO
        self.phi_30 = {}  # φ_30_{k,t}: Binaria para linealización al 30 Nov
        self.delta_v30 = {}  # Δv30_{k,t}: Incremento de volumen al 30 Nov en zona k, temporada t [hm³]
        
        # Volúmenes disponibles
        self.VR = {}  # VR_{w,t}: Volumen disponible para riego [hm³]
        self.VR_0 = {}  # VR_{0,t}: Volumen inicial riego temporada t [hm³]
        self.VG = {}  # VG_{w,t}: Volumen disponible para generación [hm³]
        self.VG_0 = {}  # VG_{0,t}: Volumen inicial generación temporada t [hm³]
        
        # Caudales
        self.qer = {}  # qer_{w,t}: Caudal extraído para riego [m³/s]
        self.qeg = {}  # qeg_{w,t}: Caudal extraído para generación [m³/s]
        # self.qf ya no es variable, es parámetro fijo qf_fijo = 47 m³/s
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
            # Los datos de VUC vienen con el mismo índice k para cada zona
            # VUC[(1, k)] = vr_k (volumen de riego para zona k)
            # VUC[(2, k)] = vg_k (volumen de generación para zona k)
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
        """Crea todas las variables según formulación LaTeX - CASO BASE (FILTRACIONES FIJAS)"""
        print("Creando variables de decisión (Caso Base - Filtraciones Fijas en 47 m³/s)...")
        
        K_zonas = self.K[:-1]  # Zonas 1 a K-1 (la última zona no necesita variables delta)
        
        # Volúmenes del lago (sin límite superior estricto, controlado por delta)
        self.V = self.model.addVars(self.W, self.T, lb=0, name="V")
        
        # Volumen al 30 de Noviembre (inicio de cada temporada)
        self.V_30Nov = self.model.addVars(self.T, lb=0, name="V_30Nov")
        
        # Variables de linealización SOLO para volúmenes de uso (phi_30 y delta_v30)
        # NO se necesitan phi_var ni delta_f porque qf es fijo
        self.phi_30 = self.model.addVars(K_zonas, self.T, vtype=GRB.BINARY, name="phi_30")
        self.delta_v30 = self.model.addVars(K_zonas, self.T, lb=0, name="delta_v30")
        
        # Volúmenes disponibles por uso
        self.VR_0 = self.model.addVars(self.T, lb=0, name="VR_0")
        self.VR = self.model.addVars(self.W, self.T, lb=0, name="VR")
        self.VG_0 = self.model.addVars(self.T, lb=0, name="VG_0")
        self.VG = self.model.addVars(self.W, self.T, lb=0, name="VG")
        
        # Caudales
        self.qer = self.model.addVars(self.W, self.T, lb=0, name="qer")
        self.qeg = self.model.addVars(self.W, self.T, lb=0, name="qeg")
        # qf NO es variable, es parámetro fijo qf_fijo = 47 m³/s
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
        
        print("✓ Variables creadas correctamente (Caso Base - Filtraciones Fijas)")
        print(f"  Filtración fija: qf = {self.qf_fijo} m³/s (constante)")
        print(f"  Variables phi_30 (30 Nov): {len(K_zonas) * 6:,}")
        print(f"  Variables delta_v30: {len(K_zonas) * 6:,}")

    def crear_restricciones(self):
        """Crea todas las restricciones según formulación LaTeX - CASO BASE (FILTRACIONES FIJAS)"""
        print("\nCreando restricciones (Caso Base - Filtraciones Fijas en 47 m³/s)...")
        
        K_zonas = self.K[:-1]  # Zonas 1 a K-1
        
        # ========== 1. FILTRACIONES FIJAS (NO HAY LINEALIZACIÓN) ==========
        print("  1. Filtraciones fijas (qf = 47 m³/s constante)...")
        # En este caso base, qf es un parámetro fijo, NO una variable
        # Por lo tanto, NO se necesitan restricciones de linealización para filtraciones
        # El volumen V[w,t] es completamente libre (sujeto solo a V_MIN/V_MAX y balance)
        
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
        
        # Linealización de VR_0[t] y VG_0[t] basado en V_30Nov[t]
        # Usamos interpolación lineal por zonas entre los puntos (v_k, vr_k, vg_k)
        print("  2b. Linealización de VR_0 y VG_0 a partir de V_30Nov...")
        
        for t in self.T:
            # V_30Nov[t] = v_1 + Σ_{k=1}^{K-1} Δv30[k,t]
            # Esta ecuación relaciona V_30Nov con las zonas activadas
            v_expr = self.v_k[1]
            for k in K_zonas:
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                v_expr += self.delta_v30[k, t]
            
            self.model.addConstr(
                self.V_30Nov[t] == v_expr,
                name=f"V30Nov_linearization_{t}")
            
            # VR_0[t] = vr_1 + Σ_{k=1}^{K-1} (vr_{k+1} - vr_k) × Δv30[k,t]
            # Usamos las MISMAS variables Δv30 para mantener consistencia
            vr_expr = self.vr_k[1]
            for k in K_zonas:
                vr_k = self.vr_k[k]
                vr_k_next = self.vr_k[k + 1]
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                vr_expr += (vr_k_next - vr_k) / (v_k_next - v_k) * self.delta_v30[k, t]
            
            self.model.addConstr(
                self.VR_0[t] == vr_expr,
                name=f"VR0_linearization_{t}")
            
            # VG_0[t] = vg_1 + Σ_{k=1}^{K-1} (vg_{k+1} - vg_k) × Δv30[k,t]
            # Usamos las MISMAS variables Δv30 para mantener consistencia
            vg_expr = self.vg_k[1]
            for k in K_zonas:
                vg_k = self.vg_k[k]
                vg_k_next = self.vg_k[k + 1]
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                vg_expr += (vg_k_next - vg_k) / (v_k_next - v_k) * self.delta_v30[k, t]
            
            self.model.addConstr(
                self.VG_0[t] == vg_expr,
                name=f"VG0_linearization_{t}")
            
            # Restricciones de linealización por zonas para Δv30[k,t]
            # Estas aseguran que la interpolación sea correcta
            for k in K_zonas:
                v_k = self.v_k[k]
                v_k_next = self.v_k[k + 1]
                
                # 1. Δv30[k,t] ≤ v_{k+1} - v_k
                #    El incremento no puede exceder el ancho de la zona
                self.model.addConstr(
                    self.delta_v30[k, t] <= v_k_next - v_k,
                    name=f"delta_v30_upper_{k}_{t}")
                
                # 2. Δv30[k,t] ≥ φ_30[k,t] × (v_{k+1} - v_k)
                #    Si zona k está completa (φ_30[k,t]=1), el incremento es máximo
                self.model.addConstr(
                    self.delta_v30[k, t] >= self.phi_30[k, t] * (v_k_next - v_k),
                    name=f"delta_v30_lower_{k}_{t}")
                
                # 3. Δv30[k,t] ≤ φ_30[k-1,t] × (v_{k+1} - v_k)
                #    Solo se puede tener incremento en zona k si zona k-1 está completa
                if k > 1:
                    self.model.addConstr(
                        self.delta_v30[k, t] <= self.phi_30[k-1, t] * (v_k_next - v_k),
                        name=f"delta_v30_ordering_{k}_{t}")
                # Para k=1, no hay restricción previa (zona base siempre activa)
        
        # ========== 3. GENERACIÓN EN EL TORO ==========
        print("  3. Generación en El Toro...")
        for t in self.T:
            for w in self.W:
                # qg[1,w,t] = qer[w,t] + qeg[w,t]
                self.model.addConstr(
                    self.qg[1, w, t] == self.qer[w, t] + self.qeg[w, t],
                    name=f"gen_eltoro_{w}_{t}")
                
        
        # ========== 3b. BALANCE DE VOLÚMENES POR USO (VR Y VG) ==========
        print("  3b. Balance de volúmenes por uso (VR y VG)...")
        for t in self.T:
            for w in self.W:
                if w == 1:
                    # Primera semana: partir de volúmenes iniciales
                    # VR[1,t] = VR_0[t] - qer[1,t] * FS[1] / 10^6
                    self.model.addConstr(
                        self.VR[w, t] == self.VR_0[t] - self.qer[w, t] * self.FS[w] / 1000000,
                        name=f"balance_VR_1_{t}")
                    
                    # VG[1,t] = VG_0[t] - qeg[1,t] * FS[1] / 10^6
                    self.model.addConstr(
                        self.VG[w, t] == self.VG_0[t] - self.qeg[w, t] * self.FS[w] / 1000000,
                        name=f"balance_VG_1_{t}")
                else:
                    # Semanas posteriores: partir de semana anterior
                    # VR[w,t] = VR[w-1,t] - qer[w,t] * FS[w] / 10^6
                    self.model.addConstr(
                        self.VR[w, t] == self.VR[w-1, t] - self.qer[w, t] * self.FS[w] / 1000000,
                        name=f"balance_VR_{w}_{t}")
                    
                    # VG[w,t] = VG[w-1,t] - qeg[w,t] * FS[w] / 10^6
                    self.model.addConstr(
                        self.VG[w, t] == self.VG[w-1, t] - self.qeg[w, t] * self.FS[w] / 1000000,
                        name=f"balance_VG_{w}_{t}")
        
        # Restricción adicional: volúmenes finales no negativos (ya garantizado por lb=0 en definición de variables)
        # Pero podemos agregar explícitamente para claridad:
        for t in self.T:
            # VR[48,t] ≥ 0  (sobrante de riego no negativo)
            self.model.addConstr(
                self.VR[48, t] >= 0,
                name=f"VR_final_nonneg_{t}")
            
            # VG[48,t] ≥ 0  (sobrante de generación no negativo)
            self.model.addConstr(
                self.VG[48, t] >= 0,
                name=f"VG_final_nonneg_{t}")
        
        # ========== 4. BALANCE DE VOLUMEN EN EL LAGO ==========
        print("  4. Balance de volumen del lago...")
        for t in self.T:
            for w in self.W:
                if w == 1 and t == 1:
                    # V[1,1] = V_0 + (QA[1,1,1] - qg[1,1,1] - qf_fijo) * FS[1] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V_0 + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf_fijo) * self.FS[w] / 1000000,
                        name=f"balance_vol_11")
                elif w == 1 and t > 1:
                    # V[1,t] = V[48,t-1] + (QA[1,1,t] - qg[1,1,t] - qf_fijo) * FS[1] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V[48, t-1] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf_fijo) * self.FS[w] / 1000000,
                        name=f"balance_vol_1{t}")
                else:
                    # V[w,t] = V[w-1,t] + (QA[1,w,t] - qg[1,w,t] - qf_fijo) * FS[w] / 10^6
                    self.model.addConstr(
                        self.V[w, t] == self.V[w-1, t] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf_fijo) * self.FS[w] / 1000000,
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
        
        # V[48,6] ≥ V_F (Volumen final esperado al término de la última temporada)
        self.model.addConstr(
            self.V[48, 6] >= self.V_F,
            name="vol_final")
        
        # ========== 6. INCLUSIÓN DE FILTRACIONES ==========
        print("  6. Inclusión de filtraciones en Laja...")
        for t in self.T:
            for w in self.W:
                # qg[16,w,t] = qf_fijo (47 m³/s)
                self.model.addConstr(
                    self.qg[16, w, t] == self.qf_fijo,
                    name=f"laja_filt_{w}_{t}")
        
        # ========== 7. BALANCE DE FLUJO EN REDES (Genérico usando ARCOS_RED) ==========
        print("  7. Balance de flujo en redes...")
        for nodo in self.NODOS_BALANCE:
            for t in self.T:
                for w in self.W:
                    # Construir flujo entrante y saliente para este nodo
                    flujo_entrante = 0
                    flujo_saliente = 0
                    
                    # Filtrar arcos que corresponden a este nodo
                    arcos_nodo = [arco for arco in self.ARCOS_RED if arco['nodo'] == nodo]
                    
                    for arco in arcos_nodo:
                        var_type = arco['var']
                        idx = arco['idx']
                        tipo = arco['tipo']
                        
                        # Seleccionar la variable correcta según el tipo
                        if var_type == 'qa':
                            valor = self.QA[idx, w, t]
                        elif var_type == 'qg':
                            valor = self.qg[idx, w, t]
                        elif var_type == 'qv':
                            valor = self.qv[idx, w, t]
                        elif var_type == 'qer':
                            valor = self.qer[w, t]
                        elif var_type == 'qeg':
                            valor = self.qeg[w, t]
                        elif var_type == 'qf':
                            valor = self.qf_fijo  # Parámetro fijo
                        elif var_type == 'qp_sum':
                            valor = gp.quicksum(self.qp[d, idx, w, t] for d in self.D)
                        else:
                            continue  # Variable no reconocida
                        
                        # Agregar al flujo correspondiente
                        if tipo == 'in':
                            flujo_entrante += valor
                        elif tipo == 'out':
                            flujo_saliente += valor
                    
                    # Agregar restricción de balance
                    self.model.addConstr(
                        flujo_entrante == flujo_saliente,
                        name=f"Balance_{nodo}_{w}_{t}")
        
        # RIESALTOS: Restricción especial (no es un balance de flujo)
        print("  7b. Restricción especial RieSaltos...")
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qp[3, 3, w, t] == self.qv[11, w, t],
                    name=f"riesaltos_{w}_{t}")
        
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
        
        # 3c. Volúmenes disponibles por uso (iniciales)
        df_volumenes_uso = pd.DataFrame([
            {'Temporada': t, 'VR_0_hm3': self.VR_0[t].X, 'VG_0_hm3': self.VG_0[t].X}
            for t in self.T
        ])
        df_volumenes_uso.to_csv(f"{carpeta_salida}/volumenes_por_uso.csv", index=False)
        
        # 3d. Evolución de volúmenes VR y VG por semana
        df_vr_vg = pd.DataFrame([
            {
                'Semana': w,
                'Temporada': t,
                'VR_hm3': self.VR[w, t].X,
                'VG_hm3': self.VG[w, t].X
            }
            for w in self.W for t in self.T
        ])
        df_vr_vg.to_csv(f"{carpeta_salida}/volumenes_vr_vg.csv", index=False)
        
        # 3e. Extracciones por uso
        df_extracciones = pd.DataFrame([
            {
                'Semana': w,
                'Temporada': t,
                'qer_m3s': self.qer[w, t].X,
                'qeg_m3s': self.qeg[w, t].X
            }
            for w in self.W for t in self.T
        ])
        df_extracciones.to_csv(f"{carpeta_salida}/extracciones_por_uso.csv", index=False)
        
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
        
        # 7. Variables de linealización phi_30 (solo para 30 Nov)
        K_zonas = self.K[:-1]
        df_phi_30 = pd.DataFrame([
            {'Zona': k, 'Temporada': t, 'Phi_30': self.phi_30[k, t].X}
            for k in K_zonas for t in self.T if self.phi_30[k, t].X > 0.5
        ])
        if len(df_phi_30) > 0:
            df_phi_30.to_csv(f"{carpeta_salida}/phi_30_zonas.csv", index=False)
        
        # 8. Filtraciones (fijas en 47 m³/s) (fijas en 47 m³/s)
        df_filtraciones = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Filtracion_m3s': self.qf_fijo}
            for w in self.W for t in self.T
        ])
        df_filtraciones.to_csv(f"{carpeta_salida}/filtraciones.csv", index=False)
        
        # 9. Volúmenes incrementales al 30 Nov (delta_v30)
        df_delta_v30 = pd.DataFrame([
            {'Zona': k, 'Temporada': t, 'Delta_v30_hm3': self.delta_v30[k, t].X}
            for k in K_zonas for t in self.T if self.delta_v30[k, t].X > 0.001
        ])
        if len(df_delta_v30) > 0:
            df_delta_v30.to_csv(f"{carpeta_salida}/volumenes_incrementales_30nov.csv", index=False)
        
        print("✓ Resultados exportados exitosamente (Caso Base - Filtraciones Fijas)")
