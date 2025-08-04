# Application Usage and Installation

There are three ways to set up and run the application.

## Method 1: Using Installation Scripts (Recommended)

This is the easiest way to get the application running. The scripts will check for dependencies and guide you through the setup process.

1.  **Prerequisites:**

    - Docker and Docker Compose

2.  **Run the script:**

    - **For Windows:**
      Open PowerShell and run:

      ```powershell
      ./scripts/install.ps1
      ```

    - **For Linux/macOS:**
      Open a terminal and run:
      ```bash
      chmod +x scripts/install.sh
      ./scripts/install.sh
      ```

    The script will start the application using Docker. The API will be available at `http://localhost:8000`.

## Method 2: Using Docker Manually

This method is for users who prefer to use Docker commands directly.

1.  **Prerequisites:**

    - Docker
    - Docker Compose

2.  **Build and start the containers:**

    Navigate to the `docker` directory and run:

    ```bash
    docker-compose up --build
    ```

    _Note: Depending on your Docker version, you might need to use `docker compose` (with a space) instead of `docker-compose`._

3.  The API will be available at `http://localhost:8000`. The Docker Compose setup will start the FastAPI application and a Redis container for session management.

## Method 3: Running Locally

If you prefer to run the application locally without Docker, you will need to have a Redis server installed and running on your machine.

1.  **Prerequisites:**

    - Python 3.11+
    - Redis Server (see the [official Redis documentation](https://redis.io/docs/getting-started/installation/) for installation instructions)

2.  **Installation:**

    1.  **Clone the repository:**

        ```bash
        git clone https://github.com/irfanvtf/alfred-bot.git
        cd alfred-bot
        ```

    2.  **Create a virtual environment and activate it:**

        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
        ```

    3.  **Install the dependencies:**

        ```bash
        pip install -r requirements.txt
        ```

    

    5.  **Set up the environment variables:**

        Create a `.env` file by copying the example file. This is recommended to ensure all required environment variables are present.
        ```bash
        cp .env.example .env
        ```
        After copying, open the `.env` file and ensure the variables match your local setup, especially `REDIS_HOST` and `REDIS_PORT` for your Redis server.

3.  **Running the Application:**

        To run the application, use the following command:

        ```bash
        uvicorn main:app --reload
        ```

        The API will be available at `http://localhost:8000`.

    No newline at end of file
