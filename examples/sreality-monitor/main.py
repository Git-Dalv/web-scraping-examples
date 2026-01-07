from src.database.db import Database, FilterPageLoader, show_stats
from src.scraper.scraper import get_filters, get_all_data
from src.plugins.web.export_map import export_estates
from src.analysis.analytics import export_analytics, print_summary, generate_all_charts


def main():
    print("Sreality Monitor")
    print("=" * 50)
    
    with Database() as db:
        # Init schema
        db.init_schema()
        
        # Load reference data
        filter_data = get_filters()
        loader = FilterPageLoader(db, filter_data)
        loader.load_all()
        
        # Scrape estates
        print("\nStarting scraper...")
        get_all_data(db, step=1000, delay=0.5)
        
        # Export for map
        print("\nExporting map data...")
        export_estates(db)
        
        # Export analytics
        print("\nExporting analytics...")
        export_analytics(db)

        print("\nGenerating charts...")
        generate_all_charts(db)
        
        # Print summary
        print_summary(db)
    
    # Show DB stats
    show_stats()


if __name__ == "__main__":
    main()
