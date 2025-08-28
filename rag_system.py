import streamlit as st
import pandas as pd
import numpy as np
import faiss
import pickle
import os
import ast
from typing import List, Dict
import openai
import cloudinary
import cloudinary.uploader
import cloudinary.api
from utils import normalize_gender # Import the normalization function

class BaseRAG:
    def __init__(self):
        try:
            self.client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            cloudinary.config(**st.secrets["cloudinary"])
            self.embedding_model = "text-embedding-3-large"
        except Exception as e:
            st.error(f"Failed to initialize API clients: {e}")
            self.client = None

    def load_artifacts(self, index_path: str, details_path: str):
        try:
            self.index = faiss.read_index(index_path)
            with open(details_path, "rb") as f:
                self.product_details = pickle.load(f)
        except Exception as e:
            st.error(f"Failed to load model artifacts: {e}")
            self.index = None
            self.product_details = None

class FashionRAG(BaseRAG):
    def __init__(self, index_path: str, details_path: str):
        super().__init__()
        self.load_artifacts(index_path, details_path)

    def search(self, query: str, k: int = 8, gender: str = None) -> List[Dict]:
        """Search for relevant items using a normalized gender term in the query."""
        if self.index is None or self.client is None: return []

        # 1. Normalize the gender term ('Male' -> 'Men')
        normalized_gender = normalize_gender(gender)
        # 2. Prepend the corrected gender to the query as a "soft hint"
        search_query = f"{normalized_gender} {query}" if normalized_gender else query
        
        try:
            response = self.client.embeddings.create(input=[search_query], model=self.embedding_model)
            query_vector = np.array([response.data[0].embedding]).astype('float32')
            
            # 3. Removed the strict IDSelector filter to search the entire index
            distances, indices = self.index.search(query_vector, k)

        except Exception as e:
            st.error(f"Error during product search: {e}")
            return []

        results = []
        for idx in indices[0]:
            if idx == -1: continue
            item = self.product_details[idx]
            product_id = item.get('Product_ID', f"rec_{idx}")
            results.append({
                "id": product_id, "name": item.get('Product_Name', 'N/A'),
                "price": f"IDR {item.get('Price', 0):,}", "raw_price": item.get('Price', 0),
                "brand": item.get('Brand', 'N/A'), "color": item.get('Color', 'N/A'),
                "gender": item.get('Gender_Orientation', 'N/A'),
                "image_url": cloudinary.CloudinaryImage(product_id).build_url(width=400),
                "rating": item.get('Rating', 0), "reviews": item.get('Number_of_Reviews', 0),
                "category": item.get('Category', 'N/A'), "description": item.get('Description', 'No description available.'),
                "material": item.get('Material', 'N/A'), "size": item.get('Size', ''),
            })
        return results

class CustomerRAG(BaseRAG):
    def __init__(self, products_df: pd.DataFrame, index_path: str, details_path: str):
        super().__init__()
        self.products_df = products_df
        self.load_artifacts(index_path, details_path)

    def _get_product_details(self, product_ids: list) -> str:
        if not product_ids or not isinstance(product_ids, list): return ""
        names = self.products_df[self.products_df['Product_ID'].isin(product_ids)]['Product_Name'].tolist()
        return ", ".join(names)

    def build_customer_profile(self, customer_id: str, sessions_df: pd.DataFrame, transactions_df: pd.DataFrame, wishlists_df: pd.DataFrame) -> str:
        profile_parts = []
        try:
            def safe_literal_eval(val):
                try: return ast.literal_eval(val)
                except (ValueError, SyntaxError): return []
            sessions_df['Clicked_Product_IDs'] = sessions_df['Clicked_Product_IDs'].apply(safe_literal_eval)
            cust_sessions = sessions_df[sessions_df['Customer_ID'] == customer_id].head(7)
            if not cust_sessions.empty:
                searches = cust_sessions['Search_Queries'].unique()
                profile_parts.append(f"Searched for: {', '.join(searches)}.")
                clicked_ids = np.concatenate(cust_sessions['Clicked_Product_IDs'].values).tolist()
                if clicked_ids: profile_parts.append(f"Interested in: {self._get_product_details(clicked_ids)}.")
            transactions_df['Purchased_Product_IDs'] = transactions_df['Purchased_Product_IDs'].apply(safe_literal_eval)
            cust_transactions = transactions_df[transactions_df['Customer_ID'] == customer_id].head(7)
            if not cust_transactions.empty:
                purchased_ids = np.concatenate(cust_transactions['Purchased_Product_IDs'].values).tolist()
                if purchased_ids: profile_parts.append(f"Purchased: {self._get_product_details(purchased_ids)}.")
            wishlists_df['Wishlist Items'] = wishlists_df['Wishlist Items'].apply(safe_literal_eval)
            cust_wishlists = wishlists_df[wishlists_df['Customer_ID'] == customer_id]
            if not cust_wishlists.empty:
                wishlist_ids = np.concatenate(cust_wishlists['Wishlist Items'].values).tolist()
                if wishlist_ids: profile_parts.append(f"Wants: {self._get_product_details(wishlist_ids)}.")
        except Exception as e:
            return f"Error building profile: {e}"
        return " ".join(profile_parts) if profile_parts else "No activity data found"

    def get_recommendations_for_customer(self, customer_id: str, sessions_df: pd.DataFrame, transactions_df: pd.DataFrame, wishlists_df: pd.DataFrame, gender: str = None):
        customer_profile = self.build_customer_profile(customer_id, sessions_df, transactions_df, wishlists_df)
        if "No activity data" in customer_profile or "Error" in customer_profile: return []
        if self.index is None or self.client is None: return []
        
        # 1. Normalize the gender term ('Male' -> 'Men')
        normalized_gender = normalize_gender(gender)
        # 2. Prepend the corrected gender to the profile as a "soft hint"
        search_profile = f"{normalized_gender} {customer_profile}" if normalized_gender else customer_profile

        response = self.client.embeddings.create(input=[search_profile], model=self.embedding_model)
        query_vector = np.array([response.data[0].embedding]).astype('float32')
        
        # 3. Removed the strict IDSelector filter to search the entire index
        distances, indices = self.index.search(query_vector, 5)

        results = []
        for idx in indices[0]:
            if idx == -1: continue
            item = self.product_details[idx]
            product_id = item.get('Product_ID', f"rec_{idx}")
            results.append({
                "id": product_id, "name": item.get('Product_Name', 'N/A'),
                "price": f"IDR {item.get('Price', 0):,}", "raw_price": item.get('Price', 0),
                "brand": item.get('Brand', 'N/A'), "color": item.get('Color', 'N/A'),
                "gender": item.get('Gender_Orientation', 'N/A'),
                "image_url": cloudinary.CloudinaryImage(product_id).build_url(width=400),
                "rating": item.get('Rating', 0), "reviews": item.get('Number_of_Reviews', 0),
                "category": item.get('Category', 'N/A'), "description": item.get('Description', 'No description available.'),
                "material": item.get('Material', 'N/A'), "size": item.get('Size', ''),
            })
        return results