# 6-1. 안전한 API 키 관리 전략 실습

import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 코드는 개발 환경에서 .env 파일을 쉽게 사용하기 위함입니다.
# 프로덕션 환경에서는 Docker Secrets, AWS Secrets Manager, HashiCorp Vault 같은
# 전문적인 시크릿 관리 도구를 사용하는 것이 좋습니다.
load_dotenv()

# os.getenv를 사용하여 환경 변수에서 API 키를 읽어옵니다.
# 코드에 직접 키를 하드코딩하는 것보다 훨씬 안전합니다.
api_key = os.getenv("MY_API_KEY")

if api_key:
    print(f"성공적으로 API 키를 로드했습니다. (마지막 4자리: ...{api_key[-4:]})")
else:
    print("MY_API_KEY 환경 변수를 찾을 수 없습니다.")
    print(".env.example 파일을 복사하여 .env 파일을 만들고, 그 안에 키를 설정해주세요.")

# 이 키를 사용하여 외부 서비스에 요청을 보낼 수 있습니다.
def call_external_service():
    if not api_key:
        print("API 키가 없어 외부 서비스를 호출할 수 없습니다.")
        return

    print("\n외부 서비스에 API 요청을 보냅니다...")
    # 예: requests.get("https://api.example.com/data", headers={"Authorization": f"Bearer {api_key}"})
    print("요청 성공!")

call_external_service()
