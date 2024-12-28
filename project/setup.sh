#!/bin/bash
set -e  # Exit on error

# Update package lists
apt-get update -y

# Install required system libraries
apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgstreamer1.0-0

# Install Tesseract and language packs
apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-eng

# Create necessary directories
mkdir -p ~/.streamlit/
mkdir -p /usr/share/tesseract-ocr/4.00/tessdata

# Download additional language data
wget -O /usr/share/tesseract-ocr/4.00/tessdata/ara.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/ara.traineddata
wget -O /usr/share/tesseract-ocr/4.00/tessdata/fra.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata

# Set environment variables
echo "export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata" >> ~/.bashrc

