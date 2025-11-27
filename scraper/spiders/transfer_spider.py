import scrapy
import json
from scraper.items import TransferItem


def sanitize_club_image_url(url):
    """Sanitize club image URL by removing size parameters"""
    if url:
        return url.replace("homepageWappen70x70", "head")
    return url


class TransferSpider(scrapy.Spider):
    name = 'transfer_spider'
    allowed_domains = ['transfermarkt.co.uk']

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Initialize spider with settings"""
        spider = super(TransferSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.player_file = crawler.settings.get('PLAYER_OUTPUT_FILE', 'output/players.json')
        spider.db = crawler.settings.get('DUCKDB_DATABASE')
        spider.logger.info(f'Using player file: {spider.player_file}')
        spider.logger.info(f'Using database: {spider.db}')
        return spider
    
    def start_requests(self):
        """Read player IDs from the player spider output and generate API requests"""
        try:
            if self.db:
                import duckdb
                conn = duckdb.connect(self.db)
                players = conn.execute("SELECT player_id, player_name FROM players").fetchall()
                conn.close()
            else:
                with open(self.player_file, 'r', encoding='utf-8') as f:
                    players = json.load(f)
                
            self.logger.info(f'Loaded {len(players)} players from {self.player_file}')
            
            for player in players:
                if isinstance(player, tuple):
                    player_id = player[0]
                    player_name = player[1] if len(player) > 1 else 'Unknown'
                else:
                    player_id = player.get('player_id')
                    player_name = player.get('player_name', 'Unknown')
                
                if player_id:
                    api_url = f'https://www.transfermarkt.co.uk/ceapi/transferHistory/list/{player_id}'
                    
                    yield scrapy.Request(
                        url=api_url,
                        callback=self.parse_transfer_history,
                        meta={
                            'player_id': player_id,
                            'player_name': player_name
                        },
                        errback=self.handle_error
                    )
        
        except FileNotFoundError:
            self.logger.error(f'Player file not found: {self.player_file}')
            self.logger.error('Please run player_spider first to generate the player list')
        except json.JSONDecodeError as e:
            self.logger.error(f'Error parsing player file: {e}')
    
    async def start(self):
        """Generate initial requests (new async method for Scrapy 2.13+)"""
        async for x in super().start():
            yield x
    
    def parse_transfer_history(self, response):
        """Parse the transfer history API response"""
        player_id = response.meta['player_id']
        player_name = response.meta['player_name']

        player_name = player_name.replace('-', ' ').title()
        
        try:
            data = json.loads(response.text)
            transfer_data_list = []
            
            for transfer in data.get('transfers', []):
                transfer_data = {}
                transfer_data['season'] = transfer.get('season', 'Unknown')
                transfer_data['fee'] = transfer.get('fee', 'Unknown')
                transfer_data['from_club'] = transfer['from'].get('clubName', 'Unknown')
                transfer_data['to_club'] = transfer['to'].get('clubName', 'Unknown')
                transfer_data['date'] = transfer.get('date', 'Unknown')
                transfer_data['from_club_image_url'] = sanitize_club_image_url(transfer['from'].get('clubEmblemMobile', ''))
                transfer_data['to_club_image_url'] = sanitize_club_image_url(transfer['to'].get('clubEmblemMobile', ''))

                transfer_data_list.append(transfer_data)

            yield TransferItem(
                player_id=player_id,
                player_name=player_name,
                transfers=transfer_data_list
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f'Error parsing transfer data for player {player_id}: {e}')
    
    def handle_error(self, failure):
        """Handle request errors"""
        request = failure.request
        player_id = request.meta.get('player_id', 'Unknown')
        self.logger.error(f'Request failed for player {player_id}: {failure.value}')