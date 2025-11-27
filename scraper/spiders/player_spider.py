import scrapy
import re
from scraper.items import PlayerItem

def sanitize_string(input_string):
    """Sanitize strings by replacing hyphens with spaces and title-casing"""
    if input_string:
        return input_string.replace('-', ' ').title()
    return input_string
    

class PlayerSpider(scrapy.Spider):
    name = 'player_spider'
    allowed_domains = ['transfermarkt.co.uk']
    
    # Top 8 leagues - top divisions each
    # Format: (league_name, division_name, league_url)
    start_urls_data = [
        # England
        ('England', 'Premier League', 'https://www.transfermarkt.co.uk/premier-league/startseite/wettbewerb/GB1'),
        
        # Spain
        ('Spain', 'La Liga', 'https://www.transfermarkt.co.uk/laliga/startseite/wettbewerb/ES1'),
        
        # Germany
        ('Germany', 'Bundesliga', 'https://www.transfermarkt.co.uk/bundesliga/startseite/wettbewerb/L1'),
        
        # Italy
        ('Italy', 'Serie A', 'https://www.transfermarkt.co.uk/serie-a/startseite/wettbewerb/IT1'),
        
        # France
        ('France', 'Ligue 1', 'https://www.transfermarkt.co.uk/ligue-1/startseite/wettbewerb/FR1'),
        
        # Portugal
        ('Portugal', 'Primeira Liga', 'https://www.transfermarkt.co.uk/primeira-liga/startseite/wettbewerb/PO1'),

        # Netherlands
        ('Netherlands', 'Eredivisie', 'https://www.transfermarkt.co.uk/eredivisie/startseite/wettbewerb/NL1'),

        # Saudi League
        ('Saudi Arabia', 'Saudi Pro League', 'https://www.transfermarkt.co.uk/saudi-professional-league/startseite/wettbewerb/SA1'),

        # MLS
        ('USA', 'MLS', 'https://www.transfermarkt.co.uk/major-league-soccer/startseite/wettbewerb/MLS1'), 
    ]
    
    def start_requests(self):
        """Generate initial requests for each league (deprecated, kept for backward compatibility)"""
        for league, division, url in self.start_urls_data:
            yield scrapy.Request(
                url=url,
                callback=self.parse_league,
                meta={'league': league, 'division': division}
            )
    
    async def start(self):
        """Generate initial requests for each league (new async method for Scrapy 2.13+)"""
        async for x in super().start():
            yield x
    
    def parse_league(self, response):
        """Parse league page to extract club links"""
        league = response.meta['league']
        division = response.meta['division']
        
        club_links = response.css('table.items a[href*="/startseite/verein/"]::attr(href)').getall()
        club_links = list(set(club_links))
        
        self.logger.info(f'Found {len(club_links)} clubs in {league} - {division}')
        
        for club_link in club_links:
            club_url = response.urljoin(club_link)
            club_name = club_link.split('/')[1] if '/' in club_link else 'Unknown'
            
            yield scrapy.Request(
                url=club_url,
                callback=self.parse_club,
                meta={
                    'league': league,
                    'division': division,
                    'club': club_name
                }
            )

    def parse_club(self, response):
        """Parse club page to extract player links and IDs"""
        league = response.meta['league']
        division = response.meta['division']
        club = response.meta['club']
        
        player_links = response.css('table.items a[href*="/profil/spieler/"]::attr(href)').getall()
        player_urls = response.css('table.items img[data-src*="portrait/medium"]::attr(data-src)').getall()
        market_values = response.css('table.items a[href*="/marktwertverlauf/spieler/"]::text').getall()

        player_lists = list(zip(player_links, player_urls, market_values))
        player_lists = list(set(player_lists))
        
        self.logger.info(f'Found {len(player_lists)} players in {club}')
        
        for player_list in player_lists:
            match = re.search(r'/spieler/(\d+)', player_list[0])
            
            if match:
                player_id = match.group(1)
                player_url = response.urljoin(player_list[0])
                player_img_url = player_list[1] if '/' in player_list[1] else ''
                market_value = player_list[2].strip() if len(player_list) > 2 else ''

                player_img_url = re.sub(r'portrait/medium', 'portrait/header', player_img_url)
                player_name = player_list[0].split('/')[1] if '/' in player_list[0] else 'Unknown'
                
                yield PlayerItem(
                    player_id=player_id,
                    player_name=sanitize_string(player_name),
                    player_url=player_url,
                    player_img_url=player_img_url,
                    market_value=market_value,
                    league=league,
                    division=division,
                    club=sanitize_string(club)
                )