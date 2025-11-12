import duckdb
import json
from itemadapter import ItemAdapter
from transfermarkt_scraper.items import PlayerItem, TransferItem

class DuckDBPipeline:
    """Pipeline to store items in DuckDB database"""
    
    def __init__(self, db_path='transfermarkt.db'):
        self.db_path = db_path
        self.conn = None
    
    @classmethod
    def from_crawler(cls, crawler):
        """Get database path from settings"""
        return cls(
            db_path=crawler.settings.get('DUCKDB_DATABASE', 'transfermarkt.db')
        )
    
    def open_spider(self, spider):
        """Create database connection and tables when spider starts"""
        self.conn = duckdb.connect(self.db_path)
        self._create_tables()
        spider.logger.info(f'Connected to DuckDB database: {self.db_path}')
    
    def close_spider(self, spider):
        """Close database connection when spider closes"""
        if self.conn:
            self.conn.close()
            spider.logger.info('Closed DuckDB database connection')
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        
        # Players table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id VARCHAR PRIMARY KEY,
                player_name VARCHAR,
                player_url VARCHAR,
                player_img_url VARCHAR,
                market_value VARCHAR,
                league VARCHAR,
                division VARCHAR,
                club VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transfers table (stores the full JSON)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                player_id VARCHAR PRIMARY KEY,
                player_name VARCHAR,
                transfers_json JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """)
        
        # Optional: Normalized transfers table for easier querying
        # firt create a sequence for auto-incrementing IDs
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS transfer_details_seq START 1
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS transfer_details (
                id INTEGER PRIMARY KEY,
                player_id VARCHAR,
                season VARCHAR,
                fee VARCHAR,
                from_club VARCHAR,
                to_club VARCHAR,
                transfer_date VARCHAR,
                from_club_image_url VARCHAR,
                to_club_image_url VARCHAR,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """)
    
    def process_item(self, item, spider):
        """Process and store each item"""
        adapter = ItemAdapter(item)
        
        if isinstance(item, PlayerItem):
            self._store_player(adapter)
        elif isinstance(item, TransferItem):
            self._store_transfer(adapter)
        
        return item
    
    def _store_player(self, adapter):
        """Store player data"""
        self.conn.execute("""
            INSERT OR REPLACE INTO players 
            (player_id, player_name, player_url, player_img_url, market_value, league, division, club)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            adapter.get('player_id'),
            adapter.get('player_name'),
            adapter.get('player_url'),
            adapter.get('player_img_url'),
            adapter.get('market_value'),
            adapter.get('league'),
            adapter.get('division'),
            adapter.get('club')
        ])
    
    def _store_transfer(self, adapter):
        """Store transfer data (with JSON)"""
        player_id = adapter.get('player_id')
        player_name = adapter.get('player_name')
        transfers_data = adapter.get('transfers')
        
        # Store full JSON
        self.conn.execute("""
            INSERT OR REPLACE INTO transfers 
            (player_id, player_name, transfers_json)
            VALUES (?, ?, ?)
        """, [
            player_id,
            player_name,
            json.dumps(transfers_data, ensure_ascii=False)
        ])
        
        # Optional: Also store normalized transfer details for easier querying
        # if isinstance(transfers_data, dict) and 'transfers' in transfers_data:
        #     self._store_transfer_details(player_id, transfers_data['transfers'])
        if isinstance(transfers_data, list):
            self._store_transfer_details(player_id, transfers_data)
    
    def _store_transfer_details(self, player_id, transfers_list):
        """Store individual transfer records in normalized table"""
        # Delete existing transfers for this player
        self.conn.execute("""
            DELETE FROM transfer_details WHERE player_id = ?
        """, [player_id])
        
        # Insert new transfers
        for transfer in transfers_list:
            self.conn.execute("""
                INSERT INTO transfer_details 
                (id, player_id, season, fee, from_club, to_club, transfer_date, from_club_image_url, to_club_image_url)
                VALUES (nextval('transfer_details_seq'), ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                player_id,
                transfer.get('season'),
                transfer.get('fee'),
                transfer.get('from_club'),
                transfer.get('to_club'),
                transfer.get('date'),
                transfer.get('from_club_image_url'),
                transfer.get('to_club_image_url')
            ])
