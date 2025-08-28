import streamlit as st
import pandas as pd
from ui_components import (
    display_product_grid,
    display_product_details_page
)
from utils import (
    show_trending_products,
    show_top_5_discounted_products,
    determine_women_shape_by_ratio,
    determine_men_shape_by_logic,
    generate_style_recommendation
)
from rag_system import CustomerRAG, FashionRAG
from virtual_tryon import render_virtual_tryon_modal


def render_page_with_detail_view(content_renderer):
    """
    Acts as a router. Shows the Virtual Try-On modal if activated,
    otherwise shows the main page content.
    """
    # The Virtual Try-On modal takes priority over all other views.
    if st.session_state.get('show_tryon_modal', False):
        render_virtual_tryon_modal()
    else:
        # If the modal is not active, render the normal page content.
        content_renderer()

@st.cache_data
def load_data():
    """Loads all necessary CSV data files."""
    try:
        products_df = pd.read_csv('Product Data.csv')
        sessions_df = pd.read_csv('Session Data.csv')
        transactions_df = pd.read_csv('Transaction Data.csv')
        wishlists_df = pd.read_csv('Cust Data.csv')
        return products_df, sessions_df, transactions_df, wishlists_df
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}. Please make sure all CSV files are in the same directory.")
        return None, None, None, None

@st.cache_data
def load_style_tips():
    """Loads the style tips CSV files."""
    try:
        women_tips = pd.read_csv('women_style_tips.csv')
        men_tips = pd.read_csv('men_style_tips.csv')
        return women_tips, men_tips
    except FileNotFoundError as e:
        st.error(f"Style tip file not found: {e}. Please ensure 'women_style_tips.csv' and 'men_style_tips.csv' are present.")
        return None, None

def display_query_recommendations(query: str, num_to_show: int):
    st.subheader(f"Search Results for '{query}'")
    rag = FashionRAG(index_path="product_index.faiss", details_path="product_details.pkl")
    results = rag.search(query, k=num_to_show)
    if results:
        display_product_grid(results)
    else:
        st.info("No products found for your search. Try a different query!")

def display_history_recommendations(gender: str = None):
    data_files = load_data()
    if not all(df is not None for df in data_files): return
    products_df, sessions_df, transactions_df, wishlists_df = data_files
    rag_system = CustomerRAG(products_df=products_df, index_path="product_index.faiss", details_path="product_details.pkl")
    recommendations = rag_system.get_recommendations_for_customer(customer_id=st.session_state.customer_id, sessions_df=sessions_df, transactions_df=transactions_df, wishlists_df=wishlists_df, gender=gender)
    if recommendations:
        st.subheader("Based on your history")
        display_product_grid(recommendations, num_cols=5)
        st.divider()

def display_trending_products(gender: str = None):
    st.subheader("Trending products")
    products_df, _, _, _ = load_data()
    if products_df is not None:
        products_as_list = products_df.to_dict('records')
        trending = show_trending_products(products_as_list, gender=gender)
        if trending:
            display_product_grid(trending, num_cols=5)

def display_discounted_products(gender: str = None):
    st.subheader("Discounted products")
    products_df, _, _, _ = load_data()
    if products_df is not None:
        products_as_list = products_df.to_dict('records')
        discounted = show_top_5_discounted_products(products_as_list, gender=gender)
        if discounted:
            display_product_grid(discounted, num_cols=5)

def render_style_recommendation_page():
    st.header("👗 AI-Powered Fashion Stylist")
    st.write("Select your gender and enter your measurements (in CM) to get personalized style advice and product recommendations.")

    women_tips_df, men_tips_df = load_style_tips()
    if women_tips_df is None or men_tips_df is None: return

    gender = st.radio("Select your gender:", ('Women', 'Men'), horizontal=True)

    if gender == 'Women':
        st.subheader("Women's Measurements (cm)")
        col1, col2, col3, col4 = st.columns(4)
        with col1: shoulders = st.number_input("Shoulders", min_value=1, value=96)
        with col2: bust = st.number_input("Bust", min_value=1, value=90)
        with col3: waist = st.number_input("Waist", min_value=1, value=70)
        with col4: hips = st.number_input("Hips", min_value=1, value=98)
    else: # Men
        st.subheader("Men's Measurements (cm)")
        col1, col2, col3 = st.columns(3)
        with col1: chest = st.number_input("Chest", min_value=1, value=95)
        with col2: waist = st.number_input("Waist", min_value=1, value=80)
        with col3: hips = st.number_input("Hips", min_value=1, value=90)

    if st.button("✨ Get My Style Recommendation", use_container_width=True):
        body_shape, tips_df = ("unknown", None)
        if gender == 'Women':
            body_shape = determine_women_shape_by_ratio(shoulders, bust, waist, hips)
            tips_df = women_tips_df
        else:
            body_shape = determine_men_shape_by_logic(chest, waist, hips)
            tips_df = men_tips_df

        if body_shape != "unknown" and tips_df is not None:
            st.info(f"Based on your measurements, your calculated body shape is: **{body_shape.title()}**")
            st.divider()
            with st.spinner("Your personal stylist is preparing your recommendations..."):
                ai_advice, search_query = generate_style_recommendation(gender.lower(), body_shape, tips_df)

            st.subheader("Your Personalized Style Advice")
            st.markdown(ai_advice)
            st.divider()

            st.subheader("Shop The Look")
            if search_query:
                rag = FashionRAG(index_path="product_index.faiss", details_path="product_details.pkl")
                with st.spinner("Finding the perfect items for you..."):
                    results = rag.search(query=search_query, k=12)
                    if results:
                        display_product_grid(results)
                    else:
                        st.warning("Could not find specific products matching your style advice at the moment.")
            else:
                st.error("Could not generate a search query from the style advice.")
        else:
            st.error("Could not determine body shape from the measurements provided. Please try different values.")

def render_product_recommendation_page_content():
    st.header("🔍 Product Recommendation")
    query = st.text_input("What are you looking for?")
    num_to_show = st.radio("Number of products to display:", (4, 8, 12), horizontal=True)

    if st.button("Enter"):
        st.session_state['search_query'] = query
        st.session_state['num_to_show'] = num_to_show
        st.rerun()

    gender = st.session_state.get('gender')
    if st.session_state.get('search_query'):
        st.divider()
        display_query_recommendations(st.session_state['search_query'], st.session_state.get('num_to_show', 8))
        st.divider()
        display_history_recommendations(gender=gender)
        display_trending_products(gender=gender)
        st.divider()
        display_discounted_products(gender=gender)

def render_product_recommendation_page():
    render_page_with_detail_view(render_product_recommendation_page_content)

def render_shopping_cart_page():
    st.header("Your Shopping Cart 🛒")
    cart_items = st.session_state.get('cart', [])
    if not cart_items:
        st.info("Your cart is empty. Add some products!")
        return

    if 'selected_items' not in st.session_state or len(st.session_state.selected_items) != len(cart_items):
        st.session_state.selected_items = [False] * len(cart_items)

    select_all_state = all(st.session_state.selected_items) if st.session_state.selected_items else False
    select_all = st.checkbox("Select All / Deselect All", value=select_all_state)
    if select_all and not select_all_state:
        st.session_state.selected_items = [True] * len(cart_items)
        st.rerun()
    elif not select_all and select_all_state:
        st.session_state.selected_items = [False] * len(cart_items)
        st.rerun()

    st.divider()
    total_price, items_to_remove_indices = 0, []
    for i, item in enumerate(cart_items):
        col1, col2, col3, col4 = st.columns([0.5, 1.5, 3, 1])
        with col1:
            is_selected = st.checkbox("", value=st.session_state.selected_items[i], key=f"select_{item['id']}_{i}")
            if is_selected != st.session_state.selected_items[i]:
                st.session_state.selected_items[i] = is_selected
                st.rerun()
        with col2:
            st.image(item['image_url'], width=100)
        with col3:
            st.subheader(item['name'])
            st.write(f"**Price:** {item['Price']}")
            st.write(f"**Color:** {item['Color']}")
        with col4:
            if st.button("Remove", key=f"remove_cart_{item['id']}_{i}"):
                items_to_remove_indices.append(i)
        if st.session_state.selected_items[i]:
            total_price += item.get('raw_price', 0)

    if items_to_remove_indices:
        for index in sorted(items_to_remove_indices, reverse=True):
            st.session_state.cart.pop(index)
            st.session_state.selected_items.pop(index)
        st.rerun()

    st.divider()
    st.subheader(f"Total for selected items: IDR {total_price:,}")
    if st.button("Proceed to Checkout", use_container_width=True):
        st.success("This is a demo. Checkout is not implemented.") if any(st.session_state.selected_items) else st.warning("Please select items to checkout.")

def render_wishlist_page_content():
    st.header("Your Wishlist ❤️")
    wishlist_items = st.session_state.get('wishlist', [])
    if not wishlist_items:
        st.info("Your wishlist is empty. Add some products!")
        return
    display_product_grid(wishlist_items)

def render_wishlist_page(customer_id):
    render_page_with_detail_view(render_wishlist_page_content)