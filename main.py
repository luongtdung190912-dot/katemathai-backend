import os
import re
import subprocess
import uuid
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Mở CORS toàn diện cho phép web gọi API và nhận video
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Cấu hình Gemini đọc trực tiếp từ biến môi trường trên Render
genai.configure(api_key=os.environ.get("AQ.Ab8RN6IMO4qxgHO91Q6A67A6eITidyL5lBvInwM7nhV23YB_eg"))

SYSTEM_PROMPT = "Bạn là lõi AI của 'KateMathAI'. Hãy nhận đề bài toán cấp 3 và TỰ ĐỘNG VIẾT CODE MANIM (PYTHON) để tạo video minh họa. Đặt tên Class chính là `MathSolution`, kế thừa từ `Scene`. CHỈ TRẢ VỀ ĐOẠN CODE PYTHON TRONG KHỐI MÃ ```python ... ```."

class MathRequest(BaseModel):
    prompt: str

@app.post("/generate-math-video/")
async def generate_video(request: MathRequest):
    session_id = str(uuid.uuid4())[:8]
    script_filename = f"/tmp/scene_{session_id}.py"
    video_output_dir = f"/tmp/media_{session_id}"
    
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
        response = model.generate_content(request.prompt)
        
        code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
        if not code_match:
            raise HTTPException(status_code=500, detail="Lỗi tạo mã từ AI")
        
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(code_match.group(1).strip())
            
        cmd = f"manim -ql --media_dir {video_output_dir} {script_filename} MathSolution"
        process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_output = process.stderr.decode("utf-8", errors="ignore")
            print(f"Manim Error: {error_output}")
            raise HTTPException(status_code=500, detail=f"Lỗi Manim: {error_output[-300:]}")
        
        generated_video_path = f"{video_output_dir}/videos/scene_{session_id}/480p15/MathSolution.mp4"
        
        if os.path.exists(generated_video_path):
            if os.path.exists(script_filename):
                os.remove(script_filename)
            return FileResponse(generated_video_path, media_type="video/mp4")
        else:
            raise HTTPException(status_code=500, detail="Không tìm thấy file video xuất ra")
            
    except Exception as e:
        err_detail = traceback.format_exc()
        print("=== TRACEBACK ERROR ===")
        print(err_detail)
        if os.path.exists(script_filename):
            os.remove(script_filename)
        raise HTTPException(status_code=500, detail=str(e))
