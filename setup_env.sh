#!/bin/bash
# One-shot environment setup for Chicago Closure Radar

set -e

echo "=== Chicago Closure Radar — Environment Setup ==="

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy env template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from template — add your API keys there"
fi

echo ""
echo "=== Setup complete! Next steps: ==="
echo ""
echo "1. Activate env:   source .venv/bin/activate"
echo ""
echo "2. Get Yelp data (choose one):"
echo "   a) Academic: https://business.yelp.com/data/resources/open-dataset/"
echo "      → unzip into data/raw/yelp/"
echo "   b) Kaggle:  kaggle datasets download adamamer2001/yelp-complete-open-dataset-2024 -p data/raw/yelp/ --unzip"
echo ""
echo "3. (Optional) Get a free Chicago Data Portal token at:"
echo "   https://data.cityofchicago.org/profile/app_tokens"
echo "   → add to .env as CHICAGO_PORTAL_APP_TOKEN=..."
echo ""
echo "4. Run notebooks in order:"
echo "   jupyter lab notebooks/"
