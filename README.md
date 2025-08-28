# AI Fashion Recommendation Engine 🛍️

This project is a sophisticated AI-powered fashion recommendation engine built with Streamlit. It provides a highly personalized and interactive e-commerce experience, leveraging modern AI techniques like Retrieval-Augmented Generation (RAG) for product suggestions, generative AI for style advice, and a virtual try-on feature.

---

## ✨ Key Features

* **Personalized Product Recommendations**: Utilizes a RAG system with OpenAI and FAISS to deliver relevant product suggestions based on customer data and natural language queries.
* **AI-Powered Style Guidance**:
    * Calculates the user's body shape (for both men and women) based on their measurements.
    * Generates personalized fashion advice and style tips tailored to the user's unique body shape.
* **Virtual Try-On**: Integrates with the Replicate API, allowing users to upload a photo of themselves and see how a selected clothing item would look on them.
* **Comprehensive E-commerce Platform**: Includes essential features like:
    * A simple and effective user login system.
    * Detailed product view pages.
    * Sections for "Trending" and "Top Discounted" items.
    * Fully functional Shopping Cart and Wishlist.
* **Modular and Scalable Codebase**: The application is broken down into logical modules for UI, data handling, and AI systems, making it easy to maintain and extend.

---

## ⚙️ How It Works

The application's intelligence is driven by a combination of systems:

1.  **RAG System (`rag_system.py`)**:
    * Product data from `Product Data.csv` is converted into vector embeddings using OpenAI's `text-embedding-3-large` model.
    * These embeddings are stored in a FAISS index for ultra-fast similarity searches.
    * When a user searches or the system needs a recommendation, a query is embedded and compared against the FAISS index to retrieve the most relevant products.

2.  **Style Recommendation Engine (`utils.py`, `pages.py`)**:
    * The system takes user-provided body measurements (e.g., shoulder, bust, waist, hips).
    * It applies logic to determine the user's body shape (e.g., "Rectangle", "Triangle" for men; "Hourglass", "Apple" for women).
    * Using this classification, it pulls tailored advice from `men_style_tips.csv` and `women_style_tips.csv` to guide the user on what to wear and what to avoid.

3.  **Virtual Try-On (`virtual_tryon.py`)**:
    * This module connects to the Replicate API to run an advanced image generation model.
    * It takes a user's uploaded image and an image of a garment, then composites them to create a realistic virtual try-on result.

---

## 📂 Project Structure

The project is organized into several key Python files:

* `app.py`: The main entry point for the Streamlit application. It handles user authentication, session state, and page routing.
* `pages.py`: Contains the functions that render the main pages of the app (Product Recommendations, Style Recommendations, Cart, Wishlist).
* `rag_system.py`: Defines the `FashionRAG` and `CustomerRAG` classes that manage the core recommendation logic.
* `ui_components.py`: A collection of reusable functions for creating UI elements like product grids and detail pages.
* `utils.py`: Helper functions for data loading, session state management, body shape calculation, and more.
* `virtual_tryon.py`: Manages all logic related to the virtual try-on feature, including API calls to Replicate.

---

## 📊 Datasets

The application relies on the following CSV files:

* `Product Data.csv`: Contains all product details, including name, brand, price, description, and image URLs.
* `Cust Data.csv`: Stores customer demographic information, abandoned carts, and wishlist items.
* `Session Data.csv`: Logs user search queries and product interaction data.
* `Transaction Data.csv`: Contains historical purchase data for each customer.
* `men_style_tips.csv`: Provides fashion advice tailored to different male body shapes.
* `women_style_tips.csv`: Provides fashion advice tailored to different female body shapes.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* An account and API keys for:
    * [OpenAI](https://openai.com/)
    * [Replicate](https://replicate.com/)
    * [Cloudinary](https://cloudinary.com/) (for image hosting)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file should be created with libraries such as `streamlit`, `pandas`, `openai`, `faiss-cpu`, `replicate`, `cloudinary`, etc.)*

3.  **Set up your API keys:**
    Create a file at `.streamlit/secrets.toml` and add your API keys in the following format:

    ```toml
    # .streamlit/secrets.toml

    OPENAI_API_KEY = "sk-..."
    REPLICATE_API_TOKEN = "r8_..."

    [cloudinary]
    cloud_name = "your_cloud_name"
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    ```

### Running the Application

1.  Open your terminal in the project's root directory.
2.  Run the following command:
    ```bash
    streamlit run app.py
    ```
3.  The application should now be open and running in your web browser!
