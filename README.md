# QuickQ

QuickQ is a lightweight web-based queue management system that allows users to create, join, and manage virtual queues instantly using queue codes and QR codes—without requiring registration.

## Features

* Instant queue creation
* Unique queue codes for sharing
* Automatic QR code generation
* Join queues using queue codes or QR codes
* Real-time queue management
* Queue status tracking
* Mobile-responsive design
* Anonymous participation (no sign-up required)
* Duplicate join prevention from the same browser

## Tech Stack

### Backend

* Python
* Flask

### Database

* MySQL (Aiven Cloud)

### Frontend

* HTML
* CSS
* JavaScript

### Deployment

* Render

## How It Works

### Creating a Queue

1. Open QuickQ.
2. Click **Create Queue**.
3. Enter a queue name.
4. Receive:

   * Queue Code
   * Admin Token
   * QR Code

### Joining a Queue

1. Open **Join Queue**.
2. Enter the queue code or upload the QR code image.
3. Enter a nickname.
4. Receive a token number.
5. Take a screenshot of the token number for confirmation

### Managing a Queue

1. Open **Manage Queue**.
2. Enter the Admin Token.
3. View queue members.
4. Click **Next** to serve the next person in line.

## Use Cases

* College events
* Food stalls and canteens
* Waiting rooms
* Workshops and seminars
* Fun games and competitions
* Service counters

## Project Structure

```text
QuickQ/
│
├── static/
│   ├── style.css
│   └── images/
│
├── templates/
│   ├── home.html
│   ├── createQ.html
│   ├── joinQ.html
│   ├── manageQ.html
│   ├── Qcreated.html
│   └── Qjoined.html
│
├── app.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_LINK
```

2. Navigate to the project directory:

```bash
cd QuickQ
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your MySQL database.

5. Run the application:

```bash
python app.py
```

6. Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Live Demo

Live Website: https://quickq-kmnn.onrender.com

## Future Improvements

* Live queue updates without page refresh
* QR code camera scanning
* Estimated waiting time prediction
* Multi-admin support
* Queue analytics dashboard

## Author

Bashita
