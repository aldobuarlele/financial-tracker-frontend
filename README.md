# 📊 Family Financial Tracker - Web Client

A modern, responsive web interface for the Family Financial Tracker system. Built with **Python Flask**, this client consumes the Backend API to provide an interactive financial management experience.

## 🌟 Application Highlights

* **📈 Interactive Dashboard:**
    * Real-time financial overview with dynamic **Dual-Charts** (Income vs. Expense Pie Charts).
    * **Net Cash Flow Indicator:** Instantly visualize surplus or deficit status.
    * **Global Search:** Filter transaction history by keyword, date, or category instantly.

* **📅 Smart Calendar:**
    * Integrated **FullCalendar.js** to visualize daily spending habits.
    * Interactive events: Click on any date to view, edit, or delete specific transactions via a modal popup.

* **📑 Comprehensive Reporting:**
    * **Advanced Statistics:** Detailed breakdown of spending per category and wallet distribution.
    * **Export Options:**
        * 📥 **Download CSV:** Export raw data for Excel/Google Sheets analysis.
        * 🖨️ **Print/PDF:** Printer-friendly layout for generating professional monthly reports.

* **🔄 Fund Management:**
    * Intuitive UI for recording Income, Expenses, and **Wallet-to-Wallet Transfers**.

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Framework:** Flask (Jinja2 Templating)
* **Styling:** Bootstrap 5 (Responsive & Mobile-ready)
* **Visualization:** Chart.js, FullCalendar
* **Integration:** REST API Consumption (via Python `requests`)

## ⚙️ Installation & Usage

### 1. Prerequisites
Ensure the Backend API is running on port `8080`.

### 2. Install Dependencies
```bash
pip install flask requests