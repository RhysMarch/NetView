# NetView

<p align="center">
  <img src="assets/NetView.gif" alt="NetView Demo" />
</p>

**NetView** is an intuitive, user-friendly network monitoring tool that discovers devices on your LAN and displays real-time statistics. Built in Python with a clean Nuxt interface.

---

## 🚀 Features

- **Network Discovery** – Scans local subnet for active hosts (ARP, ICMP).  
- **Device Details** – Displays IP, MAC, hostname, OS guess.  
- **Real-Time Updates** – Live refresh of device status & traffic stats.  
- **Export Data** – Download Alerts History via a Text file.

---

## 🖥️ Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/RhysMarch/NetView.git
   cd NetView
   
2. **Create a virtual environment and install requirements**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
   
3. **Run the backend**
    ```bash
    uvicorn backend.app.main:app --reload
    ```

4. **Run the frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```