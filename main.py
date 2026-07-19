import os, re, subprocess, uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])

# DÒNG SỐ 13 CHÍNH LÀ ĐÂY NÈ BẠN:
genai.configure(api_key="AQ.Ab8RN6Ieo5ljjxA1uYtMGrNqqK_lkPFvGzqOcDA3LmJ56Hy6rA")

SYSTEM_PROMPT = "Bạn là lõi AI của 'KateMathAI'. Hãy nhận đề bài toán cấp 3 và TỰ ĐỘNG VIẾT CODE MANIM (PYTHON) để tạo video minh họa. Đặt tên Class chính là `MathSolution`, kế thừa từ `Scene`. CHỈ TRẢ VỀ ĐOẠN CODE PYTHON TRONG KHỐI MÃ ```python ... ```."

class MathRequest(BaseModel):
    prompt: str

@app.post("/generate-math-video/")
async def generate_video(request: MathRequest):
    session_id = str(uuid.uuid4())[:8]
    script_filename = f"scene_{session_id}.py"
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
        response = model.generate_content(request.prompt)
        code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
        if not code_match: raise HTTPException(status_code=500, detail="Lỗi tạo mã")
        
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(code_match.group(1).strip())
            
        video_output_dir = f"media_{session_id}"
        cmd = f"manim -ql --media_dir {video_output_dir} {script_filename} MathSolution"
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        generated_video_path = f"{video_output_dir}/videos/{script_filename[:-3]}/480p15/MathSolution.mp4"
        if os.path.exists(generated_video_path):
            if os.path.exists(script_filename): os.remove(script_filename)
            return FileResponse(generated_video_path, media_type="video/mp4")
        else:
            raise HTTPException(status_code=500, detail="Lỗi làm video")
    except Exception as e:
        if os.path.exists(script_filename): os.remove(script_filename)
        raise HTTPException(status_code=500, detail=str(e))
