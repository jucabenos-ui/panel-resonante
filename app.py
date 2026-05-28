import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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
    "MDF 3 mm":      {"masa": 2.1, "costo": "Bajo",  "rigidez": "Media"},
    "MDF 6 mm":      {"masa": 4.2, "costo": "Bajo",  "rigidez": "Alta"},
    "MDF 9 mm":      {"masa": 6.3, "costo": "Medio", "rigidez": "Alta"},
    "Triplex 4 mm":  {"masa": 2.5, "costo": "Medio", "rigidez": "Media"},
    "Triplex 6 mm":  {"masa": 3.8, "costo": "Medio", "rigidez": "Media"},
    "Drywall 12 mm": {"masa": 9.5, "costo": "Bajo",  "rigidez": "Baja"},
}

# =========================================================
# FUNCIONES
# =========================================================

def calcular_modos(Lx, Ly, Lz, c=343, n_max=5):
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


def disenar_panel(f_obj, usar_relleno):
    # Para frecuencias muy bajas (<50 Hz) la cavidad física necesaria es mayor,
    # por eso ampliamos el rango válido dinámicamente.
    if f_obj < 50:
        rango_min, rango_max, optimo = 8.0, 30.0, 20.0
    elif f_obj < 80:
        rango_min, rango_max, optimo = 6.0, 22.0, 12.0
    else:
        rango_min, rango_max, optimo = 4.0, 18.0, 10.0

    candidatos = []
    for nombre, props in MATERIALES.items():
        masa = props["masa"]
        d = (60.0 / f_obj) ** 2 / masa
        d_cm = d * 100
        fr = 60.0 / np.sqrt(masa * d)
        if usar_relleno:
            coef_base = 0.75
        else:
            coef_base = 0.50
        coef_abs = round(min(coef_base + 0.12 * min(d_cm / optimo, 1.0), 0.95), 2)
        score = abs(d_cm - optimo)
        valido = rango_min <= d_cm <= rango_max
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
    if not validos:
        # Fallback: el material con menor masa (cavidad más grande = más realista para bajas f)
        validos = sorted(candidatos, key=lambda x: x["masa"])
    return sorted(validos, key=lambda x: x["score"])[0]


def calcular_dimensiones(f_obj, geometria):
    c = 343.0
    lambda_4 = (c / f_obj) / 4.0
    dim_min = max(lambda_4 * 1.25, 0.30)

    if geometria == "Rectangular":
        ancho = round(max(dim_min * 1.5, 0.60), 2)
        alto  = round(max(dim_min,       0.40), 2)
        area  = round(ancho * alto, 2)
        return {"tipo": "Rectangular", "Ancho": f"{ancho} m", "Alto": f"{alto} m", "Area": f"{area} m2"}

    elif geometria == "Cuadrado":
        lado = round(max(dim_min * 1.2, 0.50), 2)
        area = round(lado ** 2, 2)
        return {"tipo": "Cuadrado", "Lado": f"{lado} m", "Area": f"{area} m2"}

    elif geometria == "Circular":
        radio = round(max(dim_min * 0.8, 0.25), 2)
        area  = round(np.pi * radio ** 2, 2)
        return {"tipo": "Circular", "Radio": f"{radio} m", "Diametro": f"{round(radio*2, 2)} m", "Area": f"{area} m2"}

    elif geometria == "Hexagonal":
        lado = round(max(dim_min, 0.35), 2)
        area = round(3 * np.sqrt(3) / 2 * lado ** 2, 2)
        return {"tipo": "Hexagonal", "Lado": f"{lado} m", "Area": f"{area} m2"}

    return {"tipo": geometria, "Area": f"{round(dim_min**2, 2)} m2"}


def seleccionar_geometria(tipo_modo, frecuencia, densidad_modos):
    if frecuencia < 60:
        return "Circular"
    elif densidad_modos >= sensibilidad:
        return "Hexagonal"
    elif tipo_modo == "Axial":
        return "Rectangular"
    else:
        return "Cuadrado"


def sugerir_ubicacion(modo):
    nx, ny, nz = modo
    if nx != 0 and ny == 0 and nz == 0:
        return "Pared frontal y trasera (eje X)"
    if ny != 0 and nx == 0 and nz == 0:
        return "Paredes laterales (eje Y)"
    if nz != 0 and nx == 0 and ny == 0:
        return "Techo o piso (eje Z)"
    if nx != 0:
        return "Pared frontal y trasera"
    if ny != 0:
        return "Paredes laterales"
    return "Techo o piso"


def cantidad_paneles(Lx, Ly, Lz, densidad):
    vol  = Lx * Ly * Lz
    base = max(2, int(vol / 18))
    if densidad >= sensibilidad:
        base += 2
    return base

# =========================================================
# BOTÓN PRINCIPAL
# =========================================================

if st.button("🔍 Analizar recinto y diseñar panel", type="primary"):

    modos         = calcular_modos(Lx, Ly, Lz)
    modos_bajos   = [m for m in modos if m["frecuencia"] <= 300]
    modos_axiales = [m for m in modos_bajos if m["tipo"] == "Axial"]

    modo_critico       = modos_axiales[0] if modos_axiales else modos_bajos[0]
    frecuencia_critica = modo_critico["frecuencia"]

    densidad = len([
        m for m in modos_bajos
        if abs(m["frecuencia"] - frecuencia_critica) < 20
    ])

    panel     = disenar_panel(frecuencia_critica, usar_relleno)
    geometria = seleccionar_geometria(modo_critico["tipo"], frecuencia_critica, densidad)
    dims      = calcular_dimensiones(frecuencia_critica, geometria)
    ubicacion = sugerir_ubicacion(modo_critico["modo"])
    n_pan     = cantidad_paneles(Lx, Ly, Lz, densidad)

    # ----------------------------------------------------------
    # ANÁLISIS MODAL
    # ----------------------------------------------------------

    st.header("📊 Análisis modal del recinto")

    c1, c2, c3 = st.columns(3)
    c1.metric("Frecuencia crítica",   f"{frecuencia_critica} Hz")
    c2.metric("Tipo de modo",         modo_critico["tipo"])
    c3.metric("Densidad modal local", f"{densidad} modos")

    st.caption(
        f"Modo: {modo_critico['modo']} · "
        f"Total modos <= 300 Hz: {len(modos_bajos)} "
        f"({len(modos_axiales)} axiales)"
    )

    colores_tipo = {
        "Axial":      "#e74c3c",
        "Tangencial": "#3498db",
        "Oblicuo":    "#2ecc71",
    }

    fig, ax = plt.subplots(figsize=(9, 2.8))
    leyendas_vistas = set()

    for m in modos_bajos:
        t     = m["tipo"]
        color = colores_tipo[t]
        label = t if t not in leyendas_vistas else "_nolegend_"
        leyendas_vistas.add(t)
        ax.vlines(m["frecuencia"], 0, 1, colors=color, linewidth=1.8, label=label)

    ax.axvline(
        frecuencia_critica,
        color="orange", linestyle="--", linewidth=2,
        label=f"Critico: {frecuencia_critica} Hz"
    )

    ax.set_title("Distribucion de modos propios (<= 300 Hz)", fontsize=11)
    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_yticks([])
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 1.3)
    ax.grid(True, axis="x", alpha=0.25)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.7)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ----------------------------------------------------------
    # DISEÑO DEL PANEL
    # ----------------------------------------------------------

    st.header("🛠️ Diseño del panel resonante")

    st.table({
        "Parámetro": [
            "Material",
            "Masa superficial",
            "Costo relativo",
            "Frecuencia de resonancia",
            "Profundidad de cavidad",
            "Coef. de absorción",
            "Geometría",
            "Paneles recomendados",
            "Ubicación",
        ],
        "Valor": [
            panel["material"],
            f"{panel['masa']} kg/m²",
            panel["costo"],
            f"{panel['fr']} Hz",
            f"{panel['cavidad_cm']} cm",
            str(panel["absorcion"]),
            dims["tipo"],
            f"{n_pan} unidades",
            ubicacion,
        ],
    })

    # ----------------------------------------------------------
    # DIMENSIONES
    # ----------------------------------------------------------

    st.subheader("📏 Dimensiones del panel")

    dim_items = [(k, v) for k, v in dims.items() if k != "tipo"]
    st.table({
        "Dimensión": [k for k, v in dim_items],
        "Valor":     [v for k, v in dim_items],
    })

    # ----------------------------------------------------------
    # RELLENO
    # ----------------------------------------------------------

    st.header("🧵 Configuracion interna")

    mitad_cav = round(panel["cavidad_cm"] * 0.5, 1)

    if usar_relleno:
        st.success(
            "Lana mineral o lana de roca recomendada.\n\n"
            f"- Espesor sugerido: {mitad_cav} cm "
            f"(mitad de la cavidad de {panel['cavidad_cm']} cm).\n"
            "- Mayor amortiguamiento y banda de absorcion mas ancha.\n"
            "- Reduce resonancias secundarias del panel."
        )
    else:
        st.warning(
            "Panel resonante puro (sin relleno).\n\n"
            "- Absorcion muy selectiva en banda estrecha.\n"
            "- Resonancia mas pronunciada fuera de la frecuencia objetivo.\n"
            "- Recomendado solo si la frecuencia problema es muy especifica."
        )

    # ----------------------------------------------------------
    # UBICACIÓN
    # ----------------------------------------------------------

    st.header("📍 Ubicacion recomendada")

    st.info(
        f"Superficie principal: {ubicacion}\n\n"
        f"Distribuir los {n_pan} paneles simetricamente respecto al eje de la sala. "
        "Evitar esquinas si hay trampas de graves dedicadas en esas posiciones."
    )

    # ----------------------------------------------------------
    # INTERPRETACIÓN
    # ----------------------------------------------------------

    st.header("📋 Interpretacion acustica")

    if frecuencia_critica < 60:
        st.write(
            "El recinto presenta problemas severos de bajas frecuencias (< 60 Hz). "
            "Se recomienda alta masa superficial y cavidad profunda. "
            "Considerar complementar con trampas de graves tipo esquina."
        )
    elif frecuencia_critica < 120:
        st.write(
            "El problema modal se encuentra en graves medios (60-120 Hz). "
            "Un panel resonante con relleno absorbente controla bien esta zona "
            "sin comprometer el tiempo de reverberacion global."
        )
    else:
        st.write(
            "El recinto presenta resonancias moderadas (> 120 Hz). "
            "El panel suavizara acumulaciones energeticas en la zona media. "
            "Evaluar tambien difusores en las superficies paralelas opuestas."
        )

    st.markdown("---")

    st.subheader("🧠 Principio fisico")

    st.markdown(
        "El panel resonante opera como un **sistema masa-resorte**:\n\n"
        "- La lamina de madera aporta la **masa** inercial.\n"
        "- La cavidad de aire actua como **resorte** elastico.\n"
        "- El relleno de lana introduce **amortiguamiento** viscoso.\n\n"
        "El sistema entra en resonancia cerca de la frecuencia modal critica "
        "y convierte energia acustica en calor."
    )
