# Web Crawler
A scalable, multilingual web crawler designed to extract text in any language. Using dynamic Unicode block filtering, it isolates specific scripts—from Gujarati to Mandarin—while ignoring noise. Ideal for building diverse NLP datasets, global data mining, and linguistic research. Configurable, fast, and ready for any localized scraping task.

**Web Crawler** helps extract textual content in a target language from a base URL using configurable patterns and Unicode-script filtering. It is intended as a lightweight foundation for creating datasets for NLP research, dataset bootstrapping, or language analysis.

**Features**
- **Multilingual**: Configure separate crawlers per language.
- **Config-driven**: All behavior is controlled by a single `config.json` file.
- **Unicode-aware filtering**: Grab text for a specific script or language using regex patterns.
- **Concurrent fetching**: Uses a worker pool (configurable) to speed up crawling.

**Requirements**
- Python 3.8+
- No external dependencies in the repository by default (uses stdlib).

**Quick Start**
1. Edit the project configuration in [config.json](config.json).
2. Run the crawler:

```bash
python main.py
```

Output records are written as newline-delimited JSON to the `output_file` paths defined per language (e.g. `data/english_corpus.jsonl`).

**Configuration**
The project is driven by [config.json](config.json). Minimal example structure:

```json
{
	"global_settings": {
		"user_agent": "my-crawler/1.0",
		"max_workers": 8
	},
	"languages": {
		"english": {
			"enabled": true,
			"base_url": "https://example.com/en",
			"output_file": "data/english_corpus.jsonl",
			"max_pages": 500,
			"lang_code": "en",
			"regex_pattern": "[\\u0000-\\u007F]+"
		}
	}
}
```

Key fields:
- `global_settings.user_agent`: HTTP User-Agent header for requests.
- `global_settings.max_workers`: concurrency for fetching pages.
- Per-language `enabled`: toggle crawling for that language.
- Per-language `base_url`, `max_pages`, `lang_code`, `regex_pattern`, `output_file`.

**Project layout**
- [main.py](main.py) — runner that loads config and executes language crawlers.
- [utils.py](utils.py) — helper utilities (config loading, directory creation).
- crawlers/generic_crawler.py — crawler implementation used by `main.py`.
- [config.json](config.json) — main configuration file.
- `data/` — default output directory for generated corpora.

**Extending**
- Add new language entries to [config.json](config.json).
- Extend or replace the crawler in `crawlers/generic_crawler.py` to change fetching, parsing, or filtering logic.

**Contributing**
- Open issues or PRs. Keep changes focused and include tests where appropriate.

**License**
This repository includes a `LICENSE` file — follow the stated license when using or contributing.

---
If you'd like, I can also:
- add a sample `config.json` with multiple languages,
- or run a quick local test crawl and show sample output.
