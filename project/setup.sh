#!/bin/bash
# setup.sh

# Update package list
apt-get update

# Install Tesseract and required language packs
apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-ara
apt-get install -y tesseract-ocr-fra
apt-get install -y tesseract-ocr-eng
apt-get install -y libtesseract-dev

# Verify installation
tesseract --version