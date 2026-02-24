import json
from utils import load_config, ensure_output_dir

# Assuming you place your refactored crawler class here
from crawlers.generic_crawler import LanguageCrawler 

def main():
    print("Loading crawler configuration...")
    try:
        config = load_config("config.json")
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    global_settings = config.get("global_settings", {})
    languages = config.get("languages", {})

    for lang_name, settings in languages.items():
        if not settings.get("enabled", False):
            print(f"⏩ Skipping {lang_name.capitalize()} (disabled in config).")
            continue
            
        print(f"\n--- 🚀 Starting crawler for {lang_name.upper()} ---")
        
        # Ensure the 'data/' folder exists
        output_file = settings["output_file"]
        ensure_output_dir(output_file)
        
        # Initialize the crawler dynamically based on the JSON config
        # Support both `base_url` (single) and `base_urls` (list) in config
        base_urls = settings.get("base_urls") or ([settings.get("base_url")] if settings.get("base_url") else [])

        crawler = LanguageCrawler(
            base_urls=base_urls,
            max_pages=settings["max_pages"],
            lang_code=settings["lang_code"],
            regex_pattern=settings["regex_pattern"],
            headers={"User-Agent": global_settings.get("user_agent")},
            max_workers=global_settings.get("max_workers", 10)
        )
        
        # Run extraction
        dataset = crawler.crawl()
        
        # Save output
        with open(output_file, "w", encoding="utf-8") as f:
            for item in dataset:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        print(f"✅ Finished {lang_name.capitalize()}. Saved {len(dataset)} records to {output_file}.")

if __name__ == "__main__":
    main()