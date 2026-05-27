import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Diseño de Panel Resonante")

st.title("🔊 Diseño Inteligente de Panel Resonante")

# =========================================================
# DATOS DEL RECINTO
# =========================================================

st.header("📐 Dimensiones del recinto")

col1, col2, col3 = st.columns(3)

with col1:
    Lx = st.number_input("Largo (m)", 1.0, 30.0, 5.0)

with col2:
    Ly = st.number_input("Ancho (m)", 1.0, 30.0, 4.0)

with col3:
    Lz = st.number_input("Altura (m)", 1.0, 10.0, 2.8)

# =========================================================
# MODOS DEL RECINTO
# =========================================================

def calcular_modos(Lx, Ly, Lz, c=343, n_max=4):

    modos = []

    for nx in range(n_max + 1):
        for ny in range(n_max + 1):
            for nz in range(n_max + 1):

                if nx == ny == nz == 0:
                    continue

                f = (c/2)*np.sqrt(
                    (nx/Lx)**2 +
                    (ny/Ly)**2 +
                    (nz/Lz)**2
                )

                # Clasificación
                ceros = [nx, ny, nz].count(0)

                if ceros == 2:
                    tipo = "Axial"

                elif ceros == 1:
                    tipo = "Tangencial"

                else:
                    tipo = "Oblicuo"

                modos.append({
                    "frecuencia": round(f,2),
                    "tipo": tipo,
                    "modo": (nx, ny, nz)
                })

    return modos

# =========================================================
# DISEÑO DEL PANEL
# =========================================================

def disenar_panel(f_obj):

    materiales = {
        "MDF 3 mm": 2.1,
        "MDF 6 mm": 4.2,
        "Triplex 4 mm": 2.5,
        "Drywall": 8.5
    }

    mejor = None
    error_min = 999

    for material, masa in materiales.items():

        d = (60/f_obj)**2 / masa

        fr = 60 / np.sqrt(masa*d)

        error = abs(fr - f_obj)

        if error < error_min:

            error_min = error

            mejor = {
                "material": material,
                "masa": round(masa,2),
                "cavidad": round(d*100,1),
                "fr": round(fr,2)
            }

    return mejor

# =========================================================
# ANÁLISIS
# =========================================================

if st.button("🔍 Analizar"):

    modos = calcular_modos(Lx, Ly, Lz)

    modos_bajos = [m for m in modos if m["frecuencia"] <= 300]

    axial = [m for m in modos_bajos if m["tipo"] == "Axial"]

    if axial:

        modo_critico = axial[0]

    else:

        modo_critico = modos_bajos[0]

    fcrit = modo_critico["frecuencia"]

    panel = disenar_panel(fcrit)

    st.header("📊 Modo crítico")

    st.write(f"Frecuencia: {fcrit} Hz")
    st.write(f"Tipo: {modo_critico['tipo']}")
    st.write(f"Modo: {modo_critico['modo']}")

    # =====================================================
    # GRÁFICA
    # =====================================================

    fig, ax = plt.subplots(figsize=(8,3))

    frecuencias = [m["frecuencia"] for m in modos_bajos]

    ax.stem(frecuencias,
            np.ones(len(frecuencias)))

    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_yticks([])
    ax.grid(True)

    st.pyplot(fig)

    # =====================================================
    # PANEL
    # =====================================================

    st.header("🛠️ Diseño recomendado")

    st.metric("Frecuencia objetivo", f"{fcrit} Hz")

    st.metric("Material", panel["material"])

    st.metric("Masa superficial",
              f"{panel['masa']} kg/m²")

    st.metric("Profundidad cavidad",
              f"{panel['cavidad']} cm")

    # =====================================================
    # FORMA
    # =====================================================

    if modo_critico["tipo"] == "Axial":
        forma = "Rectangular"

    elif modo_critico["tipo"] == "Tangencial":
        forma = "Cuadrado"

    else:
        forma = "Ranurado"

    st.header("📐 Geometría recomendada")

    st.success(f"Forma recomendada: {forma}")

    # =====================================================
    # UBICACIÓN
    # =====================================================

    st.header("📍 Ubicación sugerida")

    nx, ny, nz = modo_critico["modo"]

    if nx != 0:
        st.write("Instalar sobre pared frontal o trasera.")

    elif ny != 0:
        st.write("Instalar sobre paredes laterales.")

    else:
        st.write("Instalar en techo o piso.")
