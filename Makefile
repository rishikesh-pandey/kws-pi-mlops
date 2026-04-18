# Variables
IMAGE_NAME = mlops-pipeline

# 1. Build the Docker environment
build-env:
	docker build -t $(IMAGE_NAME) .

# 2. Open a terminal inside the container (for testing)
shell:
	docker run -it --rm --env-file .env --mount type=bind,source="$$(pwd)",target=/app $(IMAGE_NAME) bash

# 3. Run the entire pipeline end-to-end automatically
run-pipeline:
	docker run --rm --env-file .env --mount type=bind,source="$(CURDIR)",target=/app mlops-pipeline \
	bash -c "python scripts/ingest_data.py && python scripts/train_model.py && python scripts/test_model.py && python scripts/deploy_board.py && python scripts/build_bin.py"