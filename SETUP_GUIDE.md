# Hospital Prediction System - Setup Guide

## Overview
This is a complete Hospital Appointment Management System with:
- **Backend**: FastAPI + Random Forest ML Model + Firebase
- **Frontend**: React + Vite + Tailwind CSS + Firebase Authentication
- **Database**: Firestore (NoSQL)

---

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Firebase Project (Already created: `hospital-management-f5f43`)
- Git

---

## 🔧 Backend Setup

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Verify .env File

The `.env` file already contains your Firebase credentials. Check it:

```bash
cat .env
```

The file should contain your Firebase credentials and configuration.

### Step 3: Run Backend Server

```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Backend API Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/verify-token` - Verify Firebase token
- `GET /auth/profile` - Get user profile

#### Predictions
- `POST /predict` - Make a prediction
- `GET /predictions/history` - Get user's prediction history
- `GET /predictions/statistics` - Get user statistics
- `DELETE /predictions/{id}` - Delete a prediction

#### Model Training
- `POST /train` - Train/retrain the model
- `GET /health` - Health check

---

## 🎨 Frontend Setup

### Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 2: Verify .env File

Check that `.env` file exists with API URL:

```bash
cat .env
```

Should contain:
```
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_*=...
```

### Step 3: Run Frontend Development Server

```bash
npm run dev
```

**Expected Output:**
```
VITE v6.0.11  ready in XX ms

➜  Local:   http://localhost:5173/
```

### Step 4: Access the Application

Open your browser and go to: **http://localhost:5173**

---

## 🚀 First-Time Usage

### 1. Create an Account
- Click "Sign up"
- Enter email, password, and full name
- Click "Sign Up"

### 2. Make a Prediction
- You'll be redirected to the dashboard
- Fill in the form with clinic parameters:
  - Day of week
  - Hour (0-23)
  - Number of doctors
  - Scheduled appointments
  - Walk-in patients
  - Average consultation time
  - Rain intensity
  - Holiday (checkbox)
- Click "Get Prediction"

### 3. View Results
- See predicted load score
- Expected wait minutes
- Risk level (LOW/MEDIUM/HIGH)

### 4. Check History
- Click "History" tab
- View all your previous predictions
- Delete predictions if needed

---

## 📊 Database Structure (Firestore)

### Collections

#### `users`
```json
{
  "uid": "string",
  "email": "string",
  "full_name": "string",
  "created_at": "timestamp",
  "predictions_count": "number",
  "last_prediction_at": "timestamp"
}
```

#### `predictions`
```json
{
  "user_id": "string",
  "input_data": {
    "day_of_week": "number",
    "hour": "number",
    "doctor_count": "number",
    "scheduled_appointments": "number",
    "walk_in_patients": "number",
    "avg_consultation_minutes": "number",
    "is_holiday": "boolean",
    "rain_intensity": "number"
  },
  "predicted_load_score": "number",
  "expected_wait_minutes": "number",
  "risk_level": "string (LOW/MEDIUM/HIGH)",
  "timestamp": "timestamp",
  "created_at": "string (ISO)"
}
```

---

## 🔐 Environment Variables

### Backend (.env)
```
FIREBASE_CREDENTIALS_JSON=<your-service-account-json>
FIREBASE_API_KEY=AIzaSyABbdUTEhAfS4gKVbobHIyWQ5d6CBRt8tY
FIREBASE_AUTH_DOMAIN=hospital-management-f5f43.firebaseapp.com
FIREBASE_PROJECT_ID=hospital-management-f5f43
FIREBASE_STORAGE_BUCKET=hospital-management-f5f43.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=77023761322
FIREBASE_APP_ID=1:77023761322:web:1039e742934d54021b11d3
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=AIzaSyABbdUTEhAfS4gKVbobHIyWQ5d6CBRt8tY
VITE_FIREBASE_AUTH_DOMAIN=hospital-management-f5f43.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=hospital-management-f5f43
VITE_FIREBASE_STORAGE_BUCKET=hospital-management-f5f43.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=77023761322
VITE_FIREBASE_APP_ID=1:77023761322:web:1039e742934d54021b11d3
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version

# Clear cache
rm -rf __pycache__

# Reinstall packages
pip install --force-reinstall -r requirements.txt
```

### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall packages
rm -rf node_modules
npm install
```

### Firebase Authentication Error
> Make sure `.env` files are in correct locations:
> - Backend: `backend/.env`
> - Frontend: `frontend/.env`

### CORS Error
> The backend is already configured for CORS. If you get CORS errors:
> 1. Check that backend is running on `http://localhost:8000`
> 2. Check that frontend is running on `http://localhost:5173` or `http://localhost:3000`

### Connection Refused
> Ensure both servers are running:
> ```bash
> # Terminal 1 - Backend
> cd backend/app && python -m uvicorn main:app --reload
>
> # Terminal 2 - Frontend
> cd frontend && npm run dev
> ```

---

## 📦 Project Structure

```
Hospital-Prediction/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app with routes
│   │   ├── model_service.py  # ML model prediction logic
│   │   ├── training.py       # Data generation & training
│   │   ├── schemas.py        # Pydantic models
│   │   ├── auth_service.py   # Firebase authentication
│   │   ├── database.py       # Firestore operations
│   │   └── firebase_config.py # Firebase initialization
│   ├── model/
│   │   └── load_predictor.joblib
│   ├── requirements.txt
│   ├── .env                  # Firebase credentials
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PredictionForm.jsx
│   │   │   ├── PredictionHistory.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── DashboardPage.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── firebase.js       # Firebase configuration
│   │   ├── api.js            # API client
│   │   ├── App.jsx           # Main app with routing
│   │   ├── main.jsx          # React entry
│   │   └── styles.css        # Tailwind CSS
│   ├── package.json
│   ├── .env                  # Frontend environment
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── README.md
```

---

## 🎯 Next Steps

1. **Test the System**
   - Register a test account
   - Make several predictions
   - Check history and statistics

2. **Customize**
   - Update UI colors/branding in `tailwind.config.js`
   - Add more ML features in `training.py`
   - Extend authentication (Google login, etc.)

3. **Deploy**
   - Backend: Deploy to Heroku, Railway, or Google Cloud
   - Frontend: Deploy to Vercel, Netlify, or GitHub Pages
   - Firebase: Already hosted

4. **Monitor**
   - Check Firestore database usage
   - Monitor Firebase authentication logs
   - Track API performance

---

## 📞 Support

If you encounter issues:
1. Check the `.env` files are correctly set up
2. Ensure both backend and frontend are running
3. Check browser console for error messages
4. Check backend terminal for API errors

---

## 📝 License

This project is part of the Hospital Prediction System.

---

**Happy predicting!** 🎉
