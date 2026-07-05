```markdown
# AI Freelancer Assistant

An AI-powered web application that helps freelancers automate their daily tasks including proposal generation, cover letters, invoices, contracts, and more.

## Features

- User Authentication (Register, Login, Forgot Password)
- AI Proposal Generator
- AI Cover Letter Generator
- Gig Description Generator (Fiverr)
- Smart Pricing Calculator
- Client Reply Generator
- Invoice Generator (PDF Export)
- Contract Generator (PDF Export)
- Complete History Management
- User Profile & Settings
- Theme Switching (Dark/Light)

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **AI:** Groq API (LLaMA 3.3-70b)
- **PDF Generation:** FPDF2
- **Frontend:** HTML, CSS, JavaScript

## Installation

1. Clone the repository
```
git clone https://github.com/SaraWaheed456/ai-freelancer-assistant.git
cd ai-freelancer-assistant
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Add your Groq API key in `app.py`
```
GROQ_API_KEY = "your_key_here"
```

4. Run the application
```
python app.py
```

5. Open browser
```
http://127.0.0.1:5000
```

## Project Structure

```
ai-freelancer-assistant/
├── app.py
├── database.db
├── requirements.txt
├── README.md
├── templates/
│   ├── dashboard.html
│   ├── proposals.html
│   ├── cover_letters.html
│   ├── gig_generator.html
│   ├── pricing.html
│   ├── client_replies.html
│   ├── invoices.html
│   ├── contracts.html
│   ├── history.html
│   ├── profile.html
│   ├── settings.html
│   └── ...
└── static/
    ├── css/style.css
    ├── js/script.js
    └── uploads/
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | /login | User login |
| GET/POST | /register | User registration |
| GET | /dashboard | Main dashboard |
| GET/POST | /proposals/create | Create AI proposal |
| GET | /proposals | View all proposals |
| GET/POST | /cover-letters/create | Create cover letter |
| GET/POST | /gig-generator/create | Create gig description |
| GET/POST | /pricing/create | Calculate pricing |
| GET/POST | /client-replies/create | Generate client reply |
| GET/POST | /invoices/create | Create invoice |
| GET/POST | /contracts/create | Create contract |
| GET | /history | View all history |
| GET/POST | /profile | Edit profile |
| GET/POST | /settings | App settings |
| GET | /logout | Logout |

## Database Tables

| Table | Description |
|-------|-------------|
| users | User login information |
| user_profiles | User profile details |
| proposals | Generated proposals |
| cover_letters | Generated cover letters |
| gig_descriptions | Fiverr gig descriptions |
| pricing_history | Pricing calculations |
| client_replies | Client message replies |
| invoices | Generated invoices |
| contracts | Generated contracts |
| settings | User preferences |

## Deployment

Deployed on Render: https://ai-freelancer-assistant-production.up.railway.app
## Developer

Sara Waheed
Internship Project — AI Freelancer Assistant
```
