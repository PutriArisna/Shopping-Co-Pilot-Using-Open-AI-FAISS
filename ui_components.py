import streamlit as st

def display_product_details_page(product):
    """Displays a full-page view with comprehensive product details."""
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.image(product["image_url"], use_container_width=True)

    with col2:
        st.markdown(f"### {product.get('name', 'N/A')}")
        st.markdown(f"<h4 style='color:red; font-weight:bold;'>{product.get('price', 'IDR 0')}</h4>", unsafe_allow_html=True)
        st.divider()
        
        st.write(f"**Brand:** {product.get('brand', 'N/A')}")
        st.write(f"**Category:** {product.get('category', 'N/A')}")
        st.write(f"**Color:** {product.get('color', 'N/A')}")
        st.write(f"**Gender:** {product.get('gender', 'N/A')}")
        st.write(f"**Material:** {product.get('material', 'N/A')}")
        
        reviews = product.get('reviews', 0)
        if reviews > 0:
            st.write(f"**Rating:** ⭐ {product.get('rating', 0):.1f} ({reviews} reviews)")
        
        st.divider()

        st.write("**Select Size:**")
        available_sizes = [size.strip() for size in product.get('size', '').split(',') if size.strip()]
        if available_sizes:
            size_cols = st.columns(len(available_sizes))
            for i, size in enumerate(available_sizes):
                with size_cols[i]:
                    st.button(size, key=f"size_{product['id']}_{size}")
        else:
            st.info("Size information not available.")

    st.divider()
    st.write("**Description:**")
    st.write(product.get('description', 'No description available.'))
    st.divider()

    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Add to Cart", key=f"cart_detail_{product['id']}", use_container_width=True):
             st.toast("Added to cart!")
    with action_cols[1]:
        if st.button("Add to Wishlist", key=f"wish_detail_{product['id']}", use_container_width=True):
             st.toast("Added to wishlist!")
    with action_cols[2]:
        if st.button("Visual Try-On", key=f"tryon_detail_{product['id']}", use_container_width=True):
             st.toast("Loading Visual Try-On...")


def display_product_card(product, context="main"):
    """
    Displays a single product card with icon-style action buttons and styled price.
    """
    with st.container(border=True):
        # Product Image
        st.image(product["image_url"], use_container_width=True, output_format='auto')

        # Action buttons row with icons
        action_cols = st.columns([1, 1, 1])
        with action_cols[0]:
            if st.button("📷", key=f"tryon_{context}_{product['id']}", use_container_width=True):
                st.session_state['tryon_product'] = product
                st.session_state['show_tryon_modal'] = True
                st.rerun()
        with action_cols[1]:
            if st.button("🛒", key=f"cart_{context}_{product['id']}", use_container_width=True):
                if not any(p['id'] == product['id'] for p in st.session_state.get('cart', [])):
                    st.session_state.setdefault('cart', []).append(product)
                    st.toast(f"Added {product['name']} to cart!")
                    st.rerun()
                else:
                    st.toast(f"{product['name']} is already in your cart.")
        with action_cols[2]:
            if st.button("❤️", key=f"wish_{context}_{product['id']}", use_container_width=True):
                if not any(p['id'] == product['id'] for p in st.session_state.get('wishlist', [])):
                    st.session_state.setdefault('wishlist', []).append(product)
                    st.toast(f"Added {product['name']} to wishlist!")
                    st.rerun()
                else:
                    st.toast(f"{product['name']} is already in your wishlist.")

        # Product name
        st.subheader(product.get("name", "N/A"))

        # Price display (support discount)
        old_price = product.get('old_price')
        current_price = product.get('price', 'IDR 0')
        if old_price and old_price != current_price:
            st.markdown(f"<span style='color:grey;text-decoration:line-through;'>{old_price}</span> "
                        f"<span style='color:red;font-weight:bold;'>{current_price}</span>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:red;font-weight:bold;'>{current_price}</span>",
                        unsafe_allow_html=True)

        # Brand, color, gender
        st.caption(f"{product.get('brand', '')} | {product.get('color', '')} | {product.get('gender', '')}")

        # Reviews
        reviews = product.get('reviews', 0)
        if reviews > 0:
            st.write(f"⭐ {product.get('rating', 0):.1f} ({reviews} reviews)")


def display_product_grid(products, num_cols=4):
    """Displays a grid of products with a configurable number of columns."""
    if not products:
        st.info("No products to display.")
        return
    
    # Use the num_cols argument to set the grid width
    effective_num_cols = min(len(products), num_cols)
    
    for i in range(0, len(products), effective_num_cols):
        cols = st.columns(effective_num_cols)
        row_products = products[i:i+effective_num_cols]
        for j, product in enumerate(row_products):
            with cols[j]:
                display_product_card(product, context=f"grid_{i}_{j}")