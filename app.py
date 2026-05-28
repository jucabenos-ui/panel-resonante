import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, RegularPolygon

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Diseño Inteligente de Panel Resonante",
    page_icon="🔊",
    layout="centered"
)

st.title("🔊 Diseño Inteligente de Panel Resonante")
st.markdown("""
Este sistema analiza los modos propios del recinto y diseña
un panel resonante optimizado según:

- Frecuencia modal crítica
- Tipo de modo
- Geometría del panel
- Material del panel
- Profundidad de cavidad
- Uso de relleno absorbente
- Ubicación recomendada
""")

# =========================================================
# DATOS DEL RECINTO
# =========================================================

st.header("📐 Dimensiones del recinto")

col1, col2, col3 = st.columns(3)

with col1:
    Lx = st.number_input(
        "Largo (m)",
        min_value=1.0,
        max_value=30.0,
        value=5.0,
        step=0.1
    )

with col2:
    Ly = st.number_input(
        "Ancho (m)",
        min_value=1.0,
        max_value=30.0,
        value=4.0,
        step=0.1
    )

with col3:
    Lz = st.number_input(
        "Altura (m)",
        min_value=1.0,
        max_value=10.0,
        value=2.8,
        step=0.1
    )

# =========================================================
# PARÁMETROS OPCIONALES
# =========================================================

st.header("⚙️ Parámetros de diseño")

usar_relleno = st.checkbox(
    "Usar relleno absorbente (lana mineral)",
    value=True
)

densidad_modos_usuario = st.slider(
    "Sensibilidad a densidad modal",
    1,
    10,
    5
)

# =========================================================
# FUNCIÓN MODOS
# =========================================================

def calcular_modos(Lx, Ly, Lz, c=343, n_max=5):

    modos = []

    for nx in range(n_max + 1):
        for ny in range(n_max + 1):
            for nz in range(n_max + 1):

                if nx == 0 and ny == 0 and nz == 0:
                    continue

                f = (c/2) * np.sqrt(
                    (nx/Lx)**2 +
                    (ny/Ly)**2 +
                    (nz/Lz)**2
                )

                # Clasificación modal

                ceros = [nx, ny, nz].count(0)

                if ceros == 2:
                    tipo = "Axial"

                elif ceros == 1:
                    tipo = "Tangencial"

                else:
                    tipo = "Oblicuo"

                modos.append({
                    "frecuencia": round(f, 2),
                    "tipo": tipo,
                    "modo": (nx, ny, nz)
                })

    return sorted(modos, key=lambda x: x["frecuencia"])

# =========================================================
# DISEÑO PANEL
# =========================================================

def disenar_panel(f_obj, usar_relleno):

    materiales = {
        "MDF 3 mm": 2.1,
        "MDF 6 mm": 4.2,
        "Triplex 4 mm": 2.5,
        "Drywall": 8.5
    }

    mejor = None
    error_min = 999

    for material, masa in materiales.items():

        # Fórmula panel resonante
        d = (60 / f_obj)**2 / masa

        fr = 60 / np.sqrt(masa * d)

        error = abs(fr - f_obj)

        if usar_relleno:
            absorcion = 0.85
        else:
            absorcion = 0.65

        if error < error_min:

            error_min = error

            mejor = {
                "material": material,
                "masa": round(masa, 2),
                "cavidad_cm": round(d * 100, 1),
                "fr": round(fr, 2),
                "absorcion": absorcion
            }

    return mejor

# =========================================================
# GEOMETRÍA
# =========================================================

def seleccionar_geometria(
    tipo_modo,
    frecuencia,
    densidad_modos
):

    # Frecuencia muy puntual
    if frecuencia < 60:
        return "Circular"

    # Mucha acumulación modal
    elif densidad_modos >= 6:
        return "Hexagonal"

    # Modos axiales
    elif tipo_modo == "Axial":
        return "Rectangular"

    # Intermedio
    else:
        return "Cuadrado"

# =========================================================
# UBICACIÓN
# =========================================================

def sugerir_ubicacion(modo):

    nx, ny, nz = modo

    if nx != 0:
        return "Pared frontal y trasera"

    elif ny != 0:
        return "Paredes laterales"

    else:
        return "Techo o piso"

# =========================================================
# VISUALIZACIÓN GEOMETRÍA
# =========================================================

def dibujar_geometria(forma):

    fig, ax = plt.subplots(figsize=(4,4))

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    if forma == "Rectangular":

        rect = Rectangle(
            (2, 3),
            6,
            4,
            fill=False,
            linewidth=3
        )

        ax.add_patch(rect)

    elif forma == "Cuadrado":

        rect = Rectangle(
            (3, 3),
            4,
            4,
            fill=False,
            linewidth=3
        )

        ax.add_patch(rect)

    elif forma == "Circular":

        circ = Circle(
            (5,5),
            2.5,
            fill=False,
            linewidth=3
        )

        ax.add_patch(circ)

    elif forma == "Hexagonal":

        hexag = RegularPolygon(
            (5,5),
            numVertices=6,
            radius=3,
            fill=False,
            linewidth=3
        )

        ax.add_patch(hexag)

    ax.set_aspect("equal")
    ax.axis("off")

    return fig

# =========================================================
# BOTÓN PRINCIPAL
# =========================================================

if st.button("🔍 Analizar recinto", type="primary"):

    modos = calcular_modos(Lx, Ly, Lz)

    # Filtrar bajas frecuencias
    modos_bajos = [
        m for m in modos
        if m["frecuencia"] <= 300
    ]

    # Separar axiales
    modos_axiales = [
        m for m in modos_bajos
        if m["tipo"] == "Axial"
    ]

    # Escoger modo crítico
    if len(modos_axiales) > 0:
        modo_critico = modos_axiales[0]
    else:
        modo_critico = modos_bajos[0]

    frecuencia_critica = modo_critico["frecuencia"]

    # =====================================================
    # DENSIDAD MODAL
    # =====================================================

    ancho = 20

    densidad = len([
        m for m in modos_bajos
        if abs(m["frecuencia"] - frecuencia_critica) < ancho
    ])

    # =====================================================
    # PANEL
    # =====================================================

    panel = disenar_panel(
        frecuencia_critica,
        usar_relleno
    )

    # =====================================================
    # GEOMETRÍA
    # =====================================================

    geometria = seleccionar_geometria(
        modo_critico["tipo"],
        frecuencia_critica,
        densidad
    )

    # =====================================================
    # UBICACIÓN
    # =====================================================

    ubicacion = sugerir_ubicacion(
        modo_critico["modo"]
    )

    # =====================================================
    # RESULTADOS
    # =====================================================

    st.header("📊 Análisis modal")

    st.write(f"### Frecuencia crítica: {frecuencia_critica} Hz")
    st.write(f"### Tipo modal: {modo_critico['tipo']}")
    st.write(f"### Modo: {modo_critico['modo']}")
    st.write(f"### Densidad modal local: {densidad}")

    # =====================================================
    # GRÁFICA MODAL
    # =====================================================

    st.subheader("📈 Modos del recinto")

    fig, ax = plt.subplots(figsize=(9,3))

    frecuencias = [
        m["frecuencia"]
        for m in modos_bajos
    ]

    ax.stem(
        frecuencias,
        np.ones(len(frecuencias)),
        linefmt="steelblue",
        markerfmt="o",
        basefmt=" "
    )

    ax.axvline(
        frecuencia_critica,
        color="red",
        linestyle="--",
        label="Modo crítico"
    )

    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_yticks([])
    ax.grid(True, axis="x", alpha=0.3)
    ax.legend()

    st.pyplot(fig)

    # =====================================================
    # PANEL
    # =====================================================

    st.header("🛠️ Diseño del panel resonante")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Material",
            panel["material"]
        )

        st.metric(
            "Masa superficial",
            f"{panel['masa']} kg/m²"
        )

        st.metric(
            "Coeficiente absorción",
            panel["absorcion"]
        )

    with col2:

        st.metric(
            "Frecuencia resonancia",
            f"{panel['fr']} Hz"
        )

        st.metric(
            "Profundidad cavidad",
            f"{panel['cavidad_cm']} cm"
        )

        st.metric(
            "Geometría",
            geometria
        )

    # =====================================================
    # RELLENO
    # =====================================================

    st.header("🧵 Configuración interna")

    if usar_relleno:

        st.success("""
        ✔ Se recomienda usar lana mineral o lana de roca.

        Beneficios:
        - Mayor amortiguamiento
        - Absorción más amplia
        - Menos resonancia secundaria
        """)

    else:

        st.warning("""
        ⚠ Panel resonante puro.

        Características:
        - Absorción muy selectiva
        - Banda estrecha
        - Resonancia más fuerte
        """)

    # =====================================================
    # UBICACIÓN
    # =====================================================

    st.header("📍 Ubicación recomendada")

    st.info(f"Instalar principalmente en: {ubicacion}")

    # =====================================================
    # VISUALIZACIÓN PANEL
    # =====================================================

    st.header("📐 Geometría sugerida")

    fig_geo = dibujar_geometria(geometria)

    st.pyplot(fig_geo)

    # =====================================================
    # INTERPRETACIÓN
    # =====================================================

    st.header("📋 Interpretación acústica")

    if frecuencia_critica < 60:

        st.write("""
        El recinto presenta problemas severos de bajas frecuencias.
        Se recomienda un panel con alta masa y gran cavidad.
        """)

    elif frecuencia_critica < 120:

        st.write("""
        El problema modal se encuentra en graves medios.
        Un panel resonante amortiguado puede controlar
        adecuadamente la resonancia.
        """)

    else:

        st.write("""
        El recinto presenta resonancias moderadas.
        El panel diseñado ayudará a suavizar acumulaciones
        energéticas.
        """)

    st.markdown("---")

    st.subheader("🧠 Explicación física")

    st.markdown("""
    El panel resonante funciona como un sistema masa-resorte:

    - La madera aporta la masa.
    - La cavidad de aire actúa como resorte.
    - El relleno aporta amortiguamiento.

    El sistema entra en resonancia cerca de la frecuencia
    modal crítica del recinto y absorbe energía acústica.
    """)
