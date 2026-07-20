import os
import subprocess
import glob
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình trực tiếp bằng GEMINI_API_KEY
API_KEY = os.environ.get("AQ.Ab8RN6IMO4qxgHO91Q6A67A6eITidyL5lBvInwM7nhV23YB_eg")
genai.configure(api_key=API_KEY)

class MathRequest(BaseModel):
    prompt: str

@app.post("/generate-math-video/")
async def generate_math_video(request: MathRequest):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            f"Hãy viết MỘT ĐOẠN CODE PYTHON SỬ DỤNG MANIM hoàn chỉnh để giải bài toán sau. "
            f"Chỉ trả về code Python trong khối ```python ... ```, không giải thích: {request.prompt}"
        )
        
        code_text = response.text
        if "```python" in code_text:
            code = code_text.split("```python")[1].split("```")[0].strip()
        elif "```" in code_text:
            code = code_text.split("```")[1].split("```")[0].strip()
        else:
            code = code_text.strip()

        file_name = "math_scene.py"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(code)

        class_match = re.search(r'class\s+(\w+)\s*\(', code)
        scene_name = class_match.group(1) if class_match else "MathScene"

        cmd = f"manim -pql {file_name} {scene_name}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Lỗi Manim: {process.stderr}")

        video_files = glob.glob(f"media/videos/**/{scene_name}.mp4", recursive=True)
        if not video_files:
            raise HTTPException(status_code=500, detail="Không tìm thấy file video.")

        latest_video = max(video_files, key=os.path.getctime)
        return FileResponse(latest_video, media_type="video/mp4", filename="math_solution.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "KateMathAI Backend đang chạy với Gemini Key chuẩn!"}
