# imdb_config.py

config = {

    "input_path": "input/IMDB_dataset.csv",
    "output_path": "output/IMDB_dataset_filtered.csv",

    "delimiter": ";",
    "mode": "validator",

    # Required columns (using normalized names)
    "required_columns": [
        "imbd_title_id",
        "original_titl",
        "genr",
        "country",
        "director"
    ],

    "optional_columns": [
        "content_rating",
        "release_year",
        "duration",
        "score",
        "income",
        "votes"
    ],

    "drop_columns": [
        "unnamed_8"
    ],


    # Text columns (normalized names)
    "text_columns": [
        "imbd_title_id",
        "original_titl",
        "genr",
        "country",
        "content_rating",
        "director"
    ],

    # Numeric columns
    "numeric_columns": [
        "duration",
        "income",
        "votes",
        "score",
        "release_year"
    ],

    "date_columns": [],

    # Recompute 
    "recompute": {},

    "validation_rules": [
        "release_year >= 1900 and release_year <= 2026",
        "score >= 0 and score <= 10"
    ]

}
