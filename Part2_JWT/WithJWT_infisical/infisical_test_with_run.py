# main.py
import os

api_key = os.getenv("JWT_TOKEN")
if api_key:
    print(f"성공: Infisical에서 API 키를 가져왔습니다: {api_key[:4]}****")
else:
    print("실패: JWT_TOKEN 환경 변수를 찾을 수 없습니다.")
