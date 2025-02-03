import httpx

BASE_URL = "https://shark-app-6wiyn.ondigitalocean.app/api/v1"
LOGIN_ENDPOINT = f"{BASE_URL}/auth/login"
TASK_ENDPOINT = f"{BASE_URL}/tasks/{{id}}"

LOGIN_PAYLOAD = {"email": "newAI@gmail.com", "password": "@test#123"}


async def fetch_task_by_id(task_id: int) -> dict:
    """
    Logs in to get the token and fetches the task details by ID.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: Login and get the token
        login_response = await client.post(LOGIN_ENDPOINT, json=LOGIN_PAYLOAD)
        if login_response.status_code != 201:
            raise ValueError(
                f"Login failed: {login_response.status_code} {login_response.text}"
            )

        token = login_response.json().get("token")
        if not token:
            raise ValueError("Token not found in login response.")

        # Step 2: Fetch task details using the token
        headers = {"Authorization": f"Bearer {token}"}
        task_response = await client.get(
            TASK_ENDPOINT.format(id=task_id), headers=headers
        )
        if task_response.status_code != 200:
            raise ValueError(
                f"Failed to fetch task: {task_response.status_code} {task_response.text}"
            )

        # Step 3: Return the task details
        return task_response.json()
