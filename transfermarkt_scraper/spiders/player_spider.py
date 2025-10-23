import scrapy
import re
from transfermarkt_scraper.items import PlayerItem


class PlayerSpider(scrapy.Spider):
    name = 'player_spider'
    allowed_domains = ['transfermarkt.co.uk']
    
    # Top 6 European leagues - top 3 divisions each
    # Format: (league_name, division_name, league_url)
    start_urls_data = [
        # England
        ('England', 'Premier League', 'https://www.transfermarkt.co.uk/premier-league/startseite/wettbewerb/GB1'),
        # ('England', 'Championship', 'https://www.transfermarkt.co.uk/championship/startseite/wettbewerb/GB2'),
        # ('England', 'League One', 'https://www.transfermarkt.co.uk/league-one/startseite/wettbewerb/GB3'),
        
        # # Spain
        # ('Spain', 'La Liga', 'https://www.transfermarkt.co.uk/laliga/startseite/wettbewerb/ES1'),
        # ('Spain', 'Segunda Division', 'https://www.transfermarkt.co.uk/segunda-division/startseite/wettbewerb/ES2'),
        # ('Spain', 'Primera RFEF', 'https://www.transfermarkt.co.uk/primera-federacion/startseite/wettbewerb/ES3A'),
        
        # # Germany
        # ('Germany', 'Bundesliga', 'https://www.transfermarkt.co.uk/bundesliga/startseite/wettbewerb/L1'),
        # ('Germany', '2. Bundesliga', 'https://www.transfermarkt.co.uk/2-bundesliga/startseite/wettbewerb/L2'),
        # ('Germany', '3. Liga', 'https://www.transfermarkt.co.uk/3-liga/startseite/wettbewerb/L3'),
        
        # # Italy
        # ('Italy', 'Serie A', 'https://www.transfermarkt.co.uk/serie-a/startseite/wettbewerb/IT1'),
        # ('Italy', 'Serie B', 'https://www.transfermarkt.co.uk/serie-b/startseite/wettbewerb/IT2'),
        # ('Italy', 'Serie C', 'https://www.transfermarkt.co.uk/serie-c/startseite/wettbewerb/IT3A'),
        
        # # France
        # ('France', 'Ligue 1', 'https://www.transfermarkt.co.uk/ligue-1/startseite/wettbewerb/FR1'),
        # ('France', 'Ligue 2', 'https://www.transfermarkt.co.uk/ligue-2/startseite/wettbewerb/FR2'),
        # ('France', 'National', 'https://www.transfermarkt.co.uk/national/startseite/wettbewerb/FR3A'),
        
        # # Portugal
        # ('Portugal', 'Primeira Liga', 'https://www.transfermarkt.co.uk/primeira-liga/startseite/wettbewerb/PO1'),
        # ('Portugal', 'Segunda Liga', 'https://www.transfermarkt.co.uk/liga-portugal-2/startseite/wettbewerb/PO2'),
        # ('Portugal', 'Liga 3', 'https://www.transfermarkt.co.uk/liga-3/startseite/wettbewerb/PO3'),
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
        # Use the parent class implementation which will call start_requests()
        # This provides backward compatibility
        async for x in super().start():
            yield x
    
    def parse_league(self, response):
        """Parse league page to extract club links"""
        league = response.meta['league']
        division = response.meta['division']
        
        # Extract all club links from the league page
        # Clubs are typically in tables with links to /club-name/startseite/verein/CLUB_ID
        club_links = response.css('table.items a[href*="/startseite/verein/"]::attr(href)').getall()
        
        # Get unique club links
        club_links = list(set(club_links))
        
        self.logger.info(f'Found {len(club_links)} clubs in {league} - {division}')
        
        for club_link in club_links:
            club_url = response.urljoin(club_link)
            
            # Extract club name from URL
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
        
        # Extract player links - pattern: /player-name/profil/spieler/PLAYER_ID
        player_links = response.css('table.items a[href*="/profil/spieler/"]::attr(href)').getall()
        
        # Get unique player links
        player_links = list(set(player_links))
        
        self.logger.info(f'Found {len(player_links)} players in {club}')
        
        for player_link in player_links:
            # Extract player ID from URL using regex
            match = re.search(r'/spieler/(\d+)', player_link)
            
            if match:
                player_id = match.group(1)
                player_url = response.urljoin(player_link)
                
                # Extract player name from URL (between first two slashes)
                player_name = player_link.split('/')[1] if '/' in player_link else 'Unknown'
                
                yield PlayerItem(
                    player_id=player_id,
                    player_name=player_name,
                    player_url=player_url,
                    league=league,
                    division=division,
                    club=club
                )