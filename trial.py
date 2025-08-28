import streamlit as st
import random
import uuid

# --- Helper Functions and Placeholder Data ---

def determine_body_type(bust, waist, high_hip, hips):
    """Determines body type based on measurements."""
    if bust == 0 or waist == 0 or hips == 0 or high_hip == 0:
        return "Unknown"
    
    # Pear (Triangle): Hips are the widest point.
    if hips > bust * 1.05 and hips > waist * 1.05:
        return "Pear"
    # Inverted Triangle: Bust/shoulders are wider than hips.
    if bust > hips * 1.05:
        return "Inverted Triangle"
    # Hourglass: Bust and hips are similar, with a clearly defined waist.
    if abs(bust - hips) <= 4 and waist < bust * 0.8 and waist < hips * 0.8:
        return "Hourglass"
    # Apple: Waist is wider than or very close to bust and hips.
    if waist >= bust * 0.9 and waist >= hips * 0.9:
        return "Apple"
    # Rectangle: Measurements are relatively similar without a defined waist.
    if abs(bust - hips) < 5 and abs(waist - bust) < 10:
        return "Rectangle"
        
    return "Rectangle" # Default if no other category fits perfectly

def get_placeholder_products(count):
    """Generates a list of placeholder product dictionaries."""
    products = []
    brands = ["BrandA", "BrandB", "BrandC", "ChicWear", "Moderno"]
    colors = ["Red", "Blue", "Green", "Black", "White", "Beige"]
    genders = ["Unisex", "Men's", "Women's"]
    for i in range(count):
        raw_price = random.randint(150, 1500) * 1000
        formatted_price = f"IDR {raw_price:,}"
        product = {
            "id": f"prod_{i+1}_{random.randint(1000,9999)}",
            "name": f"Product Name {i+1}",
            "price": formatted_price,
            "raw_price": raw_price,
            "brand": random.choice(brands),
            "color": random.choice(colors),
            "gender": random.choice(genders),
            "image_url": f"https://placehold.co/400x500/F5F5F5/333333?text=Product+{i+1}"
        }
        products.append(product)
    return products

def display_product_card(product, context="main"):
    """Displays a single product card with all action buttons."""
    st.image(product["image_url"], use_column_width='always')
    
    if st.button("Visual Try-On", key=f"tryon_{context}_{product['id']}", use_container_width=True):
        st.toast(f"Loading Visual Try-On for {product['name']}...")

    st.caption(f"**{product['name']}**")
    st.write(f"**Price:** {product['price']}")
    st.write(f"**Brand:** {product['brand']}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Add to Cart", key=f"cart_{context}_{product['id']}", use_container_width=True):
            if not any(p['name'] == product['name'] for p in st.session_state.cart):
                st.session_state.cart.append(product)
                st.toast(f"Added {product['name']} to cart!")
            else:
                st.toast(f"{product['name']} is already in your cart.")
    with col2:
        if st.button("❤️", key=f"wish_{context}_{product['id']}", use_container_width=True):
            if not any(p['name'] == product['name'] for p in st.session_state.wishlist):
                st.session_state.wishlist.append(product)
                st.toast(f"Added {product['name']} to wishlist!")
            else:
                st.toast(f"{product['name']} is already in your wishlist.")

def display_product_grid(products):
    """Displays a grid of products."""
    if not products:
        st.info("No products to display.")
        return
    for i in range(0, len(products), 4):
        cols = st.columns(4)
        row_products = products[i:i+4]
        for j, product in enumerate(row_products):
            with cols[j]:
                display_product_card(product, context=f"grid_{i}_{j}")

def display_single_row_products(title, num_products=4):
    """Displays a single row of products."""
    st.subheader(title)
    products = get_placeholder_products(num_products)
    cols = st.columns(num_products)
    for i, product in enumerate(products):
        with cols[i]:
            display_product_card(product, context=f"row_{title}_{i}")

# --- State Management Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.customer_id = None
    st.session_state.cart = get_placeholder_products(2) 
    st.session_state.wishlist = []
            
# --- Main App Interface ---
st.set_page_config(layout="wide")

# --- Login/Signup Flow ---
if not st.session_state.logged_in:
    st.title("Welcome to the Recommendation Engine 🛍️")
    login_choice = st.radio("Are you a new or returning customer?", ('I am a new member', 'I want to log in'), horizontal=True, label_visibility="collapsed")
    if login_choice == 'I want to log in':
        with st.form("login_form"):
            customer_id_input = st.text_input("Enter your Customer ID")
            submitted = st.form_submit_button("Login")
            if submitted:
                if customer_id_input:
                    st.session_state.logged_in = True
                    st.session_state.customer_id = customer_id_input
                    st.rerun()
                else:
                    st.error("Please enter a valid Customer ID.")
    elif login_choice == 'I am a new member':
        st.write("Click the button below to get your new Customer ID.")
        if st.button("Create New Account"):
            new_id = str(uuid.uuid4())[:8]
            st.session_state.logged_in = True
            st.session_state.customer_id = new_id
            st.success(f"Welcome! Your new Customer ID is: **{new_id}**")
            st.info("Please save this ID for future logins. The app will now load.")
            st.rerun()

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
    st.sidebar.title("Navigation")
    cart_count = len(st.session_state.cart)
    wishlist_count = len(st.session_state.wishlist)
    page = st.sidebar.radio("Choose a page", ["Fashion Style Recommendation", "Product Recommendation", f"Shopping Cart 🛒 ({cart_count})", f"Wishlist ❤️ ({wishlist_count})"])
    st.title("🛍️ Recommendation Engine")

    # --- Page 1: Fashion Style Recommendation ---
    if page == "Fashion Style Recommendation":
        st.header("👗 Fashion Style Recommendation")
        st.write("Enter your measurements in centimeters to determine your body type and get a recommendation.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            bust = st.number_input("Bust (cm)", min_value=0, value=90)
        with col2:
            waist = st.number_input("Waist (cm)", min_value=0, value=70)
        with col3:
            high_hip = st.number_input("High Hips (cm)", min_value=0, value=85)
        with col4:
            hips = st.number_input("Hips (cm)", min_value=0, value=95)
            
        if st.button("Get Recommendation"):
            body_type = determine_body_type(bust, waist, high_hip, hips)
            st.info(f"Based on your measurements, your determined body type is: **{body_type}**")
            st.subheader("Your Personalized Recommendation")
            
            recommendations = {
                "Pear": ("https://images.unsplash.com/photo-1594616532454-9139e8841433?w=500&q=80", "For a Pear body shape, emphasize your waist and arms. Try A-line skirts, well-fitting tops, and statement necklaces."),
                "Apple": ("https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=500&q=80", "For an Apple body shape, elongate your torso. V-necks, flowy tops, and straight-leg pants are great choices."),
                "Hourglass": ("https://images.unsplash.com/photo-1529391409740-59f2cea08bc6?w=500&q=80", "For an Hourglass figure, highlight your curves. Body-con dresses, high-waisted skirts, and belted outfits will look fantastic."),
                "Rectangle": ("https://images.unsplash.com/photo-1550928434-4a02a83523e4?w=500&q=80", "For a Rectangle body shape, create the illusion of curves. Peplum tops, ruffled details, and A-line cuts work well."),
                "Inverted Triangle": ("https://images.unsplash.com/photo-1572804013427-4d7ca7268211?w=500&q=80", "For an Inverted Triangle shape, add volume to your lower body. Wide-leg pants, full skirts, and bright-colored bottoms are excellent."),
                "Unknown": ("https://images.unsplash.com/photo-1485230895905-4789ba55643a?w=500&q=80", "Please enter valid measurements to get a recommendation.")
            }
            
            image_url, text = recommendations.get(body_type)
            
            st.image(image_url, width=400)
            st.markdown(f"**Style Tip:** {text}")
            st.divider()
            display_single_row_products("Shop The Look")

    # --- Page 2: Product Recommendation ---
    elif page == "Product Recommendation":
        st.header("🔍 Product Recommendation")
        query = st.text_input("What are you looking for?", "e.g., 'casual summer dress'")
        num_to_show = st.radio("Number of products to display:", (4, 8, 12), horizontal=True)
        st.divider()
        st.subheader(f"Search Results for '{query}'")
        main_products = get_placeholder_products(num_to_show)
        display_product_grid(main_products)
        st.divider()
        display_single_row_products("Based on your history")
        st.divider()
        display_single_row_products("Trending products")

    # --- Page 3: Shopping Cart ---
    elif page.startswith("Shopping Cart"):
        st.header("Your Shopping Cart 🛒")
        if not st.session_state.cart:
            st.info("Your cart is empty. Add some products!")
        else:
            total_price = 0
            selected_items_count = 0
            
            select_all = st.checkbox("Select All / Deselect All")
            st.divider()

            items_to_keep = []
            
            for i, item in enumerate(st.session_state.cart):
                col1, col2, col3, col4 = st.columns([0.5, 1, 2.5, 1])
                
                with col1:
                    is_selected = st.checkbox("", value=select_all, key=f"select_{item['id']}_{i}")
                
                with col2:
                    st.image(item['image_url'], width=100)
                
                with col3:
                    st.subheader(item['name'])
                    st.write(f"**Price:** {item['price']}")
                    st.write(f"**Color:** {item['color']}")
                
                remove_button_pressed = False
                with col4:
                    if st.button("Remove", key=f"remove_cart_{item['id']}_{i}"):
                        remove_button_pressed = True

                if not remove_button_pressed:
                    items_to_keep.append(item)
                    if is_selected:
                        total_price += item['raw_price']
                        selected_items_count += 1
            
            if len(items_to_keep) != len(st.session_state.cart):
                st.session_state.cart = items_to_keep
                st.rerun()

            st.divider()
            st.subheader(f"Total for {selected_items_count} selected items: IDR {total_price:,}")
            if st.button("Proceed to Checkout", use_container_width=True):
                if selected_items_count > 0:
                    st.success("This is a demo. Checkout is not implemented.")
                else:
                    st.warning("Please select items to checkout.")

    # --- Page 4: Wishlist ---
    elif page.startswith("Wishlist"):
        st.header("Your Wishlist ❤️")
        if not st.session_state.wishlist:
            st.info("Your wishlist is empty. Add some products you love!")
        else:
            items_to_keep_wishlist = []
            for i, item in enumerate(st.session_state.wishlist):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.image(item['image_url'], width=100)
                with col2:
                    st.subheader(item['name'])
                    st.write(f"Price: {item['price']}")
                
                remove_button_pressed = False
                with col3:
                    if st.button("Remove", key=f"remove_wish_{item['id']}_{i}"):
                        remove_button_pressed = True

                if not remove_button_pressed:
                    items_to_keep_wishlist.append(item)

            if len(items_to_keep_wishlist) != len(st.session_state.wishlist):
                st.session_state.wishlist = items_to_keep_wishlist
                st.rerun()
            
            for _ in st.session_state.wishlist:
                 st.divider()
