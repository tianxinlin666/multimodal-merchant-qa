"""API 验证脚本 —— 绕过 Shell 编码问题。"""
import httpx
import asyncio
import json

async def main():
    async with httpx.AsyncClient() as client:
        # 测试 1: 票号关键词
        r = await client.post('http://localhost:8080/api/qa',
            data={'question': '晋商的票号制度是如何运作的'})
        data = r.json()
        print(f'[票号] {data["answer"][:80]}...')
        print(f'  来源: {len(data["sources"])} 条, 得分: {data["scores"]}')
        assert '汇兑' in data['answer'], '票号关键词未匹配!'
        print('  PASS')

        # 测试 2: 徽商关键词
        r = await client.post('http://localhost:8080/api/qa',
            data={'question': '徽商文化有什么特点'})
        data = r.json()
        print(f'[徽商] {data["answer"][:80]}...')
        assert '贾而好儒' in data['answer'], '徽商关键词未匹配!'
        print('  PASS')

        # 测试 3: 健康检查
        r = await client.get('http://localhost:8080/health')
        assert r.json()['status'] == 'ok'
        print('[Health] PASS')

        print('\n全部测试通过!')

asyncio.run(main())
