# Makefile for Docker Compose user sync
# =====================================

.PHONY: help init up exec shell down clean

# 도움말 표시
help:
	@echo "사용 가능한 명령어:"
	@echo "  make init   - .env 파일 생성 (UID/GID 설정)"
	@echo "  make up     - Docker 컨테이너 시작"
	@echo "  make exec   - 컨테이너에 bash로 접속"
	@echo "  make shell  - 컨테이너에서 명령어 실행"
	@echo "                예: make shell python Part2_SQLInjection/NoSQLDefense/test_vulnerable_server.py"
	@echo "  make down   - 컨테이너 중지 및 제거"
	@echo "  make clean  - 모든 리소스 정리"

# .env 파일에 현재 사용자의 UID/GID를 자동으로 기록
init:
	@echo "UID=$$(id -u)" > .env
	@echo "GID=$$(id -g)" >> .env
	@echo ".env file generated with UID=$$(id -u), GID=$$(id -g)"

# Docker Compose 빌드 및 컨테이너 실행 (백그라운드)
up: init
	@docker compose up -d --build
	@echo "🚀 Container started. Run 'make exec' to enter."

# 실행 중인 컨테이너에 접속
exec:
	@docker compose exec fastcampus bash

# 컨테이너에서 명령어 실행 (예: make shell python Part2_SQLInjection/NoSQLDefense/test_vulnerable_server.py)
shell:
	@docker compose exec fastcampus $(filter-out $@,$(MAKECMDGOALS))

# 나머지 인자를 무시하도록 설정 (shell 명령어용)
%:
	@:

# 컨테이너 중지 및 제거
down:
	@docker compose down

# 모든 관련 리소스(이미지, 볼륨 등)를 완전히 정리
clean:
	@docker compose down --rmi all --volumes --remove-orphans
	@docker system prune -a
