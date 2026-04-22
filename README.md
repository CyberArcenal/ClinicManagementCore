# 🏥 ClinicManagementCore

A modular, high‑performance backend for clinic management systems built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. Designed as a modular monolith – ready to scale, easy to maintain.

## ✨ Features

- 👥 **User management** with role‑based access (Admin, Doctor, Nurse, Receptionist, Patient, Lab Tech, Pharmacist)
- 🧑‍⚕️ **Patient records** (demographics, medical history, allergies)
- 📅 **Appointment scheduling** with status tracking
- 🩺 **Electronic Health Records (EHR)** – diagnosis, treatment plans, clinical notes
- 💊 **Prescriptions** & e‑prescribing
- 🧪 **Lab results** management
- 💰 **Billing, Invoicing & Payments** (cash, card, insurance)
- 🛡️ **Insurance claims** tracking
- 📦 **Inventory** for medicines & supplies
- 🏥 **Room / facility** management
- 🔔 **Notifications** (email/SMS ready)
- 📊 **Reports & analytics** foundation
- 🔐 **JWT authentication** ready (implement in services)

## 🧱 Tech Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Framework    | FastAPI                                         |
| ORM          | SQLAlchemy (async‑ready)                        |
| Migrations   | Alembic                                         |
| Database     | PostgreSQL (recommended) / SQLite (dev)         |
| Validation   | Pydantic V2                                     |
| Auth         | python-jose + passlib (JWT)                     |
| Container    | Docker & Docker Compose                         |
| Server       | Uvicorn (ASGI)                                  |

## 📁 Project Structure

```
ClinicManagementCore/
├── app/
│   ├── api/                 # API layer (routers, endpoints)
│   │   ├── v1/
│   │   │   └── endpoints/   # per‑module route handlers
│   │   └── dependencies/    # DI (auth, db sessions)
│   ├── core/                # config, database, security, exceptions
│   ├── models/              # SQLAlchemy models (modular folders)
│   │   ├── base.py          # declarative base & BaseModel (id, timestamps)
│   │   ├── user/            # User, DoctorProfile, NurseProfile, etc.
│   │   ├── patient/         # Patient model
│   │   ├── appointment/     # Appointment model
│   │   ├── ehr/             # Electronic Health Record
│   │   ├── prescription/    # Prescription + items
│   │   ├── lab_result/      # Lab results
│   │   ├── treatment/       # Treatments / procedures
│   │   ├── billing/         # Invoice, BillingItem, Payment
│   │   ├── insurance/       # InsuranceDetail, InsuranceClaim
│   │   ├── staff/           # DoctorSchedule
│   │   ├── inventory/       # InventoryItem, Transaction
│   │   ├── room/            # Room model
│   │   ├── notifications/   # Notification model
│   │   ├── reports/         # ReportLog
│   │   └── patient_portal/  # Access logs
│   ├── modules/             # Business logic (services, schemas per module)
│   └── main.py              # FastAPI app entry point
├── migrations/              # Alembic migration scripts
├── tests/                   # Pytest suite
├── .env                     # Environment variables (not committed)
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

> The model layer is already split by domain – each folder contains its own `models.py` and all are imported via `app/models/__init__.py` so that Alembic can discover them.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (or Docker)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ClinicManagementCore.git
cd ClinicManagementCore
```

### 2. Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate          # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/clinicdb
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

## 🐳 Running with Docker (recommended)

The project includes a complete Docker setup.

```bash
docker-compose up --build
```

Services:
- FastAPI app → http://localhost:8000
- PostgreSQL → localhost:5432
- pgAdmin (optional) → http://localhost:5050 (email: `admin@clinic.com`, password: `admin`)

Run migrations inside the container:

```bash
docker-compose exec api alembic upgrade head
```

## 🧪 Testing

```bash
pytest tests/
```

## 📦 Database Migrations (Alembic)

Create a new migration after changing models:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🔐 Authentication (to be implemented)

The project is ready for JWT authentication. Example dependency:

```python
from app.api.dependencies import get_current_user
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the **GNU General Public License v3.0** – see the [LICENSE](LICENSE) file for details.

You may copy, distribute and modify the software as long as you track changes/dates in source files. Any modifications to or software including (via compiler) GPL-licensed code must also be made available under the GPL along with build & install instructions.

## 🙏 Acknowledgements

- FastAPI community
- SQLAlchemy & Alembic
- All contributors who will help build this clinic management system

---

**Made with ❤️ for modern clinics.**
```