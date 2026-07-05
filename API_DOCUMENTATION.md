# AI Freelancer Assistant - API Documentation

## Base URL
http://127.0.0.1:5000 (Local)
https://ai-freelancer-assistant-production.up.railway.app (Production)

## Authentication Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET/POST | /login | User login | email, password |
| GET/POST | /register | User registration | fullname, email, password, confirmPassword |
| GET/POST | /forgot-password | Password reset | email |
| GET | /logout | User logout | - |

## Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dashboard | Main dashboard with stats |

## Proposals

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /proposals | List all proposals | - |
| GET/POST | /proposals/create | Create new proposal | client_name, project_title, project_description, skills, budget, timeline, tone |
| GET/POST | /proposals/edit/<id> | Edit proposal | generated_text |
| GET | /proposals/delete/<id> | Delete proposal | - |
| GET | /proposals/export/<id> | Export proposal as PDF | - |

## Cover Letters

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /cover-letters | List all cover letters | - |
| GET/POST | /cover-letters/create | Create cover letter | job_title, company_name, experience, skills, portfolio_url |
| GET/POST | /cover-letters/edit/<id> | Edit cover letter | generated_text |
| GET | /cover-letters/delete/<id> | Delete cover letter | - |
| GET | /cover-letters/export/<id> | Export as PDF | - |

## Gig Generator

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /gig-generator | List all gigs | - |
| GET/POST | /gig-generator/create | Create gig description | category, skills, experience_level, delivery_time, features, revisions |
| GET | /gig-generator/delete/<id> | Delete gig | - |

## Pricing Calculator

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /pricing | List pricing history | - |
| GET/POST | /pricing/create | Calculate pricing | hourly_rate, estimated_hours, complexity, urgency, additional_charges, tax |
| GET | /pricing/delete/<id> | Delete record | - |

## Client Replies

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /client-replies | List all replies | - |
| GET/POST | /client-replies/create | Generate reply | client_message, tone |
| GET | /client-replies/delete/<id> | Delete reply | - |

## Invoices

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /invoices | List all invoices | - |
| GET/POST | /invoices/create | Create invoice | client_name, client_email, project_title, services, amount, tax, due_date |
| GET | /invoices/export/<id> | Download PDF | - |
| GET | /invoices/delete/<id> | Delete invoice | - |

## Contracts

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /contracts | List all contracts | - |
| GET/POST | /contracts/create | Create contract | client_name, client_email, freelancer_name, freelancer_email, project_scope, timeline, payment_terms, terms_conditions |
| GET | /contracts/export/<id> | Export as PDF | - |
| GET | /contracts/delete/<id> | Delete contract | - |

## User Management

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | /history | View complete history | - |
| GET/POST | /profile | View/edit profile | full_name, bio, phone, location, skills, profile_picture |
| GET/POST | /settings | App settings | groq_api_key, theme, language, notifications |

## AI Integration
- Provider: Groq API
- Model: LLaMA 3.3-70b-versatile
- Used for: Proposals, Cover Letters, Gig Descriptions, Pricing Analysis, Client Replies, Contracts

## Database Tables
- users
- user_profiles
- proposals
- cover_letters
- gig_descriptions
- pricing_history
- client_replies
- invoices
- contracts
- settings