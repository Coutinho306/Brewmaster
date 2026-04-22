"""
Golden dataset for RAG evaluation.
Each entry: question + reference answer (ground truth).
Questions are grounded in the Bees-Brewery-Pipeline docs (README + MONITORING).
"""

SAMPLES = [
    {
        "question": "What is the purpose of the bronze layer in the pipeline?",
        "ground_truth": "The bronze layer is responsible for raw data ingestion from the Open Brewery DB API. It stores data in its original format without transformations, serving as the landing zone for all incoming data.",
    },
    {
        "question": "What does the silver layer do with the ingested data?",
        "ground_truth": "The silver layer applies transformations and data quality checks to the raw bronze data, cleaning and standardizing it before it moves to the gold layer.",
    },
    {
        "question": "What is the gold layer responsible for?",
        "ground_truth": "The gold layer aggregates and enriches the cleaned silver data into business-ready datasets, optimized for analytics and reporting.",
    },
    {
        "question": "What technology is used to orchestrate the pipelines?",
        "ground_truth": "Apache Airflow is used to orchestrate the data pipelines in the Bees-Brewery-Pipeline project.",
    },
    {
        "question": "What API is used as the data source?",
        "ground_truth": "The Open Brewery DB API is used as the external data source for the pipeline.",
    },
    {
        "question": "What monitoring is in place for the pipelines?",
        "ground_truth": "The project includes a monitoring layer that tracks pipeline run status, alerts on failures, and performs data quality checks after each pipeline execution.",
    },
    {
        "question": "How does the pipeline handle data quality checks?",
        "ground_truth": "Data quality checks are executed after each pipeline stage to validate completeness, consistency, and correctness of the data before it advances to the next layer.",
    },
    {
        "question": "What storage format is used in the medallion architecture?",
        "ground_truth": "The pipeline uses a medallion architecture with Bronze, Silver, and Gold layers, typically storing data in structured formats managed by Airflow tasks.",
    },
]
