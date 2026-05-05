"""Mock 后端 —— 模拟完整 Q&A 响应，用于前端独立开发调试。"""
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64

app = FastAPI(title='多模态商帮问答系统 Mock API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

MOCK_SOURCES = [
    {
        'chunk_id': 'book003_0012',
        'book_title': '晋商中国第一商帮',
        'chapter_title': '第三章 票号制度的兴起',
        'text': (
            '票号是晋商独创的金融机构，起源于清代乾隆年间。日升昌票号是中国第一家'
            '专营汇兑业务的金融机构，其「汇通天下」的经营理念开创了中国近代金融业'
            '之先河。票号通过总分号制度建立起覆盖全国的汇兑网络，北至恰克图，南至'
            '广州，西至迪化，东至上海，形成了庞大的金融网络。'
        ),
    },
    {
        'chunk_id': 'book005_0047',
        'book_title': '徽商精神',
        'chapter_title': '第五章 徽商与科举文化',
        'text': (
            '徽商素有「贾而好儒」的传统，许多徽商在经商致富后延师教子、捐资办学。'
            '明清两代，徽州府共出进士1136人，状元29人，是全国进士密度最高的地区之一。'
            '这种亦贾亦儒的传统使徽商具有较高的文化素养，在处理商业契约、官府往来时'
            '得心应手。'
        ),
    },
    {
        'chunk_id': 'book012_0089',
        'book_title': '成败晋商',
        'chapter_title': '第七章 晋商没落的原因分析',
        'text': (
            '晋商衰落有多方面原因：一是清末战乱频繁，商路受阻；二是现代银行业的'
            '冲击使传统票号失去竞争优势；三是晋商固守传统经营模式，未能及时转型为'
            '现代股份公司；四是俄国十月革命后，晋商在俄资产被没收，损失惨重。'
        ),
    },
]

MOCK_ANSWERS = {
    '票号': (
        '票号是晋商在清代乾隆年间创立的金融机构，以日升昌票号为代表。其核心创新'
        '在于「汇兑」——商户在甲地存入银两，凭票在乙地兑取，避免了长途运银的风险。'
        '票号采用总分号制度，在全国设立分号，覆盖范围包括恰克图、广州、迪化、上海'
        '等地，实现了真正意义上的「汇通天下」。票号的出现标志着中国传统金融业从'
        '单纯的借贷向现代汇兑体系迈进了一大步。'
    ),
    '徽商': (
        '徽商的核心特色是「贾而好儒」。他们重视教育，明清两代徽州府进士密度冠绝'
        '全国。这种亦贾亦儒的传统使徽商在契约管理、官府往来方面具有独特优势。同时'
        '徽商以宗族为纽带，以「诚信」为经营之本，形成了稳固的商业网络。'
    ),
    'default': (
        '根据检索到的历史文献，您的问题涉及中国商帮历史的重要议题。商帮作为中国'
        '明清时期的地域性商业组织，在经济活动中发挥了关键作用。其中晋商以票号金融'
        '著称，徽商以贾而好儒的文化底蕴闻名，陕商以茶马古道贸易为主线，各有特色和贡献。'
    ),
}


@app.post('/api/qa')
async def ask_question(
    question: str = Form(...),
    image: UploadFile | None = File(None),
):
    """Mock 问答接口：根据关键词返回预设答案和来源。"""
    if image:
        await image.read()  # 模拟接收图片

    answer = MOCK_ANSWERS['default']
    for keyword, ans in MOCK_ANSWERS.items():
        if keyword in question:
            answer = ans
            break

    return {
        'answer': answer,
        'sources': MOCK_SOURCES,
        'scores': [0.9231, 0.8715, 0.8034],
    }


@app.get('/health')
async def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
