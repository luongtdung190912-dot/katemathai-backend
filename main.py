import os
import subprocess
import glob
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

# Cấu hình CORS để web frontend gọi được vào backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo client Gemini mới nhất (tự động nhận diện mã AQ... từ biến môi trường GOOGLE_API_KEY)
client = genai.Client()

class MathRequest(BaseModel):
    prompt: str

@app.post("/generate-math-video/")
async def generate_math_video(request: MathRequest):
    try:
        # Prompt hệ thống ép Gemini viết code Manim chuẩn xác
        system_instruction = (
            "Bạn là một chuyên gia toán học và lập trình Manim Python. "
            "Hãy viết MỘT ĐOẠN CODE PYTHON SỬ DỤNG MANIM hoàn chỉnh để giải và vẽ hình minh họa cho đề bài toán sau. "
            "Chỉ trả về đoạn code Python thuần túy nằm trong khối code ```python ... ```, không giải thích gì thêm."
        )

        # Gọi Gemini sử dụng chuẩn client.models.generate_content mới nhất
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )
        
        ai_response_text = response.text

        # Lọc lấy đoạn code Python từ phản hồi của AI
        if "```python" in ai_response_text:
            code = ai_response_text.split("```python")[1].split("```")[0].strip()
        elif "```" in ai_response_text:
            code = ai_response_text.split("```")[1].split("```")[0].strip()
        else:
            code = ai_response_text.strip()

        # Lưu code vào file .py tạm thời
        file_name = "math_scene.py"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(code)

        # Chạy lệnh Manim để render video (chất lượng 480p cho render nhanh)
        # Lấy tên Class đầu tiên trong code để render đúng scene
        import re
        class_match = re.search(r'class\s+(\w+)\s*\(', code)
        scene_name = class_match.group(1) if class_match else "MathScene"

        cmd = f"manim -pql {file_name} {scene_name}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Lỗi chạy Manim: {process.stderr}")

        # Tìm file video mp4 vừa được render ra
        video_files = glob.glob(f"media/videos/**/{scene_name}.mp4", recursive=True)
        if not video_files:
            raise HTTPException(status_code=500, detail="Không tìm thấy file video đầu ra từ Manim.")

        latest_video = max(video_files, key=os.path.getctime)
        return FileResponse(latest_video, media_type="video/mp4", filename="math_solution.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "KateMathAI Backend đang chạy mượt mà với chuẩn Gemini mới nhất!"}
