# Face Attendance System

This project provides a face recognition based attendance solution. The original version was a Tkinter desktop application. The repository now includes a simple FastAPI backend so it can be deployed as a web app.

## Features
- Manage users and students in a SQLite database
- Capture and store face embeddings
- Recognise faces from uploaded images
- Basic API endpoints for registration, login and student management

## Installation
```bash
# clone the repo
git clone https://github.com/Techsolutions2024/face-atendance.git
cd face-atendance

# install dependencies
pip install -r requirements.txt
```

## Running locally
### Desktop GUI
The legacy GUI can still be started with:
```bash
python main.py
```

### FastAPI server
To run the API server locally:
```bash
uvicorn api.index:app --reload
```
It exposes endpoints such as `/register`, `/login`, `/students` and `/recognize`.

## Deploying to Vercel
A `vercel.json` file is included so the FastAPI app can be deployed as a serverless function on Vercel. After installing the [Vercel CLI](https://vercel.com/docs/cli), run:
```bash
vercel --prod
```

## Folder structure
```
face-atendance/
├── api/            # FastAPI backend
├── main.py         # Legacy Tkinter application
├── requirements.txt
└── vercel.json
```
