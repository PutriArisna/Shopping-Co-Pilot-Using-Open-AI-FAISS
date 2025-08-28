import streamlit as st
import uuid
import pandas as pd
import ast
import cloudinary
from utils import initialize_session_state
from pages import (
    render_style_recommendation_page,
    render_product_recommendation_page,
    render_shopping_cart_page,
    render_wishlist_page
)

@st.cache_data
def load_data():
    """Loads all necessary CSV data files."""
    try:
        products_df = pd.read_csv('Product Data.csv')
        sessions_df = pd.read_csv('Session Data.csv')
        transactions_df = pd.read_csv('Transaction Data.csv')
        cust_df = pd.read_csv('Cust Data.csv')
        return products_df, sessions_df, transactions_df, cust_df
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}. Please make sure all CSV files are in the same directory.")
        return None, None, None, None

# --- Main App Interface ---
st.set_page_config(
    page_title="AI Fashion Recommendation Engine",
    page_icon="👕",
    layout="wide"
)


# --- Login/Signup Flow ---
if not st.session_state.get('logged_in', False):
    st.title("Welcome to the AI Fashion Recommendation Engine 🛍️👕")
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Experience the Future of Fashion Shopping
        - 🔍 **Smart Recommendations** - AI-powered product suggestions
        - 👗 **Style Guidance** - Personalized fashion advice based on your body type  
        - 👕 **Virtual Try-On** - See how clothes look on you before buying
        - 🛒 **Smart Shopping** - Enhanced cart and wishlist management
        """)
    with col2:
        st.image("https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&q=80", 
                caption="Your AI Fashion Assistant")
    
    # Login/Signup tabs
    tab1, tab2 = st.tabs(["🔑 Login", "👤 New Account"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            customer_id_input = st.text_input(
                "Enter your Customer ID", 
                placeholder="e.g., CUST0001"
            )
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submitted:
                prod_df, _, _, cust_df = load_data()
                if not customer_id_input:
                    st.error("Please enter a Customer ID.")
                elif cust_df is not None and customer_id_input not in cust_df['Customer_ID'].values:
                    st.error("Customer ID not found. Please check your ID or create a new account.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.customer_id = customer_id_input

                    if cust_df is not None and prod_df is not None:
                        try:
                            customer_data = cust_df[cust_df['Customer_ID'] == customer_id_input].iloc[0]
                            st.session_state['gender'] = customer_data.get('Gender')

                            # Load Cart
                            cart_ids_str = customer_data['Abandoned Cart']
                            cart_product_ids = ast.literal_eval(cart_ids_str)
                            cart_products = [prod_df[prod_df['Product_ID'] == prod_id].iloc[0].to_dict() for prod_id in cart_product_ids]
                            st.session_state.cart = [
                                {**p,
                                 "id": p.get("Product_ID"), "name": p.get("Product_Name", "N/A"),
                                 "price": f"IDR {p.get('Price', 0):,}", "raw_price": p.get('Price', 0),
                                 "image_url": cloudinary.CloudinaryImage(p.get("Product_ID")).build_url(width=400)
                                } for p in cart_products
                            ]

                            # Load Wishlist
                            wishlist_ids_str = customer_data['Wishlist Items']
                            wishlist_product_ids = ast.literal_eval(wishlist_ids_str)
                            wishlist_products = [prod_df[prod_df['Product_ID'] == prod_id].iloc[0].to_dict() for prod_id in wishlist_product_ids]
                            st.session_state.wishlist = [
                                {**p,
                                 "id": p.get("Product_ID"), "name": p.get("Product_Name", "N/A"),
                                 "price": f"IDR {p.get('Price', 0):,}", "raw_price": p.get('Price', 0),
                                 "image_url": cloudinary.CloudinaryImage(p.get("Product_ID")).build_url(width=400)
                                } for p in wishlist_products
                            ]
                        except (IndexError, ValueError, SyntaxError):
                            st.session_state.cart = []
                            st.session_state.wishlist = []
                    st.rerun()

    with tab2:
        st.subheader("Join Our Fashion Community!")
        st.write("Get personalized recommendations and try on clothes virtually.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🆕 Create New Account", use_container_width=True, type="primary"):
                new_id = "CUST" + str(uuid.uuid4())[:4].upper()
                st.session_state.logged_in = True
                st.session_state.customer_id = new_id
                st.session_state.cart = []
                st.session_state.wishlist = []
                st.success(f"Welcome! Your new Customer ID is: **{new_id}** 🎉")
                st.info("Please save this ID for future logins. Redirecting to the app...")
                st.balloons()
                st.rerun()
        
        with col2:
            st.info("💡 **What you get:**\n- Personalized recommendations\n- Virtual try-on technology\n- Smart shopping features\n- Style guidance")

# --- Full Application (after login) ---
else:
    # --- Sidebar ---
    st.sidebar.title("Welcome!")
    st.sidebar.success(f"Logged in as: `{st.session_state.customer_id}`")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.sidebar.divider()

    cart_count = len(st.session_state.get('cart', []))
    wishlist_count = len(st.session_state.get('wishlist', []))

    page = st.sidebar.radio(
        "Choose a page",
        [
            "Product Recommendation",
            "Fashion Style Recommendation",
            f"Shopping Cart 🛒 ({cart_count})",
            f"Wishlist ❤️ ({wishlist_count})"
        ]
    )

    # --- Page Routing ---
    if page == "Fashion Style Recommendation":
        render_style_recommendation_page()
    elif page == "Product Recommendation":
        render_product_recommendation_page()
    elif page.startswith("Shopping Cart"):
        render_shopping_cart_page()
    elif page.startswith("Wishlist"):
        render_wishlist_page(st.session_state.customer_id)