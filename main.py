import os, re, subprocess, uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# KHẮC PHỤC LỖI CORS: Mở khóa toàn diện cho phép GitHub Pages truy cập và đọc file video
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Cho phép mọi nguồn (bao gồm github.io của bạn) gọi vào
    allow_credentials=False,
    allow_methods=["*"],          # Cho phép mọi phương thức (POST, GET...)
    allow_headers=["*"],          # Cho phép mọi loại Header dữ liệu gửi lên
    expose_headers=["*"]          # BẮT BUỘC: Cho phép trình duyệt nhìn thấy và tải file video về
)

# Cấu hình khóa API Key của bạn
genai.configure(api_key="AQ.Ab8RN6I5ZNXCs7M8vGHn9AsEg3bPcZ--O7-FgJzem-9waigNgQ")

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
        if not code_match: raise HTTPException(status_code=500, detail="Lỗi tạo mã")
        
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(code_match.group(1).strip())
            
        cmd = f"manim -ql --media_dir {video_output_dir} {script_filename} MathSolution"
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        generated_video_path = f"{video_output_dir}/videos/scene_{session_id}/480p15/MathSolution.mp4"
        
        if os.path.exists(generated_video_path):
            if os.path.exists(script_filename): os.remove(script_filename)
            return FileResponse(generated_video_path, media_type="video/mp4")
        else:
            raise HTTPException(status_code=500, detail="Lỗi làm video")
    except Exception as e:
        if os.path.exists(script_filename): os.remove(script_filename)
        raise HTTPException(status_code=500, detail=str(e))
