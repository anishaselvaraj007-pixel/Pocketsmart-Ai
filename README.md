# PocketSmart AI 💜

## Your Smart Budget & Recommendation Assistant

PocketSmart AI is a GenAI-powered recommendation system that helps users plan their budget and get smart recommendations for different needs.

## ✨ Features

### 🏠 Home Interior Planning

Users can enter:

* Budget
* Room type
* Item name
* Quantity

The system generates AI-based home interior recommendations according to the user's budget and requirements.

### 🎉 Party Budget Planning

Users can enter:

* Budget
* Number of guests
* Event type
* Venue

The system creates a party budget plan with estimated spending for catering, decoration, entertainment, cake and other expenses.

### 💎 Jewelry Recommendations

Users can enter:

* Budget
* Occasion
* Jewelry style
* Outfit/Dress type

The system provides AI-based jewelry recommendations suitable for the selected occasion, style and budget.

## 🤖 AI Integration

PocketSmart AI uses Google's Gemini Generative AI to generate personalized recommendations and suggestions.

## 🔐 Authentication

The application includes:

* User Registration
* User Login
* Session-based Authentication
* Logout
* Protected Dashboard
* Recommendation History

## 🛠️ Technologies Used

* Python
* FastAPI
* Jinja2
* Google Gemini AI
* SQLAlchemy
* SQLite
* HTML
* CSS
* JavaScript
* Uvicorn

## 📁 Project Structure

```text
PocketSmart-AI/
│
├── main.py
├── requirements.txt
├── README.md
│
└── templates/
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── home.html
    ├── party.html
    ├── jewelry.html
    └── history.html
```

## 🚀 How to Run

### 1. Create virtual environment

```bash
python -m venv venv
```

### 2. Activate virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and add:

```text
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET_KEY=your_secret_key
```

Do not upload the `.env` file to GitHub.

### 5. Run the application

```bash
uvicorn main:app --reload
```

### 6. Open in browser

```text
http://127.0.0.1:8000
```

## 🎯 Project Objective

The main objective of PocketSmart AI is to provide an easy-to-use AI assistant that helps users make budget-conscious decisions and receive personalized recommendations based on their requirements.

## 🌟 Future Enhancements

* Product recommendations from online shopping platforms
* Real-time product price comparison
* Image-based jewelry analysis
* More personalized user history
* Advanced recommendation algorithms
* Mobile application
* Cloud deployment
* Additional AI-powered planning modules

## 👩‍💻 Project

**PocketSmart AI – Your Smart Budget & Recommendation Assistant**

Built using Python, FastAPI and Generative AI.
