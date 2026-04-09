import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ── Configuración de la página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Panel Resonante — Análisis Acústico",
    page_icon="🔊",
    layout="centered"
)

st.title("🔊 Sistema de Análisis de Panel Resonante")
st.markdown(
    "Ingresa las dimensiones de tu recinto para obtener el coeficiente "
    "de absorción recomendado y los parámetros del panel resonante."
)

# ── Módulo 1: Entrada de datos ───────────────────────────────────────────────
st.header("📐 Dimensiones del recinto")
col1, col2, col3 = st.columns(3)
with col1:
    Lx = st.number_input("Largo (m)", min_value=1.0, max_value=30.0, value=5.0, step=0.1)
with col2:
    Ly = st.number_input("Ancho (m)", min_value=1.0, max_value=30.0, value=4.0, step=0.1)
with col3:
    Lz = st.number_input("Altura (m)", min_value=1.0, max_value=10.0, value=2.8, step=0.1)

# ── Módulo 2: Almacenar — Análisis modal ─────────────────────────────────────
def calcular_frecuencias_modales(Lx, Ly, Lz, c=343, n_max=3):
    """Calcula frecuencias modales axiales, tangenciales y oblicuas."""
    freqs = []
    for nx in range(0, n_max + 1):
        for ny in range(0, n_max + 1):
            for nz in range(0, n_max + 1):
                if nx == 0 and ny == 0 and nz == 0:
                    continue
                f = (c / 2) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                freqs.append(round(f, 2))
    return sorted(set(freqs))

# ── Módulo 3: Procesar — Diseño del panel ────────────────────────────────────
def calcular_panel(f_objetivo, d=0.05, rho=1.21, c=343):
    """
    Estima masa superficial y coeficiente de absorción del panel.
    d   = profundidad de la cavidad en metros (default 5 cm)
    rho = densidad del aire (kg/m³)
    """
    # Rigidez del aire en la cavidad: k = rho * c² / d
    k = (rho * c**2) / d
    # Masa superficial para resonar en f_objetivo: m = k / (2π·f)²
    m = k / (2 * np.pi * f_objetivo)**2
    # Coeficiente de absorción aproximado (modelo simplificado)
    alpha = min(0.95, 0.3 + 0.65 * np.exp(-((f_objetivo - 80) / 60)**2))
    return round(m, 3), round(k, 2), round(alpha, 3)

# ── Botón de análisis ─────────────────────────────────────────────────────────
if st.button("🔍 Analizar recinto", type="primary"):
    freqs = calcular_frecuencias_modales(Lx, Ly, Lz)
    freqs_bajas = [f for f in freqs if f <= 300]

    # ── Módulo 2 output ───────────────────────────────────────────────────────
    st.header("📊 Análisis modal del recinto")

    if freqs_bajas:
        st.warning(f"⚠️ Se detectaron {len(freqs_bajas)} modos en bajas frecuencias (≤ 300 Hz).")
        f_problema = freqs_bajas[0]
        st.write(f"**Frecuencia modal más crítica:** {f_problema} Hz")

        # Gráfica de frecuencias modales
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.stem(
            freqs_bajas,
            np.ones(len(freqs_bajas)),
            linefmt="steelblue",
            markerfmt="o",
            basefmt=" "
        )
        ax.set_xlabel("Frecuencia (Hz)")
        ax.set_title("Modos propios del recinto ≤ 300 Hz")
        ax.set_yticks([])
        ax.grid(axis="x", alpha=0.3)
        st.pyplot(fig)

        # ── Módulo 3 output ───────────────────────────────────────────────────
        st.header("🛠️ Propuesta de panel resonante")
        masa, rigidez, alpha = calcular_panel(f_problema)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Frecuencia objetivo", f"{f_problema} Hz")
        col_b.metric("Masa superficial (m)", f"{masa} kg/m²")
        col_c.metric("Coeficiente de absorción (α)", f"{alpha}")

        # ── Módulo 4: Interpretar ─────────────────────────────────────────────
        st.header("📋 Interpretación del diseño")
        if alpha >= 0.7:
            st.success(
                f"✅ Panel con α = {alpha} — Alta absorción. "
                f"Recomendado para frecuencias problemáticas en {f_problema} Hz."
            )
        elif alpha >= 0.4:
            st.info(
                f"ℹ️ Panel con α = {alpha} — Absorción moderada. "
                f"Considerar aumentar la profundidad de cavidad."
            )
        else:
            st.warning(
                f"⚠️ Panel con α = {alpha} — Absorción baja. "
                f"Se recomienda revisar el material o la cavidad."
            )

        st.markdown("---")
        st.markdown(f"**Material sugerido:** Madera MDF de {round(masa*10, 1)} mm de espesor")
        st.markdown(f"**Profundidad de cavidad:** 5 cm (ajustable para afinar frecuencia)")
        st.markdown(f"**Rigidez del sistema (k):** {rigidez} N/m²")

    else:
        st.success("✅ No se detectaron acumulaciones críticas en bajas frecuencias.")
