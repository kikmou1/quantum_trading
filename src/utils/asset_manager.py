"""
Asset Manager - Load and search tradable assets database.
"""

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Manages the tradable assets database.
    """

    def __init__(self, assets_file: str = "data/tradable_assets.txt"):
        """
        Initialize asset manager.

        Args:
            assets_file: Path to tradable assets database file
        """
        self.assets_file = Path(assets_file)
        self.assets_df: Optional[pd.DataFrame] = None
        self.load_assets()

    def load_assets(self):
        """Load assets from file."""
        if not self.assets_file.exists():
            logger.error(f"Assets file not found: {self.assets_file}")
            return

        assets = []

        with open(self.assets_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse line: Symbol|Name|Category|Exchange|Description
                parts = line.split('|')
                if len(parts) == 5:
                    assets.append({
                        'symbol': parts[0].strip(),
                        'name': parts[1].strip(),
                        'category': parts[2].strip(),
                        'exchange': parts[3].strip(),
                        'description': parts[4].strip()
                    })

        self.assets_df = pd.DataFrame(assets)
        logger.info(f"Loaded {len(self.assets_df)} tradable assets")

    def get_all_assets(self) -> pd.DataFrame:
        """Get all assets as DataFrame."""
        return self.assets_df.copy() if self.assets_df is not None else pd.DataFrame()

    def get_categories(self) -> List[str]:
        """Get unique asset categories."""
        if self.assets_df is None:
            return []
        return sorted(self.assets_df['category'].unique().tolist())

    def get_by_category(self, category: str) -> pd.DataFrame:
        """
        Get assets by category.

        Args:
            category: Asset category (Stock, ETF, Commodity, etc.)

        Returns:
            DataFrame of assets in that category
        """
        if self.assets_df is None:
            return pd.DataFrame()

        return self.assets_df[self.assets_df['category'] == category].copy()

    def search_assets(self, query: str, search_in: List[str] = None) -> pd.DataFrame:
        """
        Search assets by query string.

        Args:
            query: Search query
            search_in: Fields to search in (default: symbol, name, description)

        Returns:
            DataFrame of matching assets
        """
        if self.assets_df is None or not query:
            return pd.DataFrame()

        if search_in is None:
            search_in = ['symbol', 'name', 'description']

        query_lower = query.lower()
        mask = pd.Series([False] * len(self.assets_df))

        for field in search_in:
            if field in self.assets_df.columns:
                mask |= self.assets_df[field].str.lower().str.contains(query_lower, na=False)

        return self.assets_df[mask].copy()

    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """
        Get information for a specific asset.

        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'GC=F')

        Returns:
            Dictionary with asset info or None if not found
        """
        if self.assets_df is None:
            return None

        matches = self.assets_df[self.assets_df['symbol'] == symbol]

        if len(matches) == 0:
            return None

        return matches.iloc[0].to_dict()

    def get_symbols_by_category(self, category: str) -> List[str]:
        """
        Get list of symbols for a category.

        Args:
            category: Asset category

        Returns:
            List of symbols
        """
        if self.assets_df is None:
            return []

        return self.assets_df[
            self.assets_df['category'] == category
        ]['symbol'].tolist()

    def get_popular_assets(self, n: int = 20) -> pd.DataFrame:
        """
        Get popular/commonly traded assets.

        Args:
            n: Number of assets to return

        Returns:
            DataFrame of popular assets
        """
        if self.assets_df is None:
            return pd.DataFrame()

        # Define popular symbols (most liquid and commonly traded)
        popular = [
            'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA',
            'META', 'GC=F', 'SI=F', 'CL=F', 'BTC-USD', 'ETH-USD',
            'EURUSD=X', '^GSPC', '^VIX', 'GLD', 'TLT', 'XLE'
        ]

        # Get assets that are in our database and in the popular list
        popular_assets = self.assets_df[
            self.assets_df['symbol'].isin(popular)
        ].copy()

        return popular_assets.head(n)

    def get_asset_summary(self) -> Dict:
        """
        Get summary statistics of the asset database.

        Returns:
            Dictionary with summary stats
        """
        if self.assets_df is None:
            return {}

        category_counts = self.assets_df['category'].value_counts().to_dict()

        return {
            'total_assets': len(self.assets_df),
            'categories': self.get_categories(),
            'category_counts': category_counts,
            'exchanges': sorted(self.assets_df['exchange'].unique().tolist())
        }

    def format_asset_display(self, asset: Dict) -> str:
        """
        Format asset for display.

        Args:
            asset: Asset dictionary

        Returns:
            Formatted string
        """
        return f"{asset['symbol']} - {asset['name']} ({asset['category']})"


if __name__ == "__main__":
    # Test asset manager
    logging.basicConfig(level=logging.INFO)

    manager = AssetManager()

    # Test: Get summary
    summary = manager.get_asset_summary()
    print("\nASSET DATABASE SUMMARY")
    print("="*70)
    print(f"Total Assets: {summary['total_assets']}")
    print(f"\nCategories: {', '.join(summary['categories'])}")
    print(f"\nAssets by Category:")
    for cat, count in summary['category_counts'].items():
        print(f"  {cat}: {count}")

    # Test: Search for gold
    print("\n\nSEARCH: 'gold'")
    print("="*70)
    gold_assets = manager.search_assets('gold')
    print(gold_assets[['symbol', 'name', 'category']].to_string(index=False))

    # Test: Get commodities
    print("\n\nCATEGORY: Commodity")
    print("="*70)
    commodities = manager.get_by_category('Commodity')
    print(f"Found {len(commodities)} commodities")
    print(commodities[['symbol', 'name', 'description']].head(10).to_string(index=False))

    # Test: Get asset info
    print("\n\nASSET INFO: GC=F (Gold Futures)")
    print("="*70)
    gold_info = manager.get_asset_info('GC=F')
    if gold_info:
        for key, value in gold_info.items():
            print(f"  {key}: {value}")

    # Test: Popular assets
    print("\n\nPOPULAR ASSETS")
    print("="*70)
    popular = manager.get_popular_assets(10)
    print(popular[['symbol', 'name', 'category']].to_string(index=False))
