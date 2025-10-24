import scrapy
import re
from transfermarkt_scraper.items import PlayerItem

def sanitize_string(input_string):
    """Sanitize strings by replacing hyphens with spaces and title-casing"""
    if input_string:
        return input_string.replace('-', ' ').title()
    return input_string
    

class PlayerSpider(scrapy.Spider):
    name = 'player_spider'
    allowed_domains = ['transfermarkt.co.uk']
    
    # Top 6 European leagues - top divisions each
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

        # Extract player image urls
        player_urls = response.css('table.items img[data-src*="portrait/medium"]::attr(data-src)').getall()

        # Combine player links and image urls as list of tuples
        player_lists = list(zip(player_links, player_urls))
        
        # Get unique player lists
        player_lists = list(set(player_lists))
        
        self.logger.info(f'Found {len(player_lists)} players in {club}')
        
        for player_list in player_lists:
            # Extract player ID from URL using regex
            match = re.search(r'/spieler/(\d+)', player_list[0])
            
            if match:
                player_id = match.group(1)
                player_url = response.urljoin(player_list[0])
                player_img_url = player_list[1] if '/' in player_list[1] else ''

                # replace size in image url from medium to header
                player_img_url = re.sub(r'portrait/medium', 'portrait/header', player_img_url)
                
                # Extract player name from URL (between first two slashes)
                player_name = player_list[0].split('/')[1] if '/' in player_list[0] else 'Unknown'
                
                yield PlayerItem(
                    player_id=player_id,
                    player_name=sanitize_string(player_name),
                    player_url=player_url,
                    player_img_url=player_img_url,
                    league=league,
                    division=division,
                    club=sanitize_string(club)
                )