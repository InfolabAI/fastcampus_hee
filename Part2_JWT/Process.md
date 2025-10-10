# MCP 보안 실습: JWT 인증 부재의 위험성

> **실습 목표**: HTTP MCP 서버와 프록시를 이용한 JWT 인증의 중요성 체험

## 📋 실습 개요

JWT 인증 부재의 위험성을 다음 4단계로 실습합니다:

1. **JWT 없는 상태에서 통신 실습**
2. **JWT 없는 상태에서 해킹 공격 및 탈취 실습**  
3. **JWT 있는 상태에서의 통신 실습**
4. **JWT 있는 상태에서의 해킹 공격 방어 실습**

---

## 🚀 1단계: JWT 없는 상태에서 통신 실습

### 환경 설정
```bash
# Terminal 1: 취약한 HTTP MCP 서버 시작 (JWT 인증 없음)
cd /home/hee/Dropbox/projects/fastcampus_2508/Part1_Ch3/NoJWT
python3 http_server.py
```

### 정상적인 통신 테스트 (stdio proxy 사용)
```bash
# Terminal 2: stdio proxy를 통한 테스트
python3 test_http_server_proxy.py
```

### 공격자 시뮬레이션 테스트
```bash
# Terminal 3: 공격자가 HTTP MCP 서버에 무단 접근하는 시나리오
python3 attack_simulation.py
```

**✅ 예상 결과**: 누구나 인증 없이 API에 접근하여 연산을 수행할 수 있음

---

## ⚠️ 2단계: JWT 없는 상태에서 해킹 공격 및 탈취 실습

### 2-1. 종합적인 공격 시나리오 실행
```bash
# Terminal 4: 공격 시뮬레이션 스크립트 실행 (모든 공격 유형 포함)
cd /home/hee/Dropbox/projects/fastcampus_2508/Part1_Ch3/NoJWT
python3 attack_simulation.py
```

**포함된 공격 시나리오:**
- **정찰**: 사용 가능한 도구 목록 탐색
- **기능 남용**: 정상 기능을 악용한 리소스 소모
- **악의적 입력**: XSS, SQL 인젝션, 파일 시스템 접근 시도
- **DoS 공격**: 동시 대량 요청으로 서버 과부하 시도

### 2-2. 네트워크 트래픽 모니터링 (선택사항)
```bash
# Terminal 6: 공격 중 네트워크 트래픽 분석
sudo tcpdump -i lo -w /tmp/mcp_traffic.pcap port 8000 &
TCPDUMP_PID=$!

# 공격 시뮬레이션 실행 후 패킷 분석
sleep 10
sudo kill $TCPDUMP_PID
tcpdump -r /tmp/mcp_traffic.pcap -A | grep -i "add\|greeting"
```

**⚠️ 공격 결과**: 
- 서버 리소스 고갈로 정상 사용자 서비스 불가
- 악의적인 스크립트 실행 가능
- 네트워크 트래픽 평문 노출

---

## 🛡️ 3단계: JWT 있는 상태에서의 통신 실습

### 보안 서버 설정

**📄 보안 서버 파일 생성**: `secure_http_server.py`가 생성되었습니다.

> 이 파일은 JWT 인증, 토큰 생성/검증, 권한 관리 기능을 포함합니다.

### 보안 서버 실행
```bash
# Terminal 1: 기존 서버들을 종료(Ctrl+C) 후, JWT 인증 적용된 보안 서버 시작
cd /home/hee/Dropbox/projects/fastcampus_2508/Part1_Ch3/WithJWT
python3 secure_http_server.py
```

> **중요**: 서버 시작 시 `.token` 파일이 자동 생성되어 프록시가 JWT 토큰을 공유할 수 있습니다.

### stdio proxy를 통한 JWT 인증 테스트
```bash
# Terminal 2: stdio proxy를 통한 보안 서버 테스트
python3 test_secure_server_proxy.py
```

**📋 JWT 프록시 통신 과정:**
1. `secure_http_server_proxy.py`가 `.token` 파일에서 JWT 토큰 읽기
2. `BearerAuth`를 통해 모든 요청에 자동으로 Authorization 헤더 추가
3. 클라이언트는 JWT 토큰을 의식하지 않고 MCP 도구 사용

> **참고**: HTTP curl 방식은 MCP 세션 관리의 복잡성으로 인해 권장하지 않습니다. 실습에서는 MCP 클라이언트와 공격 시뮬레이션을 사용합니다.

**✅ 예상 결과**: 유효한 JWT 토큰을 가진 사용자만 API에 접근 가능

---

## 🔒 4단계: JWT 있는 상태에서의 해킹 공격 방어 실습

### 종합적인 보안 공격 방어 시뮬레이션
```bash
# Terminal 3: 보안 서버에 대한 모든 공격 시나리오 테스트
cd /home/hee/Dropbox/projects/fastcampus_2508/Part1_Ch3/WithJWT
python3 secure_attack_simulation.py
```

**포함된 방어 테스트 시나리오:**
- **무단 접근**: JWT 토큰 없는 접근 시도 → 401 차단 확인
- **위조 토큰**: 잘못된 JWT 토큰 사용 → 401 차단 확인  
- **만료 토큰**: 만료된 토큰 사용 → 401 차단 확인
- **DoS 방어**: 대량 무단 요청 → 모두 401로 차단되어 리소스 보호
- **정상 접근**: MCP 클라이언트를 통한 정상적인 토큰 발급 확인

**🛡️ 방어 결과**:
- 무단 접근 시도: 모두 401 Unauthorized로 차단
- DoS 공격: 인증 단계에서 모두 차단되어 서버 리소스 보호
- 정상 사용자: 유효한 토큰으로 정상 서비스 이용 가능

---

## 📊 추가 보안 모니터링

### 보안 이벤트 로깅
```bash
# Terminal 9: 서버 로그 실시간 모니터링
tail -f /var/log/syslog | grep -i "mcp\|jwt\|auth"
```

### 네트워크 트래픽 분석
```bash
# 보안 서버의 트래픽 패턴 분석
sudo tcpdump -i lo -w /tmp/secure_mcp_traffic.pcap port 8001 &
TCPDUMP_PID2=$!

# 잠시 후 패킷 캡처 중지하고 분석
sleep 10
sudo kill $TCPDUMP_PID2
echo "보안 서버 트래픽 분석:"
tcpdump -r /tmp/secure_mcp_traffic.pcap -A | grep -i "authorization\|401\|403"
```

---

## 📝 실습 요약

### 🎯 학습 목표 달성 확인

| 단계 | 시나리오 | 결과 | 학습 포인트 |
|------|----------|------|-------------|
| **1단계** | JWT 없는 통신 | ✅ 성공 | 누구나 API에 접근 가능 |
| **2단계** | 해킹 공격 시도 | ⚠️ 성공 | DoS, 파라미터 주입, 트래픽 스니핑 가능 |
| **3단계** | JWT 인증 통신 | 🛡️ 보안 | 유효한 토큰 보유자만 접근 가능 |
| **4단계** | 공격 방어 확인 | 🔒 차단 | 모든 무단 접근이 401 Unauthorized로 차단 |

### 💡 핵심 보안 개념

1. **인증 부재의 위험성**
   - 무제한 API 접근으로 인한 리소스 남용
   - 민감한 기능에 대한 무단 사용
   - 서비스 가용성 저하

2. **JWT 인증의 효과**
   - 토큰 기반 상태 비저장(stateless) 인증
   - 만료 시간을 통한 보안 강화
   - 권한 기반 접근 제어

3. **실전 보안 구현**
   - 인증 미들웨어를 통한 자동 검증
   - 적절한 HTTP 상태 코드 응답(401, 403)
   - 보안 이벤트 로깅 및 모니터링

### 🚀 다음 단계

Part1_Ch3의 기존 코드를 활용하여 JWT 인증의 중요성을 실제 공격/방어 시나리오로 체험할 수 있는 완전한 실습 환경을 구성했습니다.

### 🔑 실습 구조별 특징

#### NoJWT 폴더 (취약한 환경)
- **목적**: JWT 인증 부재의 위험성 체험
- **특징**: 누구나 HTTP 엔드포인트로 직접 접근 가능
- **공격 시나리오**: 무제한 API 호출, 리소스 남용, DoS 공격

#### WithJWT 폴더 (보안 강화 환경)  
- **목적**: JWT 인증을 통한 보안 강화 체험
- **특징**: 유효한 JWT 토큰 없이는 401 Unauthorized 응답
- **방어 효과**: 모든 무단 접근 차단, 정상 사용자만 서비스 이용

#### 토큰 공유 메커니즘
1. **서버**: 시작 시 `.token` 파일에 유효한 JWT 토큰 저장
2. **프록시**: `.token` 파일에서 토큰을 읽어 BearerAuth에 설정
3. **클라이언트**: 프록시를 통해 투명한 JWT 인증 처리

**파일 구조**:
```
Part1_Ch3/
├── simple_server.py          # 기본 MCP 서버 (stdio)
├── test_simple_server.py     # stdio 직접 연결 테스트
├── 📁 NoJWT/                  # JWT 인증 없는 HTTP MCP 서버 실습
│   ├── http_server.py            # HTTP MCP 서버 (인증 없음)
│   ├── test_http_server.py       # HTTP 직접 연결 테스트
│   ├── http_server_proxy.py      # stdio-HTTP 프록시
│   ├── test_http_server_proxy.py # HTTP 프록시를 통한 테스트
│   └── attack_simulation.py      # 무단 접근 공격 시뮬레이션
└── 📁 WithJWT/                # JWT 인증 적용된 보안 MCP 서버 실습
    ├── secure_http_server.py     # HTTP MCP 서버 (JWT 인증)
    ├── secure_http_server_proxy.py # 보안 서버용 stdio-HTTP 프록시 
    ├── test_secure_server_proxy.py # 프록시를 통한 보안 서버 테스트
    ├── secure_attack_simulation.py # JWT 인증 서버 공격 방어 테스트
    └── .token                     # 서버가 생성한 JWT 토큰 (자동 생성)
```

**실무 적용을 위한 추가 고려사항:**
- 환경 변수를 통한 시크릿 키 관리
- Rate Limiting을 통한 추가 보안 강화
- HTTPS를 통한 네트워크 레벨 암호화
- 로그 분석을 통한 보안 모니터링