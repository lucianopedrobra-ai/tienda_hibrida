import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Tienda Pedro Bravin", page_icon="🏗️", layout="wide")

# --- 2. CONEXIÓN AL CEREBRO (API KEY) ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ Error: No se detectó la API Key. Configurala en los 'Secrets' de Streamlit.")
    st.stop()

# --- 3. CONEXIÓN A LOS DATOS (TU ENLACE CONFIRMADO) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTUG5PPo2kN1HkP2FY1TNAU9-ehvXqcvE_S9VBnrtQIxS9eVNmnh6Uin_rkvnarDQ/pub?gid=2029869540&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    try:
        # dtype=str es vital para que no se rompan los códigos que parecen números
        df = pd.read_csv(SHEET_URL, dtype=str).fillna("")
        return df 
    except Exception as e:
        st.error(f"Error al leer el CSV: {e}")
        return None

df = load_data()

# --- 4. ESTILOS CSS (DISEÑO TIENDA) ---
st.markdown("""
    <style>
    /* Tarjeta de Producto */
    .product-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        height: 100%;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .product-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-color: #0f2c59; }
    
    .product-sku { font-size: 0.75rem; color: #888; margin-bottom: 5px; }
    .product-name { font-weight: 600; color: #333; font-size: 0.95rem; margin-bottom: 10px; min-height: 40px; }
    .price-tag { color: #0f2c59; font-weight: 800; font-size: 1.1rem; }
    .iva-tag { font-size: 0.7rem; color: #666; }
    
    /* Botones */
    .stButton>button {
        width: 100%; border-radius: 5px; font-weight: 600;
        background-color: #0f2c59; color: white; border: none;
    }
    .stButton>button:hover { background-color: #ff6b00; color: white; }
    
    /* Ajustes generales */
    .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 5. GESTIÓN DE CARRITO (LÓGICA) ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

def add_to_cart(item):
    st.session_state.cart.append(item)
    st.toast(f"🛒 {item['nombre']} agregado!", icon="✅")

def clear_cart():
    st.session_state.cart = []

# --- 6. ESTRUCTURA DE PANTALLA (2 COLUMNAS) ---
col_chat, col_shop = st.columns([1, 2], gap="medium")

# ==========================================
# COLUMNA IZQUIERDA: LUCHO (CHATBOT)
# ==========================================
with col_chat:
    st.subheader("💬 Preguntale a Lucho")
    
    if df is not None:
        csv_context = df.to_csv(index=False)
    else:
        csv_context = "No hay datos."

    items_carrito = ", ".join([i['nombre'] for i in st.session_state.cart])
    
    sys_prompt = f"""
    ROL: Eres Lucho, vendedor experto de Pedro Bravin S.A.
    OBJETIVO: Ayudar al cliente a navegar el catálogo que tiene a su derecha.
    
    CONTEXTO ACTUAL:
    - El cliente está viendo una TIENDA ONLINE a su derecha.
    - Su carrito tiene: {items_carrito if items_carrito else 'Está vacío'}.
    
    TUS FUNCIONES:
    1. Si preguntan "¿Qué precio tiene X?", diles que lo busquen en la derecha o dáselo tú.
    2. Si preguntan "¿Para qué sirve X?", asesora técnicamente.
    3. Si piden algo, diles: "Podés agregarlo al carrito con el botón, o yo te ayudo a elegir".
    
    BASE DE DATOS (CSV):
    {csv_context}
    """

    if "messages_shop" not in st.session_state:
        st.session_state.messages_shop = [{"role": "assistant", "content": "👋 Hola! Soy Lucho. A tu derecha tenés el catálogo completo.\n\n¿Necesitás ayuda técnica para elegir algún material?"}]

    for msg in st.session_state.messages_shop:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ej: ¿Qué chapa uso para un techo bajo?"):
        st.session_state.messages_shop.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        try:
            # Usamos PRO para máxima inteligencia como pediste
            model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=sys_prompt)
            response = model.generate_content([m["content"] for m in st.session_state.messages_shop])
            
            st.session_state.messages_shop.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.error("Lucho está descansando un segundo. Intentá de nuevo.")

# ==========================================
# COLUMNA DERECHA: CATÁLOGO VISUAL (CSV)
# ==========================================
with col_shop:
    # 1. Buscador
    col_search, col_cart_btn = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Buscar producto", placeholder="Ej: Perfil C, Malla, 10mm...", label_visibility="collapsed")
    
    # 2. Filtrado de Datos
    if df is not None:
        if search_term:
            filtered_df = df[df.apply(lambda row: search_term.lower() in row.astype(str).str.lower().values.sum(), axis=1)]
        else:
            filtered_df = df.head(12) 

        # 3. Grilla de Productos
        if not filtered_df.empty:
            rows = [filtered_df.iloc[i:i+3] for i in range(0, len(filtered_df), 3)]
            
            for row_products in rows:
                cols = st.columns(3)
                # SOLUCIÓN DEL ERROR: Usamos el 'unique_id' (índice) para la key
                for idx, (unique_id, product) in enumerate(row_products.iterrows()):
                    with cols[idx]:
                        p_sku = product.get('ID_SKU', '---')
                        p_nom = product.get('Producto', 'Producto sin nombre')
                        p_precio = product.get('Precio_Lista', '0')
                        
                        st.markdown(f"""
                        <div class="product-card">
                            <div class="product-sku">{p_sku}</div>
                            <div class="product-name">{p_nom}</div>
                            <div>
                                <div class="price-tag">${p_precio}</div>
                                <div class="iva-tag">+ IVA</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # KEY ÚNICA = "add_" + INDICE DE FILA. ¡Esto no falla!
                        if st.button("➕ Agregar", key=f"add_{unique_id}"):
                            add_to_cart({"sku": p_sku, "nombre": p_nom, "precio": p_precio})
        else:
            st.info("No encontré productos con ese nombre.")

# ==========================================
# BARRA LATERAL (EL CARRITO)
# ==========================================
with st.sidebar:
    st.title(f"🛒 Tu Carrito ({len(st.session_state.cart)})")
    
    if st.session_state.cart:
        pedido_str = ""
        
        for i, item in enumerate(st.session_state.cart):
            st.markdown(f"**{item['nombre']}**")
            st.caption(f"${item['precio']} + IVA")
            pedido_str += f"- {item['nombre']} (${item['precio']})\n"
            st.divider()
        
        if st.button("🗑️ Vaciar Todo"):
            clear_cart()
            st.rerun()
            
        msg_ws = f"Hola Martín! Armé este pedido en la Tienda Web:\n\n{pedido_str}\n\n¿Me confirmás el stock y el precio final con IVA?"
        link_ws = f"https://wa.me/5493401527780?text={urllib.parse.quote(msg_ws)}"
        
        st.markdown(f"""
            <a href="{link_ws}" target="_blank" style="
                display: block; width: 100%; background-color: #25D366; color: white;
                text-align: center; padding: 15px; border-radius: 8px; 
                text-decoration: none; font-weight: bold; margin-top: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                🚀 ENVIAR PEDIDO A MARTÍN
            </a>
        """, unsafe_allow_html=True)
        
    else:
        st.write("Tu carrito está vacío.")
        st.caption("Buscá productos en el catálogo y agregalos aquí.")
