import streamlit as st
import numpy as np
import plotly.graph_objects as go

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Diseño de Panel Resonante",
    page_icon="🔊",
    layout="centered"
)

st.title("🔊 Diseño Inteligente de Panel Resonante")
st.markdown(
    "Analiza los modos propios del recinto y diseña un panel resonante "
    "optimizado según la frecuencia modal crítica, tipo de modo, material, "
    "geometría, profundidad de cavidad y relleno absorbente."
)

# =========================================================
# DATOS DEL RECINTO
# =========================================================

st.header("📐 Dimensiones del recinto")

col1, col2, col3 = st.columns(3)

with col1:
    Lx = st.number_input("Largo (m)", min_value=1.0, max_value=30.0, value=5.0, step=0.1)

with col2:
    Ly = st.number_input("Ancho (m)", min_value=1.0, max_value=30.0, value=4.0, step=0.1)

with col3:
    Lz = st.number_input("Altura (m)", min_value=1.0, max_value=10.0, value=2.8, step=0.1)

# =========================================================
# PARÁMETROS DE DISEÑO
# =========================================================

st.header("⚙️ Parámetros de diseño")

col1, col2 = st.columns(2)

with col1:
    usar_relleno = st.checkbox("Usar relleno absorbente (lana mineral)", value=True)

with col2:
    sensibilidad = st.slider("Sensibilidad a densidad modal", 1, 10, 5)

# =========================================================
# BASE DE MATERIALES
# =========================================================

MATERIALES = {
    "MDF 3 mm":     {"masa": 2.1,  "costo": "Bajo",  "rigidez": "Media"},
    "MDF 6 mm":     {"masa": 4.2,  "costo": "Bajo",  "rigidez": "Alta"},
    "MDF 9 mm":     {"masa": 6.3,  "costo": "Medio", "rigidez": "Alta"},
    "Triplex 4 mm": {"masa": 2.5,  "costo": "Medio", "rigidez": "Media"},
    "Triplex 6 mm": {"masa": 3.8,  "costo": "Medio", "rigidez": "Media"},
    "Drywall 12 mm":{"masa": 9.5,  "costo": "Bajo",  "rigidez": "Baja"},
}

# =========================================================
# CÁLCULO DE MODOS DEL RECINTO
# =========================================================

def calcular_modos(Lx, Ly, Lz, c=343, n_max=5):
    """
    Calcula los modos propios de un recinto rectangular.
    Fórmula: f = (c/2) * sqrt((nx/Lx)^2 + (ny/Ly)^2 + (nz/Lz)^2)
    Clasifica en Axial, Tangencial u Oblicuo según cuántos índices son cero.
    """
    modos = []

    for nx in range(n_max + 1):
        for ny in range(n_max + 1):
            for nz in range(n_max + 1):

                if nx == 0 and ny == 0 and nz == 0:
                    continue

                f = (c / 2) * np.sqrt(
                    (nx / Lx) ** 2 +
                    (ny / Ly) ** 2 +
                    (nz / Lz) ** 2
                )

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
# DISEÑO DEL PANEL RESONANTE
# =========================================================

def disenar_panel(f_obj, usar_relleno):
    """
    Selecciona el mejor material para un panel resonante cuya
    cavidad quede en rango práctico (4–18 cm).

    Fórmula panel resonante:
        fr = 60 / sqrt(m * d)
        d  = (60 / f_obj)^2 / m    [metros]

    Se elige el material cuya profundidad de cavidad resultante
    esté más cerca del valor óptimo práctico (~10 cm).
    """
    candidatos = []

    for nombre, props in MATERIALES.items():
        masa = props["masa"]
        d = (60.0 / f_obj) ** 2 / masa       # profundidad cavidad [m]
        d_cm = d * 100
        fr = 60.0 / np.sqrt(masa * d)        # ≈ f_obj por construcción

        # Coeficiente de absorción: mejora con cavidad más profunda y relleno
        if usar_relleno:
            coef_base = 0.75
        else:
            coef_base = 0.50

        coef_abs = round(min(coef_base + 0.12 * min(d_cm / 15.0, 1.0), 0.95), 2)

        # Puntuación: cavidad óptima ~10 cm; penalizar extremos
        score = abs(d_cm - 10.0)
        valido = 4.0 <= d_cm <= 18.0

        candidatos.append({
            "material": nombre,
            "masa": round(masa, 2),
            "cavidad_cm": round(d_cm, 1),
            "fr": round(fr, 1),
            "absorcion": coef_abs,
            "costo": props["costo"],
            "score": score,
            "valido": valido,
        })

    validos = [c for c in candidatos if c["valido"]]

    # Si ningún material da cavidad válida, usar todos como fallback
    if not validos:
        validos = candidatos

    return sorted(validos, key=lambda x: x["score"])[0]

# =========================================================
# GEOMETRÍA DEL PANEL
# =========================================================

def seleccionar_geometria(tipo_modo, frecuencia, densidad_modos):
    """
    Reglas de selección de geometría:
    - Frecuencia muy baja (<60 Hz): Circular (distribución suave de presión)
    - Alta densidad modal (≥6):     Hexagonal (mayor cobertura angular)
    - Modo axial:                   Rectangular (alineación con paredes)
    - Resto:                        Cuadrado
    """
    if frecuencia < 60:
        return "Circular"
    elif densidad_modos >= sensibilidad:
        return "Hexagonal"
    elif tipo_modo == "Axial":
        return "Rectangular"
    else:
        return "Cuadrado"

# =========================================================
# DIMENSIONES RECOMENDADAS
# =========================================================

def calcular_dimensiones(f_obj, geometria):
    """
    El tamaño mínimo efectivo de un panel resonante es λ/4
    a la frecuencia objetivo.  Se aplica un factor de seguridad ×1.25.
    """
    c = 343.0
    lambda_4 = (c / f_obj) / 4.0
    dim_min = max(lambda_4 * 1.25, 0.30)    # mínimo 30 cm

    if geometria == "Rectangular":
        ancho = round(max(dim_min * 1.5, 0.60), 2)
        alto  = round(max(dim_min,       0.40), 2)
        area  = round(ancho * alto, 2)
        return {
            "tipo": "Rectangular",
            "Ancho": f"{ancho} m",
            "Alto":  f"{alto} m",
            "Área":  f"{area} m²",
        }

    elif geometria == "Cuadrado":
        lado = round(max(dim_min * 1.2, 0.50), 2)
        area = round(lado ** 2, 2)
        return {
            "tipo": "Cuadrado",
            "Lado": f"{lado} m",
            "Área": f"{area} m²",
        }

    elif geometria == "Circular":
        radio = round(max(dim_min * 0.8, 0.25), 2)
        area  = round(np.pi * radio ** 2, 2)
        return {
            "tipo": "Circular",
            "Radio": f"{radio} m",
            "Diámetro": f"{round(radio*2, 2)} m",
            "Área": f"{area} m²",
        }

    elif geometria == "Hexagonal":
        lado = round(max(dim_min, 0.35), 2)
        area = round(3 * np.sqrt(3) / 2 * lado ** 2, 2)
        return {
            "tipo": "Hexagonal",
            "Lado": f"{lado} m",
            "Área": f"{area} m²",
        }

    return {"tipo": geometria, "Área": f"{round(dim_min**2, 2)} m²"}

# =========================================================
# UBICACIÓN
# =========================================================

def sugerir_ubicacion(modo):
    nx, ny, nz = modo

    # Modos axiales puros
    if nx != 0 and ny == 0 and nz == 0:
        return "Pared frontal y trasera (eje X)"
    if ny != 0 and nx == 0 and nz == 0:
        return "Paredes laterales (eje Y)"
    if nz != 0 and nx == 0 and ny == 0:
        return "Techo o piso (eje Z)"

    # Modos tangenciales y oblicuos
    if nx != 0:
        return "Pared frontal y trasera"
    if ny != 0:
        return "Paredes laterales"
    return "Techo o piso"

# =========================================================
# CANTIDAD DE PANELES
# =========================================================

def cantidad_paneles(Lx, Ly, Lz, densidad):
    """
    Estimación basada en volumen del recinto y densidad modal.
    Regla práctica: 1 panel por cada ~15–20 m³, mínimo 2.
    """
    vol  = Lx * Ly * Lz
    base = max(2, int(vol / 18))
    if densidad >= sensibilidad:
        base += 2
    return base

# =========================================================
# BOTÓN PRINCIPAL
# =========================================================

if st.button("🔍 Analizar recinto y diseñar panel", type="primary"):

    modos        = calcular_modos(Lx, Ly, Lz)
    modos_bajos  = [m for m in modos if m["frecuencia"] <= 300]
    modos_axiales= [m for m in modos_bajos if m["tipo"] == "Axial"]

    # Modo crítico: primer axial o primer modo si no hay axiales
    modo_critico      = modos_axiales[0] if modos_axiales else modos_bajos[0]
    frecuencia_critica= modo_critico["frecuencia"]

    # Densidad modal local ±20 Hz
    densidad = len([
        m for m in modos_bajos
        if abs(m["frecuencia"] - frecuencia_critica) < 20
    ])

    panel    = disenar_panel(frecuencia_critica, usar_relleno)
    geometria= seleccionar_geometria(modo_critico["tipo"], frecuencia_critica, densidad)
    dims     = calcular_dimensiones(frecuencia_critica, geometria)
    ubicacion= sugerir_ubicacion(modo_critico["modo"])
    n_pan    = cantidad_paneles(Lx, Ly, Lz, densidad)

    # ==========================================================
    # RESULTADOS — ANÁLISIS MODAL
    # ==========================================================

    st.header("📊 Análisis modal del recinto")

    c1, c2, c3 = st.columns(3)
    c1.metric("Frecuencia crítica",   f"{frecuencia_critica} Hz")
    c2.metric("Tipo de modo",         modo_critico["tipo"])
    c3.metric("Densidad modal local", f"{densidad} modos")

    st.caption(
        f"Modo: {modo_critico['modo']} · "
        f"Total modos ≤ 300 Hz: {len(modos_bajos)} "
        f"({len(modos_axiales)} axiales)"
    )

    # --- Gráfica modal con Plotly (sin matplotlib) ---
    colores_tipo = {
        "Axial":       "#e74c3c",
        "Tangencial":  "#3498db",
        "Oblicuo":     "#2ecc71",
    }

    fig = go.Figure()
    leyendas_vistas = set()

    for m in modos_bajos:
        t     = m["tipo"]
        color = colores_tipo[t]
        mostrar_leyenda = t not in leyendas_vistas
        leyendas_vistas.add(t)

        fig.add_trace(go.Scatter(
            x=[m["frecuencia"], m["frecuencia"]],
            y=[0, 1],
            mode="lines",
            line=dict(color=color, width=2),
            name=t,
            showlegend=mostrar_leyenda,
            legendgroup=t,
        ))

    fig.add_vline(
        x=frecuencia_critica,
        line_dash="dash",
        line_color="orange",
        line_width=2,
        annotation_text=f"  Crítico: {frecuencia_critica} Hz",
        annotation_font_color="orange",
    )

    fig.update_layout(
        title="Distribución de modos propios (≤ 300 Hz)",
        xaxis_title="Frecuencia (Hz)",
        yaxis=dict(showticklabels=False, range=[0, 1.3], title=""),
        height=260,
        margin=dict(t=45, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==========================================================
    # DISEÑO DEL PANEL
    # ==========================================================

    st.header("🛠️ Diseño del panel resonante")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Material",          panel["material"])
        st.metric("Masa superficial",  f"{panel['masa']} kg/m²")
        st.metric("Costo relativo",    panel["costo"])

    with c2:
        st.metric("Frecuencia de resonancia", f"{panel['fr']} Hz")
        st.metric("Profundidad de cavidad",   f"{panel['cavidad_cm']} cm")
        st.metric("Coef. de absorción",       panel["absorcion"])

    with c3:
        st.metric("Geometría",              dims["tipo"])
        st.metric("Paneles recomendados",   f"{n_pan} unidades")
        st.metric("Ubicación",              ubicacion)

    # ==========================================================
    # DIMENSIONES DEL PANEL
    # ==========================================================

    st.subheader("📏 Dimensiones del panel")

    dim_items = [(k, v) for k, v in dims.items() if k != "tipo"]
    dcols = st.columns(len(dim_items))

    for i, (label, valor) in enumerate(dim_items):
        dcols[i].metric(label, valor)

    # ==========================================================
    # RELLENO
    # ==========================================================

    st.header("🧵 Configuración interna")

    mitad_cav = round(panel["cavidad_cm"] * 0.5, 1)

    if usar_relleno:
        st.success(
            f"✔ **Lana mineral o lana de roca** recomendada.\n\n"
            f"- Espesor sugerido: **{mitad_cav} cm** "
            f"(mitad de la cavidad de {panel['cavidad_cm']} cm).\n"
            "- Mayor amortiguamiento y banda de absorción más ancha.\n"
            "- Reduce resonancias secundarias del panel."
        )
    else:
        st.warning(
            "⚠ **Panel resonante puro** (sin relleno).\n\n"
            "- Absorción muy selectiva en banda estrecha.\n"
            "- Resonancia más pronunciada y pronunciado roll-off fuera de la frecuencia objetivo.\n"
            "- Recomendado solo si la frecuencia problema es muy específica."
        )

    # ==========================================================
    # UBICACIÓN
    # ==========================================================

    st.header("📍 Ubicación recomendada")

    st.info(
        f"**Superficie principal:** {ubicacion}\n\n"
        f"Distribuir los **{n_pan} paneles** simétricamente respecto al eje de la sala. "
        "Evitar esquinas si hay trampas de graves dedicadas en esas posiciones."
    )

    # ==========================================================
    # INTERPRETACIÓN ACÚSTICA
    # ==========================================================

    st.header("📋 Interpretación acústica")

    if frecuencia_critica < 60:
        st.write(
            "El recinto presenta **problemas severos de bajas frecuencias** (< 60 Hz). "
            "Se recomienda alta masa superficial y cavidad profunda. "
            "Considerar complementar con trampas de graves tipo esquina."
        )
    elif frecuencia_critica < 120:
        st.write(
            "El problema modal se encuentra en **graves medios (60–120 Hz)**. "
            "Un panel resonante con relleno absorbente controla bien esta zona "
            "sin comprometer excesivamente el tiempo de reverberación global."
        )
    else:
        st.write(
            "El recinto presenta **resonancias moderadas (> 120 Hz)**. "
            "El panel diseñado suavizará acumulaciones energéticas en la zona media. "
            "Evaluar también difusores en las superficies paralelas opuestas."
        )

    st.markdown("---")

    st.subheader("🧠 Principio físico")

    st.markdown(
        "El panel resonante opera como un **sistema masa–resorte**:\n\n"
        "- La lámina de madera aporta la **masa** inercial.\n"
        "- La cavidad de aire actúa como **resorte** elástico (compresibilidad del aire).\n"
        "- El relleno de lana introduce **amortiguamiento** viscoso.\n\n"
        "El sistema entra en resonancia cerca de la frecuencia modal crítica y convierte "
        "energía acústica en calor, reduciendo la acumulación de presión en esa frecuencia."
    )
