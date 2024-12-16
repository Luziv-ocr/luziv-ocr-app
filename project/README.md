# Moroccan Document OCR System

This application extracts text from Moroccan ID cards and driving licenses using OCR technology and stores the information in a MySQL database.

## Features

- Upload and process Moroccan ID cards and driving licenses
- Extract text using OCR.space API
- Parse and structure extracted information
- Store data in MySQL database
- User-friendly Streamlit interface
- Support for both Arabic and English text

## Setup

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up MySQL database and update `.env` file with your credentials

3. Get an API key from [OCR.space](https://ocr.space/ocrapi) and add it to `.env`

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Project Structure

- `app.py`: Main Streamlit application
- `database/`: Database configuration and data access
- `utils/`: Utility functions for OCR and text parsing
- `requirements.txt`: Project dependencies

## Environment Variables

Create a `.env` file with the following variables:
```
OCR_API_KEY=your_api_key
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=ocr_documents
```