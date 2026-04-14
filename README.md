# Hospital Prediction System

A smart appointment and clinic load prediction system with user authentication, prediction history, and real-time analytics.

## 🎯 Features

- ✅ **User Authentication** - Firebase Auth (Email/Password)
- ✅ **ML Predictions** - Random Forest model for clinic load prediction
- ✅ **Prediction History** - Store and manage all predictions
- ✅ **User Statistics** - Track average wait times and risk levels
- ✅ **Real-time Dashboard** - Monitor current clinic status
- ✅ **Responsive Design** - Beautiful Tailwind CSS UI
- ✅ **Secure API** - Token-based authentication

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│       • Login/Register • Dashboard • Predictions             │
│       • History • Statistics • Responsive UI (Tailwind)      │
└────────────────────────┬────────────────────────────────────┘
                         │ API (Axios)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│   • Auth Endpoints • Prediction API • Firestore Integration  │
│   • ML Model Service • Training Pipeline                     │
└────────────────────────┬────────────────────────────────────┘
                         │ Firebase SDK
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Firebase (Backend)                        │
│ • Authentication • Firestore Database • Cloud Storage       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Automated Start (Windows)
```bash
# Run this from the project root
start.bat
```

### Option 2: Automated Start (Linux/Mac)
```bash
# Run this from the project root
chmod +x start.sh
./start.sh
```

### Option 3: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend/app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open: **http://localhost:5173**

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Firebase Project (Created: `hospital-management-f5f43`)

## ⚙️ Installation

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## 🔧 Configuration

### Backend `.env` file (already configured)
```
FIREBASE_CREDENTIALS_JSON=<your-service-account>
FIREBASE_PROJECT_ID=hospital-management-f5f43
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend `.env` file (already configured)
```
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_PROJECT_ID=hospital-management-f5f43
```

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Create new account
- `POST /auth/verify-token` - Verify JWT token
- `GET /auth/profile` - Get user profile

### Predictions
- `POST /predict` - Make clinic load prediction
- `GET /predictions/history` - Get prediction history
- `GET /predictions/statistics` - Get user statistics
- `DELETE /predictions/{id}` - Delete prediction

### Model
- `POST /train` - Train/retrain ML model
- `GET /health` - Health check

## 📊 Database Schema

### Firestore Collections
- `users/` - User profiles and preferences
- `predictions/` - Historical predictions

See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed database structure.

## 🎨 Frontend Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Firebase SDK** - Authentication
- **Axios** - HTTP client
- **Lucide React** - Icons

## 🐍 Backend Stack

- **FastAPI** - Web framework
- **scikit-learn** - ML model
- **Firebase Admin SDK** - Backend services
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

## 📖 Documentation

For detailed setup and troubleshooting, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)

## 🔐 Security Features

- JWT token-based authentication
- Firebase Admin SDK for server-side auth verification
- CORS protection
- Secure credential management via environment variables
- User data isolation in Firestore

## 📁 Project Structure

```
Hospital-Prediction/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── model_service.py     # ML predictions
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── database.py          # Firestore operations
│   │   ├── firebase_config.py   # Firebase setup
│   │   ├── training.py          # Data generation
│   │   └── schemas.py           # Data models
│   ├── model/
│   │   └── load_predictor.joblib
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── context/
│   │   ├── api.js
│   │   ├── firebase.js
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── .env
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── SETUP_GUIDE.md
├── README.md
├── start.bat
└── start.sh
```

## 🎓 Usage

1. **Create Account**: Register with email and password
2. **Input Clinic Data**: Enter current clinic parameters
3. **Get Prediction**: Receive clinic load score and wait time estimates
4. **View History**: Check all previous predictions
5. **Analyze Trends**: Monitor statistics and patterns

## 🐛 Troubleshooting

See [SETUP_GUIDE.md](./SETUP_GUIDE.md#-troubleshooting) for detailed troubleshooting steps.

## 📝 License

This project is part of the Hospital Prediction System.

## 🤝 Contributing

- Report bugs via GitHub Issues
- Submit improvements via Pull Requests

---

**Happy predicting!** 🎉

For full documentation, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

If needed, set API URL in `frontend/.env`:

```env
VITE_API_BASE=http://127.0.0.1:8000
```

## 3) Build Frontend

```powershell
cd frontend
npm run build
```

## Model Details

The backend auto-trains a model at startup if no artifact exists.

Features used:
- day_of_week
- hour
- doctor_count
- scheduled_appointments
- walk_in_patients
- avg_consultation_minutes
- is_holiday
- rain_intensity

Outputs:
- predicted load score
- expected wait time (minutes)
- risk level (LOW / MEDIUM / HIGH)

Use `POST /train` anytime to retrain the model.
