#!/bin/bash
set -e  # Exit on error

# Update and install dependencies
apt-get update -y
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libtesseract-dev

# Create directory for tesseract
mkdir -p ~/.streamlit/