"""File-based storage for scraped data."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import settings
from utils.logger import logger


class FileStorage:
    """Handles saving scraped data to files (CSV, JSON, Parquet)."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize file storage.

        Args:
            output_dir: Output directory for saved files
        """
        self.output_dir = Path(output_dir or settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage initialized: {self.output_dir.absolute()}")

    def save_json(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Save data to JSON file.

        Args:
            data: List of product dictionaries
            filename: Optional filename (default: products_YYYYMMDD_HHMMSS.json)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.json"

        filepath = self.output_dir / filename

        # Add metadata
        output_data = {
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "total_products": len(data),
                "source": "misuperfresh.com.gt",
            },
            "products": data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(data)} products to JSON: {filepath.absolute()}")
        return filepath

    def save_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Save data to CSV file.

        Args:
            data: List of product dictionaries
            filename: Optional filename (default: products_YYYYMMDD_HHMMSS.csv)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.csv"

        filepath = self.output_dir / filename

        if not data:
            logger.warning("No data to save to CSV")
            return filepath

        # Get all unique keys from all products
        fieldnames = set()
        for product in data:
            fieldnames.update(product.keys())
        fieldnames = sorted(list(fieldnames))

        # Remove internal fields
        fieldnames = [f for f in fieldnames if f not in ["raw_data"]]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for product in data:
                # Flatten nested data if needed
                row = {}
                for key, value in product.items():
                    if key == "raw_data":
                        continue
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)

        logger.info(f"Saved {len(data)} products to CSV: {filepath.absolute()}")
        return filepath

    def save_parquet(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Optional[Path]:
        """
        Save data to Parquet file.

        Args:
            data: List of product dictionaries
            filename: Optional filename (default: products_YYYYMMDD_HHMMSS.parquet)

        Returns:
            Path to saved file or None if pandas not available
        """
        try:
            import pandas as pd
        except ImportError:
            logger.warning("pandas not available, skipping Parquet export")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.parquet"

        filepath = self.output_dir / filename

        # Convert to DataFrame
        df = pd.DataFrame(data)
        # Remove raw_data column if it exists (not serializable)
        if "raw_data" in df.columns:
            df = df.drop(columns=["raw_data"])

        df.to_parquet(filepath, index=False)

        logger.info(f"Saved {len(data)} products to Parquet: {filepath.absolute()}")
        return filepath

    def save(self, data: List[Dict[str, Any]], format: Optional[str] = None) -> Dict[str, Path]:
        """
        Save data in the specified format(s).

        Args:
            data: List of product dictionaries
            format: Format to save (csv, json, parquet, or None for all)

        Returns:
            Dictionary mapping format to file path
        """
        saved_files = {}
        format = format or settings.storage_format

        if format == "json" or format == "all":
            saved_files["json"] = self.save_json(data)

        if format == "csv" or format == "all":
            saved_files["csv"] = self.save_csv(data)

        if format == "parquet" or format == "all":
            parquet_path = self.save_parquet(data)
            if parquet_path:
                saved_files["parquet"] = parquet_path

        return saved_files

