
# 🎫 Concert Ticket Reservation System

A robust and scalable concert ticket reservation system built with **Django Rest Framework (DRF)**.

---

## 🚀 Key Features
- **Custom User Management:** Advanced authentication system with role-based access control (Customer, Staff, Admin).
- **Booking Workflow:** Secure and transactional reservation process.
- **Stock Management:** Built-in `atomic transaction` and `select_for_update` logic to prevent race conditions and overbooking.
- **Financial Integrity:** Automated price calculation system ensuring accurate summation.
- **Ticket Generation:** Automated unique ticket code generation based on booking dates and seat numbers.

---

## 🛠 Tech Stack
- **Backend:** Python, Django, Django Rest Framework
- **Database:** PostgreSQL (Recommended)
- **Authentication:** Custom User Model with Role-based Permissions
- **Transactions:** `select_for_update` for concurrency control

---

## 🏗 System Architecture
The system is built around four core modules:
1. **CoreUser:** Manages user profiles, authentication, and custom roles.
2. **Show:** Handles event venues and show details.
3. **Category:** Defines ticket tiers, pricing, and manages stock levels.
4. **Booking & Ticket:** Manages the reservation lifecycle and final ticket issuance.

---

## 🛡 Permissions
The system utilizes custom DRF permissions for fine-grained access control:
- `IsAdminRole`: Grants full administrative access.
- `IsStaffOrAdminRole`: Grants authorized access to staff members for operational management.

---

## 📥 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/melikatavakoli/backend-DRF-event-booking-api.git
   ```
2. Setup virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## 💡 Technical Notes
- **Concurrency:** To prevent race conditions, stock deduction and booking operations are wrapped in `transaction.atomic()` with `select_for_update()` locked on the category object.
- **Data Handling:** While some fields use `CharField` per project requirements, all business logic and financial calculations are strictly cast to `Decimal` or `int` to ensure data integrity and accuracy.

---

## 📝 License
Distributed under the [MIT License](LICENSE).

