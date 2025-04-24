# ⛽ ICONICA – Online clothing store

ICONICA is a full-stack web application that allows users to browse, purchase, and review clothing items. It also provides an admin interface to manage products, users, and orders efficiently

---

## 🧠 Project Overview

This system provides a simple and interactive shopping experience for users to:
- Register and log in
- Browse products by category
- Add items to their cart
- Select size and quantity
- Place and view orders
- Submit product reviews

Admins can:
- Add, edit, or delete clothing items
- Manage product categories (cloth types)
- Update size-based stock
- View and manage all orders and users

---

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (Jinja templating)
- **Tools**: PyCharm, Postman, GitHub

---

## 📋 Features

### 👤 Customer
- User registration & login
- Product browsing with filters
- Add to cart and select size
- Place orders and view order history
- Submit reviews with ratings

### 🧑‍💼 Admin
- Admin login and dashboard
- Manage products (add/edit/delete)
- Set and update stock by size
- View all users and orders
- Handle product categories

---

## 🖼️ Screenshots

| User Homepage Page | Admin Dashboard |
|-------------------|------------------|
| ![Homepage](file:///Users/nhupham/Desktop/Screenshot%202025-04-24%20at%203.57.26%E2%80%AFPM.png) | ![Admin](file:///Users/nhupham/Desktop/Screenshot%202025-04-24%20at%203.52.20%E2%80%AFPM.png) |


---

## 🚀 How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/Nhupham0934/group8project
   cd group8project
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Visit [http://localhost:5001](http://localhost:5001) in your browser.

---

## 🗃️ Folder Structure

```
ICONICA/
├── app.py
├── templates/
│   ├── user/
│   └── admin/
├── models/
├── static/
├── instance/
│   └── db.sqlite
├── requirements.txt
└── README.md
```

---

## 📆 Developed With SDLC

We followed the Software Development Life Cycle (SDLC) for this project:

Planning: Defined features and user roles
Requirements: Functional + UI goals
Feasibility: Chose tools suitable for local development
Design: Sketched frontend and database structure
Development: Built backend + frontend integration
Testing: Used Postman and manual browser tests
Launch: Ran the app locally with full feature walkthrough

---

## 👤 Author

- **Name**: Nhu Pham
- **Course**: University of North Texas
- **Date**: [04/24/2001]

---

## 📜 License

This project is for educational purposes only.
