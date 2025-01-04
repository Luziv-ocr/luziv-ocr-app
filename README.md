# 🆔 Moroccan ID Card OCR

![Moroccan ID Card OCR](https://placeholder-for-project-banner.com/banner.jpg)

## 📖 Description

Moroccan ID Card OCR is an advanced optical character recognition (OCR) application designed specifically for extracting information from Moroccan identity cards. This project utilizes state-of-the-art OCR techniques to accurately parse and extract key details from ID cards, supporting both Arabic and French text. With added authentication using React.js and Supabase, it ensures secure access and data storage.

## 🔗 Quick Links

- [Streamlit App](https://moroccan-id-ocr.streamlit.app)
- [Authentication Page](https://moroccan-id-ocr-auth.vercel.app)

## 🎥 Demo

[Watch the Video Demo](https://link-to-your-video-demo.com)

![Demo GIF](https://placeholder-for-demo-gif.com/demo.gif)

## ✨ Features

- 🖼️ Image preprocessing for enhanced OCR accuracy
- 🔤 Supports both Arabic and French text extraction
- 📊 Intelligent parsing of extracted text
- 🔄 Automatic language detection and processing
- 📱 User-friendly Streamlit interface
- 🔒 Secure API integration with OCR.space
- 📜 Comprehensive logging for easy debugging
- 🔐 User authentication with React.js and Supabase
- 💾 Secure data storage using Supabase

## 🛠️ Installation

### OCR Application

1. Clone the repository:
git clone [https://github.com/yourusername/moroccan-id-ocr.git](https://github.com/yourusername/moroccan-id-ocr.git)
cd moroccan-id-ocr

2. Install required system dependencies:
sudo apt-get update
sudo apt-get install -y $(cat packages.txt)

3. Install Python dependencies:
pip install -r requirements.txt

4. Set up environment variables:
Create a `.env` file in the project root and add your OCR.space API key:
OCR_SPACE_API_KEY=your_api_key_here

### Authentication Application

1. Navigate to the auth directory:
cd auth

2. Install Node.js dependencies:
npm install

3. Set up Supabase environment variables:
Create a `.env.local` file in the auth directory and add your Supabase credentials:
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

## 🚀 Usage

### Running the OCR Application

1. Start the Streamlit application:

2. Open your web browser and navigate to `http://localhost:8501`.

3. Log in using your credentials from the authentication page.

4. Upload an image of a Moroccan ID card.

5. Click "Extract Text" to process the image and view the results.

### Running the Authentication Application

1. Start the React development server:

2. Open your web browser and navigate to `http://localhost:3000`.

3. Register a new account or log in with existing credentials.

## 📸 Screenshots

![Screenshot 1](https://placeholder-for-screenshot1.com/screenshot1.jpg)
*OCR Application Interface*

![Screenshot 2](https://placeholder-for-screenshot2.com/screenshot2.jpg)
*Authentication Page*

## 🧠 How It Works

1. **User Authentication**: Users log in through the React.js authentication page, which uses Supabase for secure user management.
2. **Image Upload**: Authenticated users upload an image through the Streamlit interface.
3. **Preprocessing**: The image is preprocessed to enhance text visibility.
4. **OCR Processing**: The preprocessed image is sent to the OCR.space API for text extraction.
5. **Text Parsing**: Extracted text is intelligently parsed to identify specific fields.
6. **Result Display**: Parsed information is displayed in a user-friendly format.
7. **Data Storage**: Extracted and parsed data is securely stored in Supabase for future reference.

## 🔒 Security

- User authentication is handled by Supabase, ensuring secure login and data access.
- All communication with the Supabase backend is encrypted.
- OCR.space API calls are made securely using API keys.
- Sensitive information is never stored in client-side code.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://github.com/yourusername/moroccan-id-ocr/issues).

## 📄 License

This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.

## 📞 Contact

Your Name - [@your_twitter](https://twitter.com/your_twitter) - email@example.com

Project Link: [https://github.com/yourusername/moroccan-id-ocr](https://github.com/yourusername/moroccan-id-ocr)
