import json
import os
from itemadapter import ItemAdapter
from transfermarkt_scraper.items import PlayerItem, TransferItem


class JsonWriterPipeline:
    """Pipeline to write items to JSON files"""

    def __init__(self, player_file='players.json', transfer_file='transfers.json'):
        self.player_file = player_file
        self.transfer_file = transfer_file

    @classmethod
    def from_crawler(cls, crawler):
        """Get file paths from settings"""
        return cls(
            player_file=crawler.settings.get('PLAYER_OUTPUT_FILE', 'players.json'),
            transfer_file=crawler.settings.get('TRANSFER_OUTPUT_FILE', 'transfers.json')
        )
    
    def open_spider(self, spider):
        """Create output directory and file handlers when spider opens"""
        os.makedirs('output', exist_ok=True)
        
        if spider.name == 'player_spider':
            self.file = open(self.player_file, 'w', encoding='utf-8')
            self.file.write('[\n')
            self.first_item = True
            
        elif spider.name == 'transfer_spider':
            self.file = open(self.transfer_file, 'w', encoding='utf-8')
            self.file.write('[\n')
            self.first_item = True
    
    def close_spider(self, spider):
        """Close file handlers when spider closes"""
        if hasattr(self, 'file'):
            self.file.write('\n]')
            self.file.close()
    
    def process_item(self, item, spider):
        """Process each item and write to appropriate file"""
        if not hasattr(self, 'file'):
            return item
            
        adapter = ItemAdapter(item)
        
        # Add comma before item if not the first one
        if not self.first_item:
            self.file.write(',\n')
        else:
            self.first_item = False
        
        # Write item as JSON
        line = json.dumps(dict(adapter), ensure_ascii=False, indent=2)
        self.file.write(line)
        
        return item