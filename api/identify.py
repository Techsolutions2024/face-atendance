from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import onnxruntime as ort
import os

app = FastAPI()

MODEL_PATH = os.getenv("MODEL_PATH", "model.onnx")
EMBEDDINGS_PATH = os.getenv("EMBEDDINGS_PATH", "embeddings.npy")
IDS_PATH = os.getenv("IDS_PATH", "user_ids.npy")

# Load model and embeddings at startup
try:
    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    known_embeddings = np.load(EMBEDDINGS_PATH)
    user_ids = np.load(IDS_PATH)
except Exception as e:
    session = None
    known_embeddings = None
    user_ids = None

class Embedding(BaseModel):
    vector: list[float]

@app.post("/identify")
def identify(data: Embedding):
    if session is None or known_embeddings is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    emb = np.array(data.vector, dtype=np.float32)
    if emb.shape[0] != known_embeddings.shape[1]:
        raise HTTPException(status_code=400, detail="Invalid embedding size")

    norms = np.linalg.norm(known_embeddings, axis=1) * np.linalg.norm(emb)
    sims = known_embeddings @ emb / norms
    idx = int(np.argmax(sims))
    if sims[idx] < 0.6:
        raise HTTPException(status_code=404, detail="No match")
    return {"user_id": str(user_ids[idx]), "score": float(sims[idx])}
