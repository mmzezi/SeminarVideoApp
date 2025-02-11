# Video processor API

Enostaven Web frontend za FFMPEG, ki za delovanje uporablja Flask in SQLAlchemy. Omogoča kodiranje videa v X265, nižanje resolucije, odstranitev metapodatkov, spremembo CRF ali pa bitne hitrosti. Dodatna funkcionalnost YT-DLP in mobilna aplikacija (s pomočjo WebView).

![alt text](https://files.catbox.moe/pqvqav.jpg)


## Uporaba
```bash
docker build -t videoprocessor .
```

```bash
docker run -d -p 5000:5000 videoprocessor
```

Do vmesnika se dostopa na 127.0.0.1:5000 (localhost).



# Video Processor API Documentation
<details>


## Authentication

### 1. Set Username
**Endpoint:**  
`POST /set_username`

**Description:**  
Nastavi uporabniško ime.

**Request:**
- **Headers:**  
  - `Content-Type: application/json`
- **Body:**
  ```json
  {
    "username": "exampleUser"
  }



**Response:**

-   **200 OK – Username set successfully.**
    
    ```json
    {
      "message": "Welcome, exampleUser!"
    }
    
    ```
    
-   **400 Bad Request – Username is missing.**
    
    ```json
    {
      "error": "Username is required"
    }
    
    ```
    

----------

## Video Upload and Processing

### 2. Upload Video

**Endpoint:**  
`POST /upload`

**Description:**  
Naloži video na strežnik.

**Request:**

-   **Headers:**
    -   `Content-Type: multipart/form-data`
-   **Body:**
    -   `file`: Video, ki ga nalagamo.

**Response:**

-   **200 OK – Upload successful.**
    
    ```json
    {
      "video_id": "12345",
      "message": "Upload successful!"
    }
    
    ```
    
-   **403 Forbidden – User is not logged in.**
    
    ```json
    {
      "error": "You must be logged in to upload videos"
    }
    
    ```
    
-   **400 Bad Request – No file uploaded.**
    
    ```json
    {
      "error": "No file provided"
    }
    
    ```
    

----------

### 3. Process Video

**Endpoint:**  
`POST /process/<video_id>`

**Description:**  
Procesira video z izbranimi opcijami.

**Request:**

-   **Headers:**
    -   `Content-Type: application/json`
-   **Body:**
    
    ```json
    {
      "codec": "libx265",
      "resolution": "-2:720",
      "volume": 5,
      "bitrate": 1000,
      "crf": 28,
      "strip_metadata": true
    }
    
    ```
    

**Response:**

-   **200 OK – Processing started successfully.**
    
    ```json
    {
      "message": "Processing started!",
      "download_link": "/download/12345"
    }
    
    ```
    
-   **400 Bad Request – Invalid parameters or missing video.**
    
    ```json
    {
      "error": "Invalid processing options"
    }
    
    ```
    

----------

### 4. Download Processed Video

**Endpoint:**  
`GET /download/<video_id>`

**Description:**  
Omogoči nalaganje procesiranega videa.

**Response:**

-   If successful, returns the processed video file for download.
-   **404 Not Found – Video ID does not exist.**

----------

## YouTube Download

### 5. Download from YouTube

**Endpoint:**  
`POST /youtube_download`

**Description:**  
Naloži video ali audio iz YouTube-a.

**Request:**

-   **Headers:**
    -   `Content-Type: application/json`
-   **Body:**
    
    ```json
    {
      "url": "https://www.youtube.com/watch?v=example",
      "format": "video"
    }
    
    ```
    

**Response:**

-   **200 OK – Download link ready.**
    
    ```json
    {
      "download_link": "/downloads/example.mp4"
    }
    
    ```
    
-   **400 Bad Request – Invalid YouTube URL.**
    
    ```json
    {
      "error": "Invalid URL"
    }
    
    ```
    

----------

## User Authentication & Session

### 6. Login

**Endpoint:**  
`POST /login`

**Description:**  
Prijavi uporabnika z uporabniškim imenom.

**Request:**

-   **Headers:**
    -   `Content-Type: application/x-www-form-urlencoded`
-   **Body:**
    
    ```
    username=exampleUser
    
    ```
    

**Response:**

-   **302 Found** – Redirects to the main page if successful.

----------

### 7. Logout

**Endpoint:**  
`GET /logout`

**Description:**  
Odjavi uporabnika, počisti sejo.

**Response:**

-   **302 Found** – Redirects to the login page.
</details>

