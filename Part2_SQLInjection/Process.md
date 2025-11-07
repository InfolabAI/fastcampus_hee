# MCP 보안 실습: SQL Injection 공격과 방어

> **실습 목표**: MCP 서버를 이용한 SQL Injection 취약점과 방어 기법 체험

## 📋 실습 개요

SQL Injection 취약점의 위험성을 다음 4단계로 실습합니다:

1. **SQL Injection 취약점이 있는 서버 통신 실습**
2. **SQL Injection 공격 및 데이터 탈취 실습**
3. **SQL Injection 방어가 적용된 서버 통신 실습**
4. **SQL Injection 공격 방어 실습**

---

## 🚀 1단계: SQL Injection 취약점이 있는 서버 통신 실습

### 환경 설정
```bash
# Terminal 1: 취약한 MCP 서버 시작 (SQL Injection 취약점 존재)
cd /home/hee/Dropbox/projects/fastcampus/Part2_SQLInjection/NoSQLDefense
python3 vulnerable_server.py
```

### 정상적인 통신 테스트
```bash
# Terminal 2: 정상적인 사용자 조회 테스트
python3 test_vulnerable_server.py
```

### 공격자 시뮬레이션 테스트
```bash
# Terminal 3: SQL Injection 공격 시나리오
python3 attack_simulation.py
```

**✅ 예상 결과**: 정상적인 쿼리는 작동하지만, 악의적인 입력에 취약함

---

## ⚠️ 2단계: SQL Injection 공격 및 데이터 탈취 실습

### 2-1. 종합적인 공격 시나리오 실행
```bash
# Terminal 4: SQL Injection 공격 시뮬레이션 스크립트 실행
cd /home/hee/Dropbox/projects/fastcampus/Part2_SQLInjection/NoSQLDefense
python3 attack_simulation.py
```

**포함된 공격 시나리오:**
- **인증 우회**: `' OR '1'='1` 를 이용한 로그인 우회
- **데이터 추출**: UNION SELECT를 이용한 전체 사용자 정보 탈취
- **데이터 조작**: UPDATE/DELETE를 이용한 데이터 변조
- **정보 수집**: 데이터베이스 스키마 정보 탈취

### 2-2. 데이터베이스 모니터링 (선택사항)
```bash
# Terminal 5: SQL 쿼리 로그 실시간 모니터링
tail -f /tmp/sql_queries.log
```

**⚠️ 공격 결과**:
- 인증 없이 관리자 계정으로 로그인 성공
- 전체 사용자 데이터베이스 내용 탈취
- 데이터 변조 및 삭제 가능
- 데이터베이스 구조 정보 노출

---

## 🛡️ 3단계: SQL Injection 방어가 적용된 서버 통신 실습

### 보안 서버 설정

**📄 보안 서버 파일 생성**: `secure_server.py`가 생성되었습니다.

> 이 파일은 Prepared Statements, Input Validation, 파라미터화된 쿼리를 포함합니다.

### 보안 서버 실행
```bash
# Terminal 1: 기존 서버를 종료(Ctrl+C) 후, SQL Injection 방어가 적용된 보안 서버 시작
cd /home/hee/Dropbox/projects/fastcampus/Part2_SQLInjection/WithSQLDefense
python3 secure_server.py
```

### 정상적인 통신 테스트
```bash
# Terminal 2: 보안 서버를 통한 정상 테스트
python3 test_secure_server.py
```

**📋 SQL Injection 방어 메커니즘:**
1. **Prepared Statements**: SQL 쿼리와 데이터를 분리
2. **Input Validation**: 입력값 검증 및 필터링
3. **파라미터화된 쿼리**: 동적 쿼리 생성 방지
4. **최소 권한 원칙**: 데이터베이스 사용자 권한 제한

**✅ 예상 결과**: 정상적인 쿼리만 처리되고, 악의적인 입력은 차단됨

---

## 🔒 4단계: SQL Injection 공격 방어 실습

### 종합적인 보안 공격 방어 시뮬레이션
```bash
# Terminal 3: 보안 서버에 대한 모든 SQL Injection 공격 테스트
cd /home/hee/Dropbox/projects/fastcampus/Part2_SQLInjection/WithSQLDefense
python3 secure_attack_simulation.py
```

**포함된 방어 테스트 시나리오:**
- **인증 우회 시도**: `' OR '1'='1` → 차단 확인
- **UNION SELECT**: UNION 기반 데이터 추출 시도 → 차단 확인
- **Blind SQL Injection**: 시간 기반 공격 → 차단 확인
- **Stacked Queries**: 다중 쿼리 실행 시도 → 차단 확인
- **정상 접근**: 올바른 입력으로 정상 동작 확인

**🛡️ 방어 결과**:
- 악의적인 SQL 구문: 모두 무해한 문자열로 처리됨
- 데이터 탈취 시도: Prepared Statement로 차단
- 정상 사용자: 정상적인 데이터 조회 및 처리 가능

---

## 📊 추가 보안 모니터링

### 보안 이벤트 로깅
```bash
# Terminal 6: 서버 로그 실시간 모니터링
tail -f /tmp/secure_sql_server.log | grep -i "injection\|blocked\|suspicious"
```

### SQL 쿼리 분석
```bash
# 실행된 SQL 쿼리 패턴 분석
grep "SELECT\|INSERT\|UPDATE\|DELETE" /tmp/secure_sql_server.log | tail -20
```

---

## 📝 실습 요약

### 🎯 학습 목표 달성 확인

| 단계 | 시나리오 | 결과 | 학습 포인트 |
|------|----------|------|-------------|
| **1단계** | 취약한 서버 통신 | ✅ 성공 | 정상 쿼리 작동 |
| **2단계** | SQL Injection 공격 | ⚠️ 성공 | 인증 우회, 데이터 탈취, 데이터 조작 가능 |
| **3단계** | 보안 서버 통신 | 🛡️ 보안 | Prepared Statement 적용 |
| **4단계** | 공격 방어 확인 | 🔒 차단 | 모든 악의적 입력이 무해화됨 |

### 💡 핵심 보안 개념

1. **SQL Injection 취약점의 위험성**
   - 인증 우회로 인한 무단 접근
   - 민감한 데이터 탈취 (개인정보, 비밀번호 등)
   - 데이터 변조 및 삭제
   - 시스템 명령 실행 가능성

2. **SQL Injection 방어 기법**
   - **Prepared Statements**: SQL과 데이터 분리
   - **Input Validation**: 입력값 검증 및 화이트리스트
   - **파라미터화된 쿼리**: Placeholder 사용
   - **최소 권한**: 데이터베이스 사용자 권한 최소화
   - **에러 메시지 제한**: DB 구조 정보 노출 방지

3. **실전 보안 구현**
   - ORM 사용으로 안전한 쿼리 생성
   - 입력값 이스케이프 처리
   - 보안 이벤트 로깅 및 모니터링
   - 정기적인 보안 감사

### 🔑 실습 구조별 특징

#### NoSQLDefense 폴더 (취약한 환경)
- **목적**: SQL Injection 취약점의 위험성 체험
- **특징**: 문자열 연결로 SQL 쿼리 생성
- **공격 시나리오**: 인증 우회, 데이터 탈취, 데이터 조작

#### WithSQLDefense 폴더 (보안 강화 환경)
- **목적**: SQL Injection 방어 기법 체험
- **특징**: Prepared Statement와 Input Validation 적용
- **방어 효과**: 모든 악의적 입력 무해화, 정상 사용자만 데이터 접근

**파일 구조**:
```
Part2_SQLInjection/
├── Process.md                      # 이 파일
├── 📁 NoSQLDefense/                # SQL Injection 취약한 서버 실습
│   ├── vulnerable_server.py           # 취약한 MCP 서버
│   ├── test_vulnerable_server.py      # 정상 동작 테스트
│   └── attack_simulation.py           # SQL Injection 공격 시뮬레이션
└── 📁 WithSQLDefense/              # SQL Injection 방어 서버 실습
    ├── secure_server.py               # 보안이 적용된 MCP 서버
    ├── test_secure_server.py          # 정상 동작 테스트
    └── secure_attack_simulation.py    # 방어 테스트
```

**실무 적용을 위한 추가 고려사항:**
- ORM(SQLAlchemy, Django ORM 등) 사용
- WAF(Web Application Firewall) 적용
- 정기적인 보안 취약점 스캔
- 침입 탐지 시스템(IDS) 구축
- 데이터베이스 접근 로그 분석
