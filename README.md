Concert Ticketing README

A high-performance, concurrency-safe Concert Ticket Reservation System built with Django Rest Framework (DRF). This system allows organizers to manage shows and categories while providing a seamless, reliable booking experience for customers.

🚀 Features





Role-Based Access Control: Distinct roles for Admins, Staff, and Customers.



Concurrency Safety: Uses database transactions and select_for_update() to prevent overbooking.



Dynamic Ticketing: Automated unique QR-ready ticket code generation.



Secure Calculations: Decimal-based price handling for financial accuracy.



RESTful API: Clean, intuitive endpoints for managing Shows, Categories, and Bookings.



🏗️ Architecture Overview

graph TD
    User[Customer/Staff] --> API[DRF API ViewSet]
    API --> Booking[Booking Logic]
    Booking --> Show[Show Info]
    Booking --> Cat[Category - Price/Stock]
    Booking --> Ticket[Ticket Generation]
    
    subgraph "Database Layer (Atomic Transactions)"
    Cat
    Ticket
    Booking
    end




🛠️ Data Model Relationships

The system is designed for high data integrity:

ModelPurposeCoreUserManages user profiles, roles, and authentication.ShowRepresents the event (location, title, description).CategoryDefines pricing tiers and manages inventory (stock).BookingLinks users to shows; calculates total transaction cost.TicketIndividual seat reservation with unique tracking codes.



⚡ Key Technical Implementation

1. Stock Management

To ensure zero overbooking, the system employs pessimistic locking:





select_for_update() locks the category record during the booking process.



An atomic transaction ensures that stock reduction and ticket creation succeed or fail together.

2. Price Handling

Financial values are stored as CharField in the database, but processed as Decimal in the application logic to ensure precision and prevent floating-point errors.

3. Ticket Generation

Tickets are automatically generated upon confirmed booking.





Code Format: YY-MM-DD-SeatNumber



Example: 26-05-24-1



📦 Setup Instructions





Clone the repository:

git clone https://github.com/yourusername/concert-ticketing-system.git




Install dependencies:

pip install -r requirements.txt




Run migrations:

python manage.py migrate




Start the server:

python manage.py runserver




🛡️ API Security

Access is strictly managed via Custom Permission Classes mapping to RoleType:





Admin/Staff: Have full read/write access.



Customers: Limited to viewing events and managing their own bookings.



Built with Django Rest Framework, Python 3.11+
