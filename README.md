# Contact Finder

A customisable web-scraping agent built with Ollama that extracts business contact information from search results.

## Overview

This application uses a custom Qwen2.5 model to search for businesses and extract their contact details from websites, including:
- Phone numbers
- Email addresses
- Physical addresses
- Social media profiles
- Business hours
- Key personnel

## File Structure

The application is designed with modularity in mind:

- `Modelfile`: Configuration for the custom Ollama model
- `prompt_template.txt`: Template instructions for the model's extraction behaviour
- `config_manager.py`: Manages configuration settings
- `model_manager.py`: Handles Ollama model creation and querying
- `web_scraper.py`: Performs web searches and scrapes websites
- `contact_finder.py`: Orchestrates the overall process
- `bulk_contact_finder.py`: Enables bulk searches across multiple businesses
- `main.py`: Command-line interface for the application

## Installation

1. Make sure you have Ollama installed:
   ```bash
   # Follow instructions at https://ollama.ai/
   ```

2. Install the required Python dependencies:
   ```bash
   pip install requests beautifulsoup4 ollama
   ```

3. Clone this repository and navigate to its directory.

## Usage

### Initial Setup

Create your custom model (this will be saved as "miles_web" in Ollama):

```bash
python main.py setup
```

The model will be permanently saved in Ollama and can be used outside this application.

You can specify a different model name:
```bash
python main.py setup --model-name "custom_contact_finder"
```

### Finding Contact Information

The application follows a two-stage scraping workflow:

1. **Initial Search**:
   ```bash
   python main.py find "Lee's Custom Woodwork"
   ```
   This performs a search and extracts contact information from the search results only, without visiting individual URLs.

2. **Deep Scraping** (two options):
   
   a. After initial search, you'll be prompted if you want to scrape specific URLs for more details.
   
   b. Direct URL scraping:
   ```bash
   python main.py find "Lee's Custom Woodwork" --url "https://example.com/lees-woodwork"
   ```

3. **Interactive Mode**:
   ```bash
   python main.py find "Lee's Custom Woodwork" --interactive
   ```
   This starts an interactive session where you can select which URLs to scrape from the search results.

### Bulk Search

Perform searches across multiple businesses:

1. **Interactive Bulk Search**:
   ```bash
   python main.py bulk --interactive
   ```

2. **Bulk Search from Command Line**:
   ```bash
   python main.py bulk --names "Company A" "Company B" --query "contact details"
   ```

3. **Bulk Search from File**:
   ```bash
   python main.py bulk --input-file companies.txt --query "email addresses"
   ```

#### Saved Search Results

When you perform a bulk search, results are automatically saved:

- Location: `contact_search_results/` directory
- Filename format: `bulk_search_{query}_{timestamp}.csv`
- File contents:
  - Name of the business
  - Search query used
  - Extracted result text
  - Source URLs
  - Any errors encountered

Example filename:
```
contact_search_results/bulk_search_contact_details_20250401_145245.csv
```

The CSV provides a comprehensive record of the search, making it easy to review and use the results later.

### Configuration

View all settings:

```bash
python main.py config --list
```

Change a setting:

```bash
python main.py config --set search_engine "https://duckduckgo.com/?q="
python main.py config --set max_search_results 10
```

Get a specific setting:

```bash
python main.py config --get model_name
```

## Customisation

### Changing the Base Model

Edit the `Modelfile` and change the `FROM` line to use a different base model:

```
FROM llama3:latest
```

Then regenerate your custom model:

```bash
python main.py setup
```

### Modifying Extraction Behaviour

Edit `prompt_template.txt` to change how the model extracts and formats contact information.

### Adjusting Scraping Settings

You can modify scraping behaviour through configuration:

```bash
python main.py config --set request_delay 2.0
python main.py config --set max_search_results 8
```

## Advanced Customisation

You can extend functionality by modifying the individual component files:

- `web_scraper.py`: Add support for additional search engines or extraction patterns
- `model_manager.py`: Implement advanced Ollama features or caching
- `contact_finder.py`: Add new analysis or verification steps
- `bulk_contact_finder.py`: Customise bulk search behaviour

## Using the Model Outside This Application

Since the model is saved in Ollama, you can use it directly:

```bash
# Run interactive mode
ollama run miles_web

# One-off query
echo "Find contact info for Tesla Motors" | ollama run miles_web
```

In Python applications:
```python
import ollama

# Generate a response
response = ollama.generate(model="miles_web", 
                         prompt="Find contact info for Apple Inc")
print(response['response'])
```

This makes the model reusable across all your projects.

## License

MIT