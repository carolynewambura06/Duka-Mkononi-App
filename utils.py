import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constants
SUPPORTED_LANGUAGES = ["Swahili", "English"]
DEFAULT_LANGUAGE = "Swahili"
SALES_FILE = "sales.csv"  # Define the path to your sales data file

def get_col_names():
    """Returns language-specific column names with robust error handling and validation"""
    try:
        # Get current language with safe default
        current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
        
        # Validate language selection
        if current_lang not in SUPPORTED_LANGUAGES:
            st.warning(f"Unsupported language '{current_lang}'. Defaulting to {DEFAULT_LANGUAGE}.")
            current_lang = DEFAULT_LANGUAGE
        
        # Comprehensive column mappings with Swahili corrections
        COLUMN_MAPPINGS = {
            "Swahili": {
                "product": "Bidhaa",
                "cost_price": "Bei_ya_ununuzi",
                "stock": "Hifadhi",
                "date": "Tarehe",
                "qty": "Idadi",
                "unit_price": "Bei_ya_rejareja",
                "total_price": "Jumla_bei",
                "profit": "Faida",
                "sale_price": "Bei_ya_mauzo"
            },
            "English": {
                "product": "product",
                "cost_price": "cost_price",
                "stock": "stock",
                "date": "date",
                "qty": "quantity",
                "unit_price": "unit_price",
                "total_price": "total_price",
                "profit": "profit",
                "sale_price": "sale_price"
            }
        }
        
        return COLUMN_MAPPINGS[current_lang]
        
    except Exception as e:
        st.error(f"Critical error in column mapping: {str(e)}")
        # Return minimal safe columns in English
        return {
            "product": "product",
            "cost_price": "cost_price",
            "stock": "stock",
            "date": "date"
        }

def migrate_data_columns(df, target_language):
    """Safely migrates dataframe columns between languages with data validation"""
    try:
        # Validate input dataframe
        if not isinstance(df, pd.DataFrame):
            st.error("Invalid input: Expected pandas DataFrame")
            return pd.DataFrame()
            
        if df.empty:
            return df
            
        # Standardize column names first
        df.columns = df.columns.str.strip().str.replace(" ", "_")
        
        # Correct common Swahili typos
        typo_corrections = {
            "Bet_": "Bei_",
            "Hitadhi": "Hifadhi",
            "Faida": "Faida",
            "Falda": "Faida",
            "Bidha": "Bidhaa"
        }
        
        for typo, correct in typo_corrections.items():
            df.columns = df.columns.str.replace(typo, correct)
        
        # Get column mappings
        col_names = get_col_names()
        
        # Determine source language
        source_language = "English" if target_language == "Swahili" else "Swahili"
        
        # Create mapping dictionary
        column_mapping = {}
        for eng_col, swa_col in col_names.items():
            source_col = swa_col if source_language == "Swahili" else eng_col
            target_col = swa_col if target_language == "Swahili" else eng_col
            column_mapping[source_col] = target_col
        
        # Apply mapping and fill NA values
        migrated_df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ["product", "cost_price", "stock", "date"]
        for col in required_cols:
            target_col = col_names.get(col, col)
            if target_col not in migrated_df.columns:
                migrated_df[target_col] = 0 if col != "date" else datetime.now()
        
        return migrated_df.fillna(0)  # Fill empty cells with appropriate defaults
        
    except Exception as e:
        st.error(f"Data migration failed: {str(e)}")
        return df  # Return original dataframe as fallback

def validate_dataframe(df, required_cols=None):
    """Comprehensive dataframe validation with column checking and type verification"""
    try:
        if not isinstance(df, pd.DataFrame):
            st.error("Invalid data: Not a pandas DataFrame")
            return False
            
        if df.empty:
            st.warning("Empty dataframe detected")
            return True  # Empty but valid structure
            
        if required_cols:
            # Get current language column names
            col_names = get_col_names()
            required_cols = [col_names.get(col, col) for col in required_cols]
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                return False
                
            # Check for completely null columns
            null_cols = df.columns[df.isnull().all()].tolist()
            if null_cols:
                st.warning(f"Columns with all null values: {', '.join(null_cols)}")
                
        return True
        
    except Exception as e:
        st.error(f"Validation error: {str(e)}")
        return False

def load_sales():
    """Robust sales data loader with automatic repair and validation"""
    try:
        # Initialize empty dataframe if file doesn't exist
        if not os.path.exists(SALES_FILE):
            cols = get_col_names()
            return pd.DataFrame(columns=[cols.get(col, col) for col in [
                "product", "cost_price", "stock", "date", 
                "qty", "unit_price", "total_price", "profit"
            ]])
            
        # Load with error handling for malformed files
        df = pd.read_csv(SALES_FILE, encoding='utf-8', on_bad_lines='warn')
        
        # Convert date column with validation
        date_col = get_col_names().get("date", "date")
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df[date_col] = df[date_col].fillna(pd.Timestamp.now())
        
        # Ensure required columns exist
        required_cols = ["product", "cost_price", "stock", "date"]
        col_names = get_col_names()
        
        for col in required_cols:
            target_col = col_names.get(col, col)
            if target_col not in df.columns:
                df[target_col] = 0 if col != "date" else pd.Timestamp.now()
        
        # Migrate to current language
        current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
        df = migrate_data_columns(df, current_lang)
        
        # Final validation
        if not validate_dataframe(df, required_cols):
            st.error("Sales data failed validation. Some columns may be missing.")
            
        return df
        
    except Exception as e:
        st.error(f"Failed to load sales data: {str(e)}")
        # Return empty dataframe with correct columns
        cols = get_col_names()
        return pd.DataFrame(columns=[cols.get(col, col) for col in [
            "product", "cost_price", "stock", "date", 
            "qty", "unit_price", "total_price", "profit"
        ]])