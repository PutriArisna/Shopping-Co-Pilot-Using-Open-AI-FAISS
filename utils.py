import streamlit as st
import random
import cloudinary
import re
import ast
import pandas as pd
import openai

# --- NEW: Function to standardize gender terms ---
def normalize_gender(gender_string):
    """Converts different gender representations ('Male', 'men', etc.) to a standard form."""
    if isinstance(gender_string, str):
        g_lower = gender_string.lower()
        if g_lower in ['male','men']:
            return 'Men'
        if g_lower in ['female','women']:
            return 'Women'
    return gender_string 

def initialize_session_state():
    """Enhanced session state initialization including virtual try-on states."""
    # Existing variables
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'customer_id' not in st.session_state: st.session_state.customer_id = None
    if 'cart' not in st.session_state: st.session_state.cart = []
    if 'wishlist' not in st.session_state: st.session_state.wishlist = []
    
    # OLD detail page variable (can be removed or kept for safety)
    if 'selected_product' not in st.session_state: st.session_state.selected_product = None
    
    # NEW virtual try-on variables
    if 'show_tryon_modal' not in st.session_state: st.session_state.show_tryon_modal = False
    if 'tryon_product' not in st.session_state: st.session_state.tryon_product = None
    if 'tryon_result_url' not in st.session_state: st.session_state.tryon_result_url = None
    if 'tryon_result_product' not in st.session_state: st.session_state.tryon_result_product = None

def determine_women_shape_by_ratio(shoulders, bust, waist, hips):
    if any(m <= 0 for m in [shoulders, bust, waist, hips]): return "unknown"
    if (waist / shoulders) >= 1.05 and (waist / bust) >= 1.05: return "Apple"
    elif (shoulders / hips) >= 1.05 or (bust / hips) >= 1.05: return "Inverted Triangle"
    elif (hips / shoulders) >= 1.05 or (hips / bust) >= 1.05: return "Pear"
    elif (waist / shoulders) >= 0.75 and (waist / bust) >= 0.75: return "Rectangle"
    elif ((waist / shoulders) <= 0.75 or (waist / bust) <= 0.75) and (waist / hips) <= 0.75: return "Hourglass"
    else: return "unknown"

def determine_men_shape_by_logic(chest, waist, hips):
    if (76.2 <= chest <= 86.36) and (76.2 <= waist <= 86.36) and (76.2 <= hips <= 86.36): return "Rectangle"
    elif (81.28 <= chest <= 91.44) and (81.28 <= waist <= 91.44) and (81.28 <= hips <= 91.44): return "Oval"
    elif (71.12 <= chest <= 81.28) and (76.2 <= waist <= 86.36) and (86.36 <= hips <= 96.52): return "Triangle"
    elif (91.44 <= chest <= 101.6) and (71.12 <= waist <= 81.28) and (71.12 <= hips <= 81.28): return "Inverted Triangle"
    elif (91.44 <= chest <= 101.6) and (76.2 <= waist <= 86.36) and (86.36 <= hips <= 96.52): return "Trapezoid"
    else: return "unknown"

@st.cache_data
def generate_style_recommendation(gender, body_shape, _tips_df):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    try:
        style_rules = _tips_df[_tips_df['name'] == body_shape].iloc[0].to_dict()
    except IndexError:
        return f"No styling tips found for the '{body_shape}' body shape.", ""
    rag_context = "\n".join([f"- {key.replace('_', ' ').title()}: {value}" for key, value in style_rules.items() if key != 'name'])
    search_query = " ".join(style_rules.values())
    prompt = f"""
    Act as a friendly and encouraging personal fashion stylist.
    A user has been identified with a '{body_shape}' body shape.

    Based *only* on the following styling rules, provide a personalized and encouraging style recommendation.
    Choose one of the products in styling tips emphasize why with your knowledge why certain product work well for them based on the provided tips.
    Dont make the recommended style and avoid style in one line, separate them, and make it point for each recommendation product.
    Make sure to follow this format below:
    **Styling Rules for {body_shape}:**
    **1. for tops:** describe the necklines, shoulder, how the fit(e.g,loose/fitted), tops cloud be outers like jacket/sweater keep matching the styling tips
    **2. for pants:** describe the cutting (e.g.,mid/low/high rise)
    **3. etc
    **Avoids:**
    - for this type of body, please avoid (e.g., flare pants) because ..
    -
    -
    """
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": "You are a helpful fashion assistant."}, {"role": "user", "content": prompt}], max_tokens=400, temperature=0.7)
        recommendation = response.choices[0].message.content
        return recommendation, search_query
    except Exception as e:
        return f"An error occurred: {e}", ""

def format_product_dictionary(p):
    product_dict = p.copy()
    product_dict['id'] = product_dict.get("Product_ID")
    product_dict['name'] = product_dict.get("Product_Name", "N/A")
    product_dict['price'] = f"IDR {product_dict.get('Price', 0):,}"
    product_dict['raw_price'] = product_dict.get('Price', 0)
    product_dict['image_url'] = cloudinary.CloudinaryImage(product_dict.get("Product_ID")).build_url(width=400)
    product_dict['reviews'] = product_dict.get('Number_of_Reviews', 0)
    product_dict['category'] = product_dict.get('Category', 'N/A')
    product_dict['material'] = product_dict.get('Material', 'N/A')
    product_dict['size'] = product_dict.get('Size', '')
    product_dict['description'] = product_dict.get('Description', 'No description available.')
    product_dict['gender'] = product_dict.get('Gender_Orientation', "N/A")
    return product_dict

def show_trending_products(products_list: list, gender: str = None):
    target_products = products_list
    if gender:
        # Use the normalization function for a reliable comparison
        normalized_user_gender = normalize_gender(gender)
        target_products = [p for p in products_list if normalize_gender(p.get('Gender_Orientation')) == normalized_user_gender]

    def calculate_trending_score(p):
        return (p.get('Rating', 0) * 0.6) + (p.get('Number_of_Reviews', 0) * 0.2) + (p.get('Trending_Score', 0) * 0.2)
    
    sorted_products = sorted(target_products, key=calculate_trending_score, reverse=True)[:5]
    return [format_product_dictionary(p) for p in sorted_products]

def show_top_5_discounted_products(products_list: list, gender: str = None):
    target_products = products_list
    if gender:
        # Use the normalization function for a reliable comparison
        normalized_user_gender = normalize_gender(gender)
        target_products = [p for p in products_list if normalize_gender(p.get('Gender_Orientation')) == normalized_user_gender]

    def get_discount_percentage(p):
        discount_str = p.get('Discount', '0%')
        numeric_part = re.search(r'\d+', str(discount_str))
        return int(numeric_part.group(0)) if numeric_part else 0
        
    sorted_products = sorted(target_products, key=get_discount_percentage, reverse=True)[:5]
    return [format_product_dictionary(p) for p in sorted_products]