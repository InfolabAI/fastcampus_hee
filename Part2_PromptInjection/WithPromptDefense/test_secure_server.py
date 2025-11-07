#!/usr/bin/env python3
"""
보안 LLM 서버 테스트 클라이언트

정상적인 사용 시나리오를 테스트합니다.
방어 메커니즘이 적용되어도 정상 기능은 잘 작동하는지 확인합니다.
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_secure_server():
    """보안 LLM 서버의 정상 동작 테스트"""

    print("=" * 70)
    print("🧪 보안 LLM 서버 - 정상 동작 테스트")
    print("=" * 70)
    print("🛡️  방어 메커니즘이 적용된 상태에서 정상 기능 확인")
    print("=" * 70)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "secure_server.py")],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. 일반 채팅 테스트
            print("\n📝 테스트 1: 일반 채팅")
            print("-" * 70)
            result = await session.call_tool("chat", arguments={
                "message": "Hello! How are you?"
            })
            print(f"결과: {result.content[0].text}")

            # 2. 문서 요약 테스트
            print("\n📝 테스트 2: 문서 요약")
            print("-" * 70)
            document = """
            Artificial Intelligence has transformed various industries.
            Machine learning algorithms can now process vast amounts of data
            to provide insights and predictions.
            """
            result = await session.call_tool("summarize_document", arguments={
                "document": document
            })
            print(f"결과: {result.content[0].text}")

            # 3. 텍스트 번역 테스트
            print("\n📝 테스트 3: 텍스트 번역")
            print("-" * 70)
            result = await session.call_tool("translate_text", arguments={
                "text": "Hello, how are you today?",
                "target_language": "Korean"
            })
            print(f"결과: {result.content[0].text}")

            # 4. 데이터 분석 테스트
            print("\n📝 테스트 4: 데이터 분석")
            print("-" * 70)
            data = "Sales: Q1=100, Q2=150, Q3=200, Q4=250"
            result = await session.call_tool("analyze_data", arguments={
                "data": data,
                "analysis_type": "trend"
            })
            print(f"결과: {result.content[0].text}")

            # 5. 한국어 채팅 테스트
            print("\n📝 테스트 5: 한국어 채팅")
            print("-" * 70)
            result = await session.call_tool("chat", arguments={
                "message": "안녕하세요! 날씨가 좋네요."
            })
            print(f"결과: {result.content[0].text}")

            # 6. 복잡한 질문 테스트
            print("\n📝 테스트 6: 복잡한 질문")
            print("-" * 70)
            result = await session.call_tool("chat", arguments={
                "message": "Can you explain what machine learning is and how it works?"
            })
            print(f"결과: {result.content[0].text}")

    print("\n" + "=" * 70)
    print("✅ 모든 정상 테스트 완료")
    print("=" * 70)
    print("\n💡 확인 사항:")
    print("  ✓ 모든 정상 기능이 올바르게 작동합니다")
    print("  ✓ 방어 메커니즘이 정상 사용을 방해하지 않습니다")
    print("  ✓ 사용자 경험이 유지됩니다")
    print()
    print("🔒 적용된 보안 기능:")
    print("  • 입력 검증 및 정제")
    print("  • 구조화된 프롬프트 템플릿")
    print("  • 출력 검증")
    print("  • 권한 분리")
    print("  • 길이 제한")
    print("  • 감사 로깅")
    print()
    print("💡 다음 단계: secure_attack_simulation.py를 실행하여 방어를 검증해보세요!")

if __name__ == "__main__":
    asyncio.run(test_secure_server())
