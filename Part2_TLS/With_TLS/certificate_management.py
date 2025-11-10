#!/usr/bin/env python3
"""
===========================================
TLS 인증서 생성 및 관리 스크립트
===========================================

강의 목적:
이 파일은 HTTPS 서버에서 사용할 TLS 인증서를 생성하고 관리합니다.

학습 포인트:
1. PKI (Public Key Infrastructure) 개념
   - 공개 키 암호화 시스템의 기반 구조
   - 인증서, CA, 신뢰 체인

2. X.509 인증서 구조
   - Subject (소유자 정보)
   - Issuer (발급자 정보)
   - Public Key (공개 키)
   - Validity Period (유효 기간)
   - Signature (서명)

3. 자체 서명 인증서 vs CA 서명 인증서
   - Self-Signed: 자신이 자신을 서명 (개발/테스트용)
   - CA-Signed: 신뢰할 수 있는 CA가 서명 (프로덕션용)

4. 인증서 생성 프로세스
   - 1. 개인 키 생성 (Private Key)
   - 2. CSR 생성 (Certificate Signing Request)
   - 3. 인증서 발급 (Certificate)

5. mTLS (Mutual TLS)
   - 서버와 클라이언트 양쪽 인증
   - 클라이언트 인증서 필요

주요 파일:
- server.key: 서버 개인 키 (절대 공개 금지!)
- server.csr: 인증서 서명 요청
- server.crt: 서버 인증서 (공개 가능)
- client.key: 클라이언트 개인 키
- client.crt: 클라이언트 인증서

중요:
개인 키는 절대 공개하거나 Git에 커밋하면 안 됩니다!
.gitignore에 *.key, *.pem 추가 필수!

비교:
- HTTP: 암호화 없음, 인증서 불필요
- HTTPS: TLS 암호화, 인증서 필수
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import os                    # 파일 권한 설정
import sys                   # 시스템 종료
import subprocess            # OpenSSL 명령어 실행
from datetime import datetime, timedelta  # 인증서 유효기간 (사용 안 하지만 import됨)
from pathlib import Path     # 파일 경로 처리

# ===========================================
# CertificateManager 클래스
# ===========================================

class CertificateManager:
    """
    TLS 인증서 생성 및 관리 클래스

    역할:
    - 개인 키 (Private Key) 생성
    - 인증서 서명 요청 (CSR) 생성
    - 자체 서명 인증서 생성
    - 클라이언트 인증서 생성 (mTLS용)
    - 인증서 검증 및 정보 확인

    PKI 개념:
    - Public Key Infrastructure
    - 공개 키 기반 암호화 시스템
    - 인증서를 통한 신원 확인 및 암호화

    TLS 핸드셰이크에서 인증서의 역할:
    1. 서버가 클라이언트에게 인증서 전송
    2. 클라이언트가 인증서 검증 (CA 체인, 유효기간 등)
    3. 인증서의 공개 키로 대칭키 교환
    4. 대칭키로 데이터 암호화 통신
    """

    def __init__(self, cert_dir="./certs"):
        """
        인증서 관리자 초기화

        디렉토리 구조:
        ./certs/
          ├── server.key     # 서버 개인 키 (비밀!)
          ├── server.csr     # 인증서 서명 요청
          ├── server.crt     # 서버 인증서
          ├── client.key     # 클라이언트 개인 키 (옵션)
          └── client.crt     # 클라이언트 인증서 (옵션)

        보안 주의사항:
        - *.key 파일은 절대 공개 금지!
        - 파일 권한: 0o600 (소유자만 읽기/쓰기)
        - Git에 커밋하지 않도록 .gitignore 설정
        """
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)  # 디렉토리 생성 (이미 존재하면 무시)

        # 인증서 파일 경로 설정
        self.key_file = self.cert_dir / "server.key"    # RSA 개인 키
        self.cert_file = self.cert_dir / "server.crt"   # X.509 인증서
        self.csr_file = self.cert_dir / "server.csr"    # 인증서 서명 요청
        
    def check_openssl(self):
        """OpenSSL 설치 확인"""
        try:
            result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
            print(f"✅ OpenSSL 버전: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            print("❌ OpenSSL이 설치되지 않았습니다.")
            print("   Ubuntu/Debian: sudo apt-get install openssl")
            print("   macOS: brew install openssl")
            return False
            
    def generate_private_key(self, key_size=2048):
        """
        RSA 개인 키 생성

        RSA (Rivest-Shamir-Adleman):
        - 비대칭 암호화 알고리즘
        - 공개 키와 개인 키 쌍 생성
        - key_size: 키 길이 (2048, 3072, 4096 비트)

        보안 고려사항:
        - 2048비트: 현재 표준, 대부분의 용도에 충분
        - 3072비트: 높은 보안이 필요한 경우
        - 4096비트: 최고 보안, 성능 저하 있음

        OpenSSL 명령어:
        openssl genrsa -out server.key 2048

        생성되는 파일:
        - server.key: PEM 형식의 RSA 개인 키
        - 파일 권한: 0o600 (소유자만 읽기/쓰기)
        """
        print(f"\n🔑 RSA {key_size}비트 개인 키 생성 중...")

        cmd = [
            "openssl", "genrsa",  # RSA 키 생성
            "-out", str(self.key_file),  # 출력 파일
            str(key_size)  # 키 비트 길이
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ 개인 키 생성 완료: {self.key_file}")
            # 키 파일 권한 설정 (읽기 전용)
            os.chmod(self.key_file, 0o600)
            return True
        else:
            print(f"   ❌ 개인 키 생성 실패: {result.stderr}")
            return False
            
    def generate_csr(self):
        """
        인증서 서명 요청 (CSR - Certificate Signing Request) 생성

        CSR이란:
        - 인증서 발급을 요청하기 위한 파일
        - 서버의 공개 키와 신원 정보 포함
        - CA에 제출하여 인증서 발급 받음

        CSR에 포함되는 정보:
        - CN (Common Name): 도메인 이름 (예: localhost, example.com)
        - O (Organization): 조직 이름
        - OU (Organizational Unit): 부서 이름
        - C (Country): 국가 코드 (KR, US 등)
        - ST (State): 시/도
        - L (Locality): 도시

        실제 사용 시:
        - 프로덕션: CN을 실제 도메인으로 변경 (www.example.com)
        - 개발/테스트: localhost 사용

        OpenSSL 명령어:
        openssl req -new -key server.key -out server.csr -subj "/C=KR/..."
        """
        print("\n📝 인증서 서명 요청(CSR) 생성 중...")

        # 인증서 주체 정보 (Subject)
        # 실제 사용 시 조직 정보와 도메인을 변경해야 함
        subject = "/C=KR/ST=Seoul/L=Seoul/O=FastCampus Security Lab/OU=Development/CN=localhost"
        
        cmd = [
            "openssl", "req",
            "-new",
            "-key", str(self.key_file),
            "-out", str(self.csr_file),
            "-subj", subject
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ CSR 생성 완료: {self.csr_file}")
            return True
        else:
            print(f"   ❌ CSR 생성 실패: {result.stderr}")
            return False
            
    def generate_self_signed_certificate(self, days=365):
        """
        자체 서명 인증서 (Self-Signed Certificate) 생성

        자체 서명 인증서란:
        - CA의 서명 없이 자신이 직접 서명한 인증서
        - 개발/테스트 환경에 적합
        - 프로덕션에서는 사용 금지!

        장점:
        - 무료, 즉시 생성 가능
        - 외부 의존성 없음
        - 로컬 개발에 편리

        단점:
        - 브라우저/클라이언트에서 신뢰하지 않음
        - 보안 경고 발생
        - 사용자가 수동으로 신뢰 설정 필요

        CA 서명 인증서 vs 자체 서명:
        - CA 서명: Let's Encrypt, DigiCert 등에서 발급
        - 자체 서명: openssl로 직접 생성
        - CA 서명은 신뢰 체인에 포함되어 자동 신뢰

        SAN (Subject Alternative Names):
        - 하나의 인증서로 여러 도메인/IP 커버
        - 필수 확장 (Chrome 58+에서 CN 무시)
        - DNS.1, DNS.2, IP.1 등으로 지정

        OpenSSL 명령어:
        openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
        """
        print(f"\n🏅 자체 서명 인증서 생성 중 (유효기간: {days}일)...")

        # SAN (Subject Alternative Names) 설정 파일 생성
        # 현대 브라우저는 SAN을 요구 (CN만으로는 부족)
        san_config = self.cert_dir / "san.cnf"
        with open(san_config, 'w') as f:
            f.write("""[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = KR
ST = Seoul
L = Seoul
O = FastCampus Security Lab
OU = Development
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
""")
        
        cmd = [
            "openssl", "x509",
            "-req",
            "-days", str(days),
            "-in", str(self.csr_file),
            "-signkey", str(self.key_file),
            "-out", str(self.cert_file),
            "-extensions", "v3_req",
            "-extfile", str(san_config)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ 인증서 생성 완료: {self.cert_file}")
            # 설정 파일 삭제
            san_config.unlink()
            return True
        else:
            print(f"   ❌ 인증서 생성 실패: {result.stderr}")
            return False
            
    def verify_certificate(self):
        """인증서 정보 확인"""
        print("\n🔍 인증서 정보 확인...")
        
        cmd = [
            "openssl", "x509",
            "-in", str(self.cert_file),
            "-text",
            "-noout"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # 주요 정보만 추출
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ["Subject:", "Issuer:", "Not Before", "Not After", "DNS:", "IP Address:"]):
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"   ❌ 인증서 확인 실패: {result.stderr}")
            return False
            
    def generate_client_certificate(self, client_name="client"):
        """클라이언트 인증서 생성 (상호 TLS용)"""
        print(f"\n👤 클라이언트 인증서 생성: {client_name}")
        
        client_key = self.cert_dir / f"{client_name}.key"
        client_csr = self.cert_dir / f"{client_name}.csr"
        client_cert = self.cert_dir / f"{client_name}.crt"
        
        # 1. 클라이언트 개인 키 생성
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(client_key),
            "2048"
        ], capture_output=True)
        
        # 2. 클라이언트 CSR 생성
        subject = f"/C=KR/ST=Seoul/L=Seoul/O=FastCampus Security Lab/OU=Client/CN={client_name}"
        subprocess.run([
            "openssl", "req",
            "-new",
            "-key", str(client_key),
            "-out", str(client_csr),
            "-subj", subject
        ], capture_output=True)
        
        # 3. 서버 인증서로 클라이언트 인증서 서명
        result = subprocess.run([
            "openssl", "x509",
            "-req",
            "-days", "365",
            "-in", str(client_csr),
            "-CA", str(self.cert_file),
            "-CAkey", str(self.key_file),
            "-CAcreateserial",
            "-out", str(client_cert)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ 클라이언트 인증서 생성 완료:")
            print(f"      - 개인 키: {client_key}")
            print(f"      - 인증서: {client_cert}")
            # 파일 권한 설정
            os.chmod(client_key, 0o600)
            return True
        else:
            print(f"   ❌ 클라이언트 인증서 생성 실패")
            return False
            
    def create_certificate_bundle(self):
        """인증서 번들 생성 (체인)"""
        bundle_file = self.cert_dir / "ca-bundle.crt"
        
        with open(bundle_file, 'w') as bundle:
            with open(self.cert_file, 'r') as cert:
                bundle.write(cert.read())
                
        print(f"\n📦 인증서 번들 생성: {bundle_file}")
        
    def show_security_warnings(self):
        """보안 경고 표시"""
        print("\n⚠️  자체 서명 인증서 사용 시 주의사항")
        print("=" * 60)
        print("1. 브라우저에서 보안 경고가 표시됩니다.")
        print("2. 실제 프로덕션 환경에서는 신뢰할 수 있는 CA의 인증서를 사용하세요.")
        print("3. Let's Encrypt를 통해 무료로 유효한 인증서를 발급받을 수 있습니다.")
        print("4. 자체 서명 인증서는 개발/테스트 목적으로만 사용하세요.")
        
    def show_curl_test_commands(self):
        """테스트 명령어 표시"""
        print("\n🧪 인증서 테스트 명령어")
        print("=" * 60)
        print("# HTTPS 서버 테스트 (인증서 검증 스킵)")
        print("curl -k https://localhost:8443")
        print()
        print("# 인증서 정보 확인")
        print("openssl s_client -connect localhost:8443 -showcerts")
        print()
        print("# 인증서 체인 확인")
        print(f"openssl verify -CAfile {self.cert_file} {self.cert_file}")

def main():
    """메인 실행 함수"""
    print("🔐 TLS 인증서 관리자")
    print("=" * 60)
    
    manager = CertificateManager()
    
    # OpenSSL 확인
    if not manager.check_openssl():
        sys.exit(1)
        
    # 기존 인증서 확인
    if manager.cert_file.exists():
        print(f"\n⚠️  기존 인증서가 존재합니다: {manager.cert_file}")
        response = input("새로 생성하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("기존 인증서를 사용합니다.")
            manager.verify_certificate()
            manager.show_curl_test_commands()
            return
            
    # 인증서 생성 프로세스
    print("\n🚀 새 인증서 생성 시작...")
    
    # 1. 개인 키 생성
    if not manager.generate_private_key():
        sys.exit(1)
        
    # 2. CSR 생성
    if not manager.generate_csr():
        sys.exit(1)
        
    # 3. 자체 서명 인증서 생성
    if not manager.generate_self_signed_certificate():
        sys.exit(1)
        
    # 4. 인증서 정보 확인
    manager.verify_certificate()
    
    # 5. 인증서 번들 생성
    manager.create_certificate_bundle()
    
    # 6. 클라이언트 인증서 생성 (옵션)
    response = input("\n클라이언트 인증서도 생성하시겠습니까? (y/N): ")
    if response.lower() == 'y':
        manager.generate_client_certificate()
        
    # 7. 보안 경고 및 테스트 명령어
    manager.show_security_warnings()
    manager.show_curl_test_commands()
    
    print("\n✅ 인증서 생성이 완료되었습니다!")
    print(f"   인증서 디렉토리: {manager.cert_dir}")

if __name__ == "__main__":
    """
    인증서 생성 스크립트 실행

    실행 방법:
    python3 certificate_management.py

    또는 Docker 환경:
    make shell python3 Part2_SSL/With_TLS/certificate_management.py

    생성되는 파일:
    - ./certs/server.key: 서버 개인 키 (2048비트 RSA)
    - ./certs/server.csr: 인증서 서명 요청
    - ./certs/server.crt: 자체 서명 인증서 (365일 유효)
    - ./certs/ca-bundle.crt: 인증서 번들
    - (옵션) ./certs/client.key, client.crt: 클라이언트 인증서

    사용 예시:
    1. 인증서 생성 후 HTTPS 서버 시작:
       python3 secure_fastapi_mcp_server.py

    2. 브라우저 접속:
       https://localhost:8443
       (보안 경고 발생 - "계속 진행" 클릭)
    """
    main()


# ===========================================
# 종합 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. PKI (Public Key Infrastructure) 개념

   PKI 구성 요소:
   - CA (Certificate Authority): 인증서 발급 기관
   - RA (Registration Authority): 인증 요청 검증
   - 인증서 (Certificate): 공개 키 + 신원 정보
   - CRL (Certificate Revocation List): 폐기 인증서 목록

   신뢰 체인:
   Root CA → Intermediate CA → End Entity Certificate
   - 브라우저는 Root CA를 신뢰
   - Root CA가 서명한 인증서는 자동 신뢰
   - 자체 서명 인증서는 체인에 없어서 경고 발생

2. X.509 인증서 구조

   주요 필드:
   - Version: X.509 버전 (보통 v3)
   - Serial Number: 고유 일련번호
   - Signature Algorithm: 서명 알고리즘 (SHA256-RSA 등)
   - Issuer: 발급자 정보 (CA)
   - Validity: 유효기간 (Not Before, Not After)
   - Subject: 소유자 정보 (CN, O, OU 등)
   - Public Key: 공개 키
   - Extensions: 확장 필드 (SAN, Key Usage 등)
   - Signature: 디지털 서명

3. 인증서 생성 프로세스

   1단계: 개인 키 생성
   openssl genrsa -out server.key 2048
   - RSA 2048비트 개인 키 생성
   - 개인 키는 절대 공개 금지!
   - 파일 권한: 0o600 (소유자만 접근)

   2단계: CSR 생성
   openssl req -new -key server.key -out server.csr -subj "/C=KR/..."
   - 인증서 서명 요청 생성
   - 공개 키 + 신원 정보 포함
   - CA에 제출하여 인증서 발급 요청

   3단계: 인증서 발급

   자체 서명:
   openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
   - 자신의 개인 키로 자신을 서명
   - 개발/테스트용
   - 브라우저 경고 발생

   CA 서명:
   - CSR을 CA에 제출
   - CA가 검증 후 서명
   - 신뢰 체인에 포함
   - 프로덕션용

4. RSA 암호화 알고리즘

   비대칭 암호화:
   - 공개 키: 누구나 사용 가능 (암호화용)
   - 개인 키: 소유자만 보유 (복호화용)

   키 길이:
   - 1024비트: 더 이상 안전하지 않음 (deprecated)
   - 2048비트: 현재 표준
   - 3072비트: 높은 보안
   - 4096비트: 최고 보안 (성능 저하)

   용도:
   - TLS 핸드셰이크: 대칭키 교환
   - 디지털 서명: 신원 확인
   - 데이터 암호화: 소량 데이터

5. SAN (Subject Alternative Names)

   필요성:
   - Chrome 58+ 부터 CN 필드 무시
   - SAN이 없으면 인증서 오류
   - 여러 도메인/IP를 하나의 인증서로 커버

   설정 예시:
   [alt_names]
   DNS.1 = localhost
   DNS.2 = *.localhost
   DNS.3 = example.com
   IP.1 = 127.0.0.1
   IP.2 = ::1

   장점:
   - 멀티 도메인 지원
   - 와일드카드 지원
   - IPv4/IPv6 모두 지원

6. 자체 서명 vs CA 서명 인증서

   자체 서명 인증서:
   장점:
   - 무료, 즉시 생성
   - 외부 의존성 없음
   - 로컬 개발에 편리

   단점:
   - 브라우저 신뢰 없음
   - 보안 경고 발생
   - 수동 신뢰 설정 필요
   - 프로덕션 사용 불가

   CA 서명 인증서:
   장점:
   - 자동 신뢰
   - 보안 경고 없음
   - 프로덕션 사용 가능

   단점:
   - 비용 (무료: Let's Encrypt)
   - 발급 시간 필요
   - 갱신 관리 필요

7. Let's Encrypt

   무료 CA:
   - 무료 TLS 인증서 제공
   - 자동 갱신 (90일마다)
   - Certbot 도구 사용

   설치 예시:
   # Certbot 설치
   sudo apt-get install certbot python3-certbot-nginx

   # 인증서 발급
   sudo certbot certonly --standalone -d example.com

   # 자동 갱신 설정
   sudo certbot renew --dry-run

8. mTLS (Mutual TLS)

   개념:
   - 서버와 클라이언트 양방향 인증
   - 일반 TLS: 서버만 인증서 제공
   - mTLS: 클라이언트도 인증서 제공

   사용 사례:
   - 마이크로서비스 간 통신
   - API 인증 (OAuth 대안)
   - IoT 디바이스 인증
   - 높은 보안이 필요한 환경

   구현:
   - 클라이언트 인증서 생성
   - 서버 설정에서 클라이언트 검증 활성화
   - 클라이언트가 연결 시 인증서 제시

9. 인증서 보안 모범 사례

   개인 키 보호:
   - 파일 권한: 0o600 (소유자만)
   - Git 커밋 금지 (.gitignore)
   - 암호화 저장 (HSM, KMS)
   - 정기적 교체

   인증서 관리:
   - 유효기간 모니터링
   - 자동 갱신 설정
   - 인증서 폐기 시 CRL 업데이트
   - 강력한 암호화 알고리즘 사용

   배포:
   - HTTPS 강제 (HSTS)
   - 최신 TLS 버전 사용 (TLS 1.3)
   - 약한 암호 스위트 비활성화
   - Perfect Forward Secrecy 활성화

10. 다음 학습 단계

    - secure_fastapi_mcp_server.py 실행
      * 생성한 인증서로 HTTPS 서버 시작
      * TLS 핸드셰이크 과정 이해
      * 브라우저 보안 경고 처리

    - secure_attack_simulation.py 실행
      * HTTPS 트래픽 스니핑 시도
      * 암호화된 데이터 확인
      * HTTP vs HTTPS 비교

    - TLS 프로토콜 심화
      * 핸드셰이크 과정
      * 대칭키 교환 메커니즘
      * Perfect Forward Secrecy

핵심 메시지:
인증서는 HTTPS의 핵심입니다!
개발에서는 자체 서명 인증서를 사용하고,
프로덕션에서는 반드시 신뢰할 수 있는 CA의 인증서를 사용하세요!
"""