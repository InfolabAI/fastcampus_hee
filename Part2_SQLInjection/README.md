# Part2_SQLInjection - SQL Injection 공격과 방어 실습

SQL Injection 취약점의 위험성과 방어 기법을 실습하는 교육 자료입니다.

## 📂 폴더 구조

```
Part2_SQLInjection/
├── README.md                        # 이 파일
├── Process.md                       # 상세 실습 가이드
├── NoSQLDefense/                    # SQL Injection 취약한 환경
│   ├── vulnerable_server.py         # 취약한 MCP 서버
│   ├── test_vulnerable_server.py    # 정상 동작 테스트
│   └── attack_simulation.py         # 공격 시뮬레이션
└── WithSQLDefense/                  # SQL Injection 방어 환경
    ├── secure_server.py             # 보안 강화 MCP 서버
    ├── test_secure_server.py        # 정상 동작 테스트
    └── secure_attack_simulation.py  # 방어 테스트
```

## 🚀 빠른 시작

### 방법 1: Docker 환경에서 실행 (권장)

```bash
# 프로젝트 루트에서 Docker 컨테이너 시작
cd /home/hee/Dropbox/projects/fastcampus
make up

# 1단계: 취약한 서버 테스트
make shell python Part2_SQLInjection/NoSQLDefense/test_vulnerable_server.py

# 2단계: 공격 시뮬레이션
make shell python Part2_SQLInjection/NoSQLDefense/attack_simulation.py

# 3단계: 보안 서버 테스트
make shell python Part2_SQLInjection/WithSQLDefense/test_secure_server.py

# 4단계: 방어 테스트
make shell python Part2_SQLInjection/WithSQLDefense/secure_attack_simulation.py

# 컨테이너 중지
make down
```

### 방법 2: 로컬 환경에서 실행

#### 1단계: 취약한 서버 실습

```bash
cd NoSQLDefense

# Terminal 1: 서버 시작
python3 vulnerable_server.py

# Terminal 2: 정상 동작 테스트
python3 test_vulnerable_server.py

# Terminal 3: 공격 시뮬레이션
python3 attack_simulation.py
```

#### 2단계: 보안 서버 실습

```bash
cd WithSQLDefense

# Terminal 1: 보안 서버 시작
python3 secure_server.py

# Terminal 2: 정상 동작 테스트
python3 test_secure_server.py

# Terminal 3: 방어 테스트
python3 secure_attack_simulation.py
```

## 📚 학습 내용

### 취약점 (NoSQLDefense)
- ❌ 문자열 연결로 SQL 쿼리 생성
- ❌ 입력값 검증 없음
- ❌ 상세한 에러 메시지 노출
- ❌ 인증 우회 가능
- ❌ 데이터 탈취 가능

### 방어 기법 (WithSQLDefense)
- ✅ Prepared Statements 사용
- ✅ 파라미터화된 쿼리
- ✅ 입력값 검증 및 화이트리스트
- ✅ 에러 메시지 최소화
- ✅ 모든 악의적 입력 차단

## ⚠️ 주의사항

이 코드는 **교육 목적으로만** 사용하세요. 실제 시스템에 무단으로 공격을 시도하면 법적 책임을 질 수 있습니다.

## 📖 상세 가이드

전체 실습 과정은 [Process.md](Process.md)를 참고하세요.
