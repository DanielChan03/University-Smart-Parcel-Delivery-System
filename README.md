# 📦 University Parcel Management System (UPMS)

## 📌 Overview

The University Parcel Management System (UPMS) is designed to facilitate efficient and reliable parcel handling between universities. The system integrates key functionalities such as real-time parcel tracking, sequenced parcel status updates, and smart locker management.

It allows:

- Parcel Managers to assign parcels, update statuses, and manage smart lockers  
- Couriers to handle inter-campus parcel transfers and delivery updates  
- Students and Staff to retrieve parcels and receive notifications  

The system improves transparency, reduces delays, and ensures smooth parcel operations across university campuses.

---

## ⚙️ Key Features

### 1. Parcel Management
Parcel Managers are responsible for:

- Assigning parcels  
- Organising parcel storage in smart lockers  
- Tracking parcel status updates  

---

### 2. Courier Operations
Couriers can:

- Manage inter-campus parcel transportation  
- Update parcel delivery status in real-time  

---

### 3. User Notifications & Locker Access
Students and Staff can:

- Receive parcel notifications  
- Collect parcels from smart lockers  

---

### 4. Real-Time Tracking (In Session)
- Continuous status updates ensure transparency and accuracy  
- Users can track parcel progress anytime  

---

## 🛠️ Installation Requirements

### ✔️ Python Requirement

Ensure Python is installed (version **3.8 or above recommended**)

Check version:

```bash
python3 --version
```

✔️ Install all the dependencies provided.
Install using environment.yml file:

```bash
conda env create -f environment.yml
```

## 🚀 How to Run the System
Follow these steps carefully:
1. Navigate to Project Directory
Open terminal and move into the project folder:

```bash
cd your-project-folder-name
```
2. Run the Application
Start the Flask server:

```bash
python main.py
```

3. Open in Browser
After running the server, open:

```bash
http://127.0.0.1:5000
```

## 👤 User Login Guide

1. 🧑‍🎓 Student / Staff
Go to homepage login
Enter your email and password directly

2. 📦 Parcel Manager Login

```bash
http://127.0.0.1:5000/parcel-manager/parcel-manager-login
```
3. 🚚 Courier Login

```bash
http://127.0.0.1:5000/courier/courier-login
```

4. 🛠️ Admin Login

```bash
http://127.0.0.1:5000/admin/admin-login
```

## 🔐 Default Login Credentials

| Role            | Email                        | Password        |
|-----------------|------------------------------|-----------------|
| Admin           | john.doe@gmail.com           | JohnDOE@12345   |
| Parcel Manager  | wentao.woon@trackiq.com      | password123     |
| Student / Staff | tan.weiling@mmu.edu.my       | password123     |
| Courier         | daniel.chan@trackiq.com      | password123     |


📁 Project Structure 

```bash
UPMS/
│
├── main.py
├── instance
├── webapp/
       ├── model_py_codes
       ├── templates/
       ├── static/
├── environment.yml
└── README.md
```

## 📌 Notes
Ensure Flask is installed before running the system.

Always run main.py from the project root directory.

Use correct login URLs for each role.
