# Hospital Equipment Maintenance Management and Reminder System

## Description

This project is a web-based system designed to manage hospital equipment maintenance schedules and send reminders for upcoming maintenance tasks. It provides a way to track equipment, schedule preventive maintenance (PPM), and handle occasional corrective maintenance (OCM). The system is built using Python with the Flask framework.

## Features

*   **Equipment Tracking:**
    *   Add, edit, and delete equipment records.
    *   Support for both Preventive Maintenance (PPM) and Occasional Corrective Maintenance (OCM).
*   **Maintenance Scheduling:**
    *   Define quarterly maintenance schedules for each piece of equipment.
    *   Specify dates and assigned engineers for each maintenance task.
*   **Bulk Import:**
    *   Import equipment and maintenance data from CSV files.
    *   Robust validation of data during import.
    *   Skip duplicated records, showing warnings.
*   **Export:**
    *   Export all PPM data to a CSV file.
*   **Email Reminders:**
    *   Send email reminders for upcoming PPM tasks.
    *   Configurable reminder period (default: 60 days).
*   **Data Storage:**
    *   Data is stored in JSON files (`ppm.json`, `ocm.json`).
* **PPM/OCM data**:
    * PPM data has information about the equipement and it has 4 quarters, with a date and an engineer.
    * OCM data has information about the equipement and it has the OCM for this year and next year and the name of the engineer.

## Technical Stack

## Dependencies

*   Python 3.11+
*   Flask: Web framework
*   Pydantic: Data validation and settings management
*   Pandas: Data manipulation (for CSV handling)
*   Schedule: Task scheduling
*   Python-dotenv: Environment variable management
*   APScheduler: Advanced task scheduling
* email-validator
* Flask-wtf

## Setup Instructions

1.  **Clone the Repository:** First, you need to clone the project repository to your local machine. Open your terminal or command prompt and use the following command, replacing `<repository_url>` with the actual URL of your repository: `git clone <repository_url>`. After cloning, navigate to the project directory using `cd hospital-equipment-maintenance`.
2.  **Install Poetry:** Make sure you have Poetry installed. Poetry is a tool for dependency management and packaging in Python. If you do not have it, run the following command: `curl -sSL https://install.python-poetry.org | python3 -`.
3.  **Install Dependencies:** Once you are in the project directory, install the required dependencies using Poetry. Run the command `poetry install`. This will install all the necessary Python libraries specified in the `pyproject.toml` file. This will create a virtual environment.
4.  **Activate the Virtual Environment:** After the dependencies are installed, you need to activate the virtual environment. Run the command `poetry shell`. This will activate the virtual environment created by poetry.
5. **Run the App**: With the virtual environment activated, you can now start the Flask development server. To do so, run the command `flask --app app run --debug`.
6.  **Access the Application:** Once the server is running, open your web browser and go to `http://127.0.0.1:5000/` or the address provided by the server.

**Explanation of the steps:**

1.  **Clone the Repository:** This step gets a copy of the project's code onto your computer. The `git clone` command downloads the code, and `cd` changes your current directory to the project's folder.
2.  **Install Poetry:** This step is important to manage the dependencies. It ensures that the correct tools are installed.
3.  **Install Dependencies:** This step uses Poetry to read the `pyproject.toml` file and install all the necessary libraries that the project needs to run. It also creates a virtual environment.
4.  **Activate the Virtual Environment:** This step activates the virtual environment created by Poetry, so the dependencies installed are available for the project.
5. **Run the App:** This step starts the Flask application using the `flask` command, making the app accessible in a web browser. the `--debug` is optional.
6. **Access the application:** This step tells how to access the application once it is running.


