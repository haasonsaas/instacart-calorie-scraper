# Instacart Calorie Scraper

A Python script that enriches Instacart product data with nutritional information by querying OpenFoodFacts and USDA FoodData Central APIs.

## Features

- Processes JSON product dumps from multiple stores (Target, Safeway, Costco)
- Automatically fetches calorie data from two sources:
  1. OpenFoodFacts API (free, no key required)
  2. USDA FoodData Central API (optional, requires API key)
- Filters out non-food items automatically
- Outputs unified CSV with store, product name, location, price, and calories per serving
- Rate-limited to be respectful to APIs (0.5s delay between requests)

## Requirements

```bash
pip install requests pandas
```

## Usage

```bash
export USDA_API_KEY="your-fdc-key"   # optional but recommended
python instacart_calorie_scraper.py \
  --targets  /path/to/products_target.json \
  --safeway  /path/to/products_safeway.json \
  --costco   /path/to/products_costco.json \
  --out      instacart_with_calories.csv
```

## Input Format

The script expects JSON files with product objects containing:
- `name`: Product name
- `price`: Price string (will extract numeric value)
- `location`: Aisle or department location

## Output Format

CSV file with columns:
- `Store`: Store name (Target, Safeway, Costco)
- `Name`: Product name
- `Location`: Aisle/department
- `Price_USD`: Numeric price
- `Calories_per_serving`: Calories per serving or "N/A" for non-food items

## API Data Sources

1. **OpenFoodFacts**: Free, community-driven food database
2. **USDA FoodData Central**: Official USDA nutritional database (requires free API key)

## Example Output

The included `instacart_with_calories.csv` contains 90 products with their nutritional information scraped from the APIs.