"""
Process scraped product data to generate a text file for ChatGPT.
Filters out non-edible categories and formats the output.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from io import StringIO
import pandas as pd

# Categories to exclude (non-edible)
NON_EDIBLE_CATEGORIES = [
    "Bebe",
    "Cuidado Del Hogar / Hogar Y Librería",
    "Cuidado Del Hogar / Limpieza, Ropa Y Hogar",
    "Cuidado Personal",
    "Mascotas",
    "Medicinales"
]

def get_latest_json_file(data_dir: Path) -> Path:
    """Find the latest products JSON file in the data directory."""
    json_files = list(data_dir.glob("products_*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")
    
    return max(json_files, key=lambda p: p.stat().st_mtime)

def load_data(file_path: Path) -> pd.DataFrame:
    """Load JSON data and convert to DataFrame with Spanish column names."""
    print(f"Loading data from: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = data.get("products", [])
    print(f"Total products loaded: {len(products)}")
    
    df = pd.DataFrame(products)
    
    # Remove raw_data if exists
    if "raw_data" in df.columns:
        df = df.drop(columns=["raw_data"])
        
    # Rename columns to Spanish
    column_mapping = {
        "barcode": "codigo_barras",
        "category": "categoria",
        "description": "descripcion",
        "image_url": "url_imagen",
        "name": "nombre",
        "offer_description": "descripcion_oferta",
        "offer_price": "precio_oferta",
        "price": "precio",
        "stock": "inventario",
        "subcategory": "subcategoria"
    }
    
    df_spanish = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    return df_spanish

def filter_edible_products(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out non-edible products based on category."""
    if 'categoria' not in df.columns:
        print("Warning: 'categoria' column not found, skipping filter.")
        return df
        
    df_edible = df[~df['categoria'].isin(NON_EDIBLE_CATEGORIES)].copy()
    print(f"Filtered {len(df) - len(df_edible)} non-edible products.")
    print(f"Remaining edible products: {len(df_edible)}")
    
    return df_edible

def generate_text_file(df: pd.DataFrame, output_path: Path):
    """Generate a formatted text file with product list and prices."""
    output_buffer = StringIO()

    def print_and_save(text):
        print(text)
        output_buffer.write(text + "\n")

    print_and_save("=" * 60)
    print_and_save("PRODUCTOS COMESTIBLES CON PRECIOS")
    print_and_save("=" * 60)
    
    if 'categoria' in df.columns and 'subcategoria' in df.columns:
        # Sort by category, subcategory and name
        df_sorted = df.sort_values(['categoria', 'subcategoria', 'nombre'])
        
        # Get unique categories
        categorias = sorted(df_sorted['categoria'].unique())
        
        for categoria in categorias:
            df_categoria = df_sorted[df_sorted['categoria'] == categoria]
            subcategorias = sorted(df_categoria['subcategoria'].unique())
            
            print_and_save(f"\nCATEGORIA: {categoria}")
            print_and_save("=" * 60)
            
            for subcategoria in subcategorias:
                df_subcat = df_categoria[df_categoria['subcategoria'] == subcategoria]
                
                print_and_save(f"\n  SUBCATEGORIA: {subcategoria} ({len(df_subcat)} productos)")
                print_and_save("  " + "-" * 58)
                
                # Print each product
                for _, row in df_subcat.iterrows():
                    nombre = row.get('nombre', 'N/A')
                    precio = row.get('precio', 'N/A')
                    
                    # Format price
                    if pd.notna(precio):
                        try:
                            precio_num = float(precio)
                            precio_str = f"Q{precio_num:.2f}"
                        except (ValueError, TypeError):
                            precio_str = f"Q{precio}"
                    else:
                        precio_str = "Q0.00"
                    
                    print_and_save(f"    {nombre} - {precio_str}")
        
        print_and_save("\n" + "=" * 60)
        print_and_save(f"Total productos comestibles mostrados: {len(df_sorted)}")
        
        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_buffer.getvalue())
            
        print(f"\nFile saved to: {output_path.absolute()}")
    else:
        print("Error: Required columns 'categoria' or 'subcategoria' not found.")

def main():
    parser = argparse.ArgumentParser(description="Process scraped product data.")
    parser.add_argument("--input", help="Path to input JSON file (optional, defaults to latest)")
    parser.add_argument("--output-dir", default="data", help="Directory for output files")
    args = parser.parse_args()
    
    try:
        # Determine input file
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file {input_path} not found.")
                sys.exit(1)
        else:
            data_dir = Path("data")
            if not data_dir.exists():
                print(f"Error: Data directory {data_dir} not found.")
                sys.exit(1)
            input_path = get_latest_json_file(data_dir)
            
        # Determine output path
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        output_filename = input_path.stem.replace(".json", "") + "_productos_comestibles.txt"
        output_path = output_dir / output_filename
        
        # Process data
        df = load_data(input_path)
        df_edible = filter_edible_products(df)
        generate_text_file(df_edible, output_path)
        
    except Exception as e:
        print(f"Error processing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

