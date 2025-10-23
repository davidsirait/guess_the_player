import json
import os
from itemadapter import ItemAdapter
from transfermarkt_scraper.items import PlayerItem, TransferItem


class JsonWriterPipeline:
    """Pipeline to write items to JSON files"""
    
    def open_spider(self, spider):
        """Create output directory and file handlers when spider opens"""
        os.makedirs('output', exist_ok=True)
        
        if spider.name == 'player_spider':
            self.file = open('output/players.json', 'w', encoding='utf-8')
            self.file.write('[\n')
            self.first_item = True
            
        elif spider.name == 'transfer_spider':
            self.file = open('output/transfers.json', 'w', encoding='utf-8')
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