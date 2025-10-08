# Makefile for Docker Compose user sync
# =====================================

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

# 컨테이너 중지 및 제거
down:
	@docker compose down

# 모든 관련 리소스(이미지, 볼륨 등)를 완전히 정리
clean:
	@docker compose down --rmi all --volumes --remove-orphans
	@docker system prune -a
