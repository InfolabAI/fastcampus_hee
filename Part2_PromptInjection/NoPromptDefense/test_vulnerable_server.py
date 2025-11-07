#!/usr/bin/env python3
"""
취약한 LLM 서버 테스트 클라이언트

정상적인 사용 시나리오를 테스트합니다.
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_vulnerable_server():
    """취약한 LLM 서버의 정상 동작 테스트"""

    print("=" * 70)
    print("🧪 취약한 LLM 서버 - 정상 동작 테스트")
    print("=" * 70)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "vulnerable_server.py")],
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
            Artificial Intelligence (AI) has transformed various industries.
            Machine learning algorithms can now process vast amounts of data
            to provide insights and predictions. Deep learning, a subset of
            machine learning, uses neural networks to solve complex problems.
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

    print("\n" + "=" * 70)
    print("✅ 모든 정상 테스트 완료")
    print("=" * 70)
    print("\n💡 다음 단계: attack_simulation.py를 실행하여 공격을 시도해보세요!")

if __name__ == "__main__":
    asyncio.run(test_vulnerable_server())
