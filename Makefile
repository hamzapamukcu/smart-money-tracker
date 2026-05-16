.PHONY: setup fetch-data run clean docker-run docker-fetch

setup:
	@echo "Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "Setup complete! Please make sure to configure your .env file by copying .env.example"

fetch-data:
	@echo "Initializing database and fetching data..."
	.venv/bin/python scripts/init_db.py

run:
	@echo "Starting the Streamlit dashboard..."
	.venv/bin/streamlit run app/main.py

clean:
	@echo "Cleaning up Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-run:
	@echo "Running the app with Docker..."
	docker-compose up --build

docker-fetch:
	@echo "Fetching data inside the Docker container..."
	docker-compose exec app python scripts/init_db.py
