# Attendify – Smart Student Attendance Management System

**Attendify** is a web-based student attendance management system built with Flask and SQLite. It provides a centralized platform for managing university accounts, courses, student enrolments, and attendance records.

The system simplifies attendance tracking by allowing lecturers to record student attendance, administrators to manage academic records, and students to monitor their attendance performance through personalized dashboards.

## Features

### Authentication & User Management
- Secure login with password hashing.
- Role-based access for administrators, lecturers, and students.
- Administrator-controlled account creation.
- Account management, including deletion.
- Protected dashboards based on user roles.

### Administrator Dashboard
- Create and manage student, lecturer, and administrator accounts.
- Register courses and assign lecturers.
- Enroll students into courses.
- Search registered accounts and courses.
- Delete accounts and courses.
- View system statistics and academic records.

### Lecturer Dashboard
- View assigned courses.
- View enrolled students.
- Record and manage daily attendance.
- Search students when marking attendance.
- Generate course attendance reports.
- Export attendance reports to CSV.

### Student Dashboard
- View enrolled courses.
- Monitor attendance percentages.
- Review individual attendance records.
- Track attendance status against the required threshold.
- View projected attendance performance and risk indicators.

### Attendance Analytics
- Automatic attendance percentage calculation.
- Attendance threshold monitoring.
- Attendance status classification.
- Projected end-of-semester attendance.
- Risk indicators to help identify students who may fall below the required attendance threshold.

## Technology Stack

| Component          | Technology                                |
|--------------------|-------------------------------------------|
| Backend            | Python, Flask                             |
| Frontend           | HTML5, CSS3, JavaScript                   |
| UI Framework       | Bootstrap 5                               |
| Icons              | Bootstrap Icons                           |
| Database           | SQLite                                    |
| Authentication     | Flask Sessions, Werkzeug Password Hashing |
| Data Visualization | Chart.js                                  |
| Report Export      | CSV                                       |

## System Architecture

Attendify follows a modular Flask application structure, separating authentication, database operations, administration, lecturer functionality, student functionality, and analytics.

```text
Attendify/
│
├── app/
│   ├── auth/
│   │   ├── routes.py
│   │   └── decorators.py
│   │
│   ├── admin/
│   │   └── routes.py
│   │
│   ├── lecturer/
│   │   └── routes.py
│   │
│   ├── student/
│   │   └── routes.py
│   │
│   ├── database/
│   │   └── db.py
│   │
│   ├── services/
│   │   └── analytics.py
│   │
│   ├── templates/
│   └── static/
│       ├── css/
│       └── js/
│
├── instance/
│   └── attendance.db
│
├── run.py
├── requirements.txt
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.12 or later
- Git

### 1. Clone the Repository

```bash
 git clone https://github.com/harizonelopez/Attendify.git
```

```bash
 cd Attendify
```

### 2. Create a Virtual Environment

```bash
 python -m venv .env
```

### 3. Activate the Environment

**Windows – Git Bash**

```bash
 source .env/Scripts/activate
```

**Windows – PowerShell**

```powershell
 ./.env/Scripts/Activate
```

### 4. Install Dependencies

```bash
 pip install -r requirements.txt
```

### 5. Run the Application

```bash
 flask run
```

Open your browser and navigate to:

```text
 http://127.0.0.1:5000
```

## User Roles

| Role          | Responsibilities                                                 |
|---------------|------------------------------------------------------------------|
| Administrator | Manages accounts, courses, and student enrolments.               |
| Lecturer      | Manages assigned courses and records student attendance.         |
| Student       | Monitors attendance records and academic attendance performance. |

All accounts are created and managed by the **administrator**. There is no public registration.

## Attendance Calculation

The system uses a configurable attendance threshold to determine whether a student is maintaining the required attendance level.

Projected attendance and risk indicators provide additional insight into a student's potential end-of-semester performance. These are statistical estimates rather than machine-learning predictions.

## Security Considerations

- Passwords are stored as secure hashes.
- Role-based access restrictions protect application routes.
- Database operations use parameterized SQL queries.
- Session-based authentication protects user dashboards.
- Administrative actions are restricted to authorized users.

For production deployment, configure a strong secret key, enable CSRF protection, and use a production-ready database and server configuration.

## Future Improvements

- Integration with machine-learning-based attendance risk prediction.
- Automated attendance notifications.
- More advanced analytics and reporting.
- Integration with institutional student information systems.
- Improved audit logs and administrative activity tracking.
- Deployment with a production database.

## Project Purpose

Attendify was developed as a practical software engineering project to demonstrate backend development, database management, authentication, role-based authorization, reporting, and data-driven application functionality.

## Author

**Harison Onyango**

- LinkedIn: [Harison Onyango](https://www.linkedin.com/in/harison-onyango-a267b625b/)

---

*Attendify – Simplifying University Attendance Management.*