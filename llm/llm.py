from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()

# Initialize the model
from transformers import pipeline
llm = pipeline(
    "text-generation",
    model="EleutherAI/gpt-neo-125M",
    device=-1  # Use -1 for CPU or 0 for GPU
)

# Define request model
class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 100

@app.post("/generate/")
def generate(request: GenerationRequest):
    try:
        result = llm(request.prompt, max_length=request.max_length, num_return_sequences=1)
        return {"generated_text": result[0]["generated_text"]}
    except Exception as e:
        return {"error": str(e)}