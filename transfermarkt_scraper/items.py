import scrapy


class PlayerItem(scrapy.Item):
    """Item for storing player basic information"""
    player_id = scrapy.Field()
    player_name = scrapy.Field()
    player_url = scrapy.Field()
    league = scrapy.Field()
    division = scrapy.Field()
    club = scrapy.Field()


class TransferItem(scrapy.Item):
    """Item for storing player transfer history"""
    player_id = scrapy.Field()
    player_name = scrapy.Field()
    transfers = scrapy.Field()  # List of transfer records

# class TransferDetail(scrapy.Item):
#     """Item for storing player transfer history"""
#     player_id = scrapy.Field()
#     player_name = scrapy.Field()
#     transfers = scrapy.Field()  # List of transfer records