# virtual_tryon.py - Integrated Virtual Try-On Module

import streamlit as st
import replicate
import requests
from PIL import Image
import io
import base64
import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any

class VirtualTryOnSystem:
    """Integrated Virtual Try-On system for the recommendation engine"""
    
    def __init__(self):
        """Initialize the virtual try-on system with API clients"""
        self.client = None
        self.init_replicate_client()
        self.init_cloudinary()
    
    def init_replicate_client(self):
        """Initialize Replicate client with API token"""
        try:
            if "REPLICATE_API_TOKEN" not in st.secrets:
                st.error("Please add your REPLICATE_API_TOKEN to Streamlit secrets")
                return False
            self.client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
            return True
        except Exception as e:
            st.error(f"Failed to initialize Replicate client: {str(e)}")
            return False
    
    def init_cloudinary(self):
        """Initialize Cloudinary configuration"""
        try:
            cloudinary.config(**st.secrets["cloudinary"])
            return True
        except Exception as e:
            st.error(f"Failed to initialize Cloudinary: {str(e)}")
            return False
    
    def upload_image_to_temp_url(self, image: Image.Image) -> str:
        """Convert PIL image to base64 data URL"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def get_product_image(self, product_id: str) -> Optional[Image.Image]:
        """Get product image from Cloudinary"""
        try:
            image_url = cloudinary.CloudinaryImage(product_id).build_url(width=400)
            response = requests.get(image_url)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            return None
        except Exception as e:
            st.error(f"Failed to fetch product image: {str(e)}")
            return None
    
    def determine_garment_category(self, product_name: str, product_data: Dict) -> str:
        """Determine garment category based on product information"""
        product_name_lower = product_name.lower()
        
        # Check product data for category hints
        category_hints = {
            'upperbody': ['shirt', 't-shirt', 'tshirt', 'blouse', 'top', 'jacket', 'blazer', 'sweater', 'hoodie', 'cardigan'],
            'lowerbody': ['pants', 'jeans', 'trousers', 'shorts', 'skirt', 'leggings'],
            'dresses': ['dress', 'gown', 'frock', 'sundress']
        }
        
        for category, keywords in category_hints.items():
            if any(keyword in product_name_lower for keyword in keywords):
                return category
        
        # Default to upperbody if uncertain
        return "upperbody"
    
    def perform_virtual_tryon(self, person_image: Image.Image, product_data: Dict, 
                             garment_category: Optional[str] = None) -> Optional[str]:
        """
        Perform virtual try-on using the product data from the recommendation system
        
        Args:
            person_image: PIL Image of the person
            product_data: Product dictionary from the recommendation system
            garment_category: Optional category override
            
        Returns:
            URL of the result image or None if failed
        """
        if not self.client:
            st.error("Replicate client not initialized")
            return None
        
        try:
            # Get product image
            product_id = product_data.get('id', '')
            clothing_image = self.get_product_image(product_id)
            
            if not clothing_image:
                st.error(f"Could not fetch clothing image for product {product_id}")
                return None
            
            # Determine garment category if not provided
            if not garment_category:
                garment_category = self.determine_garment_category(
                    product_data.get('name', ''), 
                    product_data
                )
            
            # Convert images to data URLs
            person_url = self.upload_image_to_temp_url(person_image)
            clothing_url = self.upload_image_to_temp_url(clothing_image)
            
            # Use OOT Diffusion model for virtual try-on
            with st.spinner(f"Generating virtual try-on for {product_data.get('name', 'product')}..."):
                output = self.client.run(
                    "qiweiii/oot_diffusion_dc:dfda793f95fb788961b38ce72978a350cd7b689c17bbfeb7e1048fc9c7c4849d",
                    input={
                        "seed": 0,
                        "steps": 15,
                        "model_image": person_url,
                        "garment_image": clothing_url,
                        "guidance_scale": 2,
                        "garment_category": garment_category
                    }
                )
            
            return self._process_tryon_result(output)
            
        except Exception as e:
            st.error(f"Error during virtual try-on: {str(e)}")
            return None
    
    def _process_tryon_result(self, result: Any) -> Optional[str]:
        """Process the result from Replicate API"""
        try:
            result_url = None
            
            # Handle different response formats
            if isinstance(result, str):
                if result.startswith(('http://', 'https://')):
                    result_url = result
                    
            elif isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, str) and first_item.startswith(('http://', 'https://')):
                    result_url = first_item
                elif isinstance(first_item, dict):
                    result_url = (first_item.get('url') or 
                                first_item.get('output') or 
                                first_item.get('image'))
                    
            elif isinstance(result, dict):
                result_url = (result.get('url') or 
                            result.get('output') or 
                            result.get('image') or 
                            result.get('result'))
            
            return result_url
            
        except Exception as e:
            st.error(f"Error processing result: {str(e)}")
            return None
    
    def display_tryon_result(self, result_url: str, product_data: Dict):
        """Display the virtual try-on result with download option"""
        try:
            response = requests.get(result_url)
            if response.status_code == 200:
                result_image = Image.open(io.BytesIO(response.content))
                
                st.image(
                    result_image, 
                    caption=f"Virtual Try-On: {product_data.get('name', 'Product')}", 
                    use_column_width=True
                )
                
                # Download button
                buf = io.BytesIO()
                result_image.save(buf, format='PNG')
                st.download_button(
                    label="📥 Download Try-On Result",
                    data=buf.getvalue(),
                    file_name=f"tryon_{product_data.get('id', 'product')}.png",
                    mime="image/png",
                    use_container_width=True
                )
                
                return result_image
            else:
                st.error("Failed to download result image")
                return None
                
        except Exception as e:
            st.error(f"Error displaying result: {str(e)}")
            return None


# Enhanced UI Components with Virtual Try-On Integration
def display_product_card_with_tryon(product: Dict, context: str = "main", 
                                   tryon_system: Optional[VirtualTryOnSystem] = None):
    """Enhanced product card with virtual try-on functionality"""
    
    st.image(product["image_url"], use_container_width=True, output_format='auto')
    
    # Virtual Try-On button (prominent placement)
    if tryon_system and st.button(
        "👕 Virtual Try-On", 
        key=f"tryon_{context}_{product['id']}", 
        use_container_width=True,
        type="primary"
    ):
        # Store the selected product for try-on in session state
        st.session_state['tryon_product'] = product
        st.session_state['show_tryon_modal'] = True
        st.rerun()
    
    # Product details
    st.caption(f"**{product['name']}**")
    st.write(f"**Price:** {product['price']}")
    st.write(f"**Brand:** {product['brand']}")
    
    # Other action buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Add to Cart", key=f"cart_{context}_{product['id']}", use_container_width=True):
            if not any(p['id'] == product['id'] for p in st.session_state.get('cart', [])):
                st.session_state.setdefault('cart', []).append(product)
                st.toast(f"Added {product['name']} to cart!")
            else:
                st.toast(f"{product['name']} is already in your cart.")
                
    with col2:
        if st.button("❤️", key=f"wish_{context}_{product['id']}", use_container_width=True):
            if not any(p['id'] == product['id'] for p in st.session_state.get('wishlist', [])):
                st.session_state.setdefault('wishlist', []).append(product)
                st.toast(f"Added {product['name']} to wishlist!")
            else:
                st.toast(f"{product['name']} is already in your wishlist.")


def render_virtual_tryon_modal():
    """Render the virtual try-on modal when activated"""
    
    if not st.session_state.get('show_tryon_modal', False):
        return
    
    product = st.session_state.get('tryon_product')
    if not product:
        return
    
    # Initialize try-on system
    tryon_system = VirtualTryOnSystem()
    
    st.header(f"👕 Virtual Try-On: {product['name']}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload Your Photo")
        person_file = st.file_uploader(
            "Upload your photo for try-on",
            type=['png', 'jpg', 'jpeg'],
            key="tryon_person_upload"
        )
        
        if person_file is not None:
            person_image = Image.open(person_file)
            st.image(person_image, caption="Your Photo", use_container_width=True)
            
            # Garment category selection
            st.subheader("👔 Garment Category")
            suggested_category = tryon_system.determine_garment_category(
                product.get('name', ''), product
            )
            
            garment_category = st.selectbox(
                "Select garment type:",
                ["upperbody", "lowerbody", "dresses"],
                index=["upperbody", "lowerbody", "dresses"].index(suggested_category)
            )
            
            # Try-on button
            if st.button("🎯 Generate Try-On", type="primary", use_container_width=True):
                result_url = tryon_system.perform_virtual_tryon(
                    person_image, product, garment_category
                )
                
                if result_url:
                    st.session_state['tryon_result_url'] = result_url
                    st.session_state['tryon_result_product'] = product
                    st.rerun()
    
    with col2:
        st.subheader("👔 Product Details")
        st.image(product["image_url"], caption=product["name"], use_container_width=True)
        st.write(f"**Price:** {product['price']}")
        st.write(f"**Brand:** {product['brand']}")
        st.write(f"**Color:** {product['color']}")
        
        # Display try-on result if available
        if st.session_state.get('tryon_result_url'):
            st.subheader("✨ Try-On Result")
            tryon_system.display_tryon_result(
                st.session_state['tryon_result_url'],
                st.session_state.get('tryon_result_product', product)
            )
    
    # Close modal button
    if st.button("❌ Close Try-On", use_container_width=True):
        # Clear try-on related session state
        for key in ['show_tryon_modal', 'tryon_product', 'tryon_result_url', 'tryon_result_product']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# Integration with existing recommendation system
def get_tryon_recommendations(tryon_system: VirtualTryOnSystem, base_product: Dict, 
                            rag_system) -> list:
    """Get recommendations based on the product used for virtual try-on"""
    
    # Create a search query based on the tried-on product
    query = f"{base_product.get('name', '')} {base_product.get('color', '')} {base_product.get('gender', '')}"
    
    try:
        recommendations = rag_system.search(query, k=4)
        return recommendations
    except Exception as e:
        st.error(f"Failed to get try-on recommendations: {str(e)}")
        return []


# Updated utils functions
def initialize_session_state_with_tryon():
    """Enhanced session state initialization including virtual try-on states"""
    
    # Existing initialization
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'customer_id' not in st.session_state:
        st.session_state.customer_id = None
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'wishlist' not in st.session_state:
        st.session_state.wishlist = []
    
    # Virtual try-on states
    if 'show_tryon_modal' not in st.session_state:
        st.session_state.show_tryon_modal = False
    if 'tryon_product' not in st.session_state:
        st.session_state.tryon_product = None
    if 'tryon_result_url' not in st.session_state:
        st.session_state.tryon_result_url = None
    if 'tryon_result_product' not in st.session_state:
        st.session_state.tryon_result_product = None