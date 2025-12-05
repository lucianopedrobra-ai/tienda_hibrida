import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Tienda Pedro Bravin", page_icon="🛒", layout="wide")

# --- 2. ESTILOS CSS (E-COMMERCE) ---
st.markdown("""
    <style>
    /* Estilo Tarjeta de Producto */
    .product-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .product-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .price-tag { color: #0f2c59; font-weight: bold; font-size: 1.2rem; }
    .product-name { font-weight: 600; color: #333; height: 50px; overflow: hidden; }
    
    /* Botones */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GESTIÓN DE ESTADO (CARRITO) ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

def add_to_cart(item):
    st.session_state.cart.append(item)
    st.toast(f"✅ {item['Producto']} agregado al carrito")

def clear_cart():
    st.session_state.cart = []

# --- 4. CARGA DE DATOS ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("Falta API KEY")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTUG5PPo2kN1HkP2FY1TNAU9-ehvXqcvE_S9VBnrtQIxS9eVNmnh6Uin_rkvnarDQ/pub?gid=2029869540&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, dtype=str).fillna("")
        return df 
    except:
        return None

df = load_data()

# --- 5. INTERFAZ DIVIDIDA (LA MAGIA HÍBRIDA) ---
col_chat, col_shop = st.columns([1, 1.5], gap="large")

# ==========================================
# COLUMNA DERECHA: EL CATÁLOGO (SHOP)
# ==========================================
with col_shop:
    st.subheader("📦 Catálogo de Materiales")
    
    # Buscador visual
    search = st.text_input("🔍 Buscar producto...", placeholder="Ej: Chapa, Perfil, Malla")
    
    if df is not None:
        # Filtro de búsqueda
        if search:
            filtered_df = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().values.sum(), axis=1)]
        else:
            filtered_df = df.head(20) # Mostrar primeros 20 por defecto para no saturar

        # Renderizar Grid de Productos
        # Usamos columnas dentro de la columna para hacer una grilla
        cols = st.columns(3) 
        for index, row in filtered_df.iterrows():
            with cols[index % 3]: # Distribuye en 3 columnas
                # Tarjeta de producto simulada con HTML/Streamlit
                st.markdown(f"""
                <div class="product-card">
                    <div class="product-name">{row.get('Producto', 'Producto')}</div>
                    <div class="price-tag">${row.get('Precio_Lista', '0')} + IVA</div>
                    <small>Stock: {row.get('Disponibilidad', 'Consultar')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón funcional de Streamlit
                if st.button(f"➕ Agregar", key=f"btn_{index}"):
                    add_to_cart({
                        "sku": row.get('ID_SKU', 'N/A'),
                        "nombre": row.get('Producto', 'Producto'),
                        "precio": row.get('Precio_Lista', '0')
                    })

# ==========================================
# BARRA LATERAL: EL CARRITO
# ==========================================
with st.sidebar:
    st.title("🛒 Tu Pedido")
    
    if len(st.session_state.cart) > 0:
        total_aprox = 0.0
        pedido_texto = ""
        
        for item in st.session_state.cart:
            st.write(f"▪️ {item['nombre']}")
            # Limpieza básica de precio para sumar (quita símbolos si los hay)
            try:
                precio_limpio = float(str(item['precio']).replace('$','').replace('.','').replace(',','.'))
                total_aprox += precio_limpio
            except:
                pass
            pedido_texto += f"- {item['nombre']} (${item['precio']})\n"
            
        st.divider()
        # Nota: El total es estimado porque depende del formato de tu CSV
        st.write(f"**Items:** {len(st.session_state.cart)}")
        
        if st.button("🗑️ Vaciar Carrito"):
            clear_cart()
            st.rerun()
            
        # BOTÓN WHATSAPP DEL CARRITO
        msg_final = f"Hola Martín! Quiero comprar esto que armé en la web:\n{pedido_texto}\nRevisame el stock y precio final."
        wa_url = f"https://wa.me/5493401527780?text={urllib.parse.quote(msg_final)}"
        
        st.markdown(f"""
            <a href="{wa_url}" target="_blank" style="
                display: block; width: 100%; background-color: #25D366; color: white;
                text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                👉 FINALIZAR COMPRA
            </a>
        """, unsafe_allow_html=True)
    else:
        st.info("El carrito está vacío.")

# ==========================================
# COLUMNA IZQUIERDA: LUCHO (EL ASESOR)
# ==========================================
with col_chat:
    st.subheader("💬 Asesor Técnico (Lucho)")
    
    # Inyectamos el contexto del carrito en el cerebro de Lucho
    items_en_carrito = ", ".join([i['nombre'] for i in st.session_state.cart])
    contexto_extra = f"\n\nACTUALMENTE EL CLIENTE TIENE EN SU CARRITO: {items_en_carrito if items_en_carrito else 'Nada aún'}."
    
    # Prompt Simplificado para la Demo
    sys_prompt = f"""
    ROL: Eres Lucho, vendedor de Pedro Bravin S.A.
    OBJETIVO: Ayudar al cliente a elegir productos del catálogo que tiene a su derecha.
    
    CONTEXTO CARRITO: {contexto_extra}
    
    INSTRUCCIONES:
    1. Si el cliente pregunta qué comprar, sugiérele productos y dile que los busque en el buscador de la derecha o que presione el botón "Agregar".
    2. Si el cliente ya tiene cosas en el carrito, felicítalo y sugiere complementos.
    3. Tu trabajo es guiar la navegación, no solo chatear.
    
    BASE DE DATOS:
    {df.to_string(index=False) if df is not None else 'Error carga'}
    """

    # Gestión de Chat (Igual que antes pero reducido para esta vista)
    if "messages_shop" not in st.session_state:
        st.session_state.messages_shop = [{"role": "assistant", "content": "Hola 👋. A la derecha tenés la lista de precios. Podés agregar cosas al carrito o preguntarme si tenés dudas técnicas."}]

    for msg in st.session_state.messages_shop:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Preguntale a Lucho..."):
        st.session_state.messages_shop.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=sys_prompt)
            response = model.generate_content([m["content"] for m in st.session_state.messages_shop])
            
            st.session_state.messages_shop.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
