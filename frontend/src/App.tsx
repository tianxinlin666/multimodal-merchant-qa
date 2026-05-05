/** 多模态商帮问答系统 —— 主应用组件。 */

import { useState, useRef, type FormEvent, type ChangeEvent } from "react";
import { askQuestion, type QAResponse, type Source } from "./api";

type Status = "idle" | "loading" | "success" | "error";

const PLACEHOLDER = `输入您关于商帮历史的问题，例如：
· 晋商的票号制度是如何运作的？
· 徽商为什么被称为「贾而好儒」？
· 明清商帮衰落的主要原因是什么？`;

export default function App() {
  const [question, setQuestion] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<QAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImage(file);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setStatus("loading");
    setError(null);
    setResult(null);
    try {
      const res = await askQuestion(question, image ?? undefined);
      setResult(res);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败，请检查后端是否启动");
      setStatus("error");
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>多模态商帮问答系统</h1>
        <p className="subtitle">
          基于 100+ 本晋商 / 徽商 / 苏商 / 陕商 / 粤商 / 浙商历史文献的智能问答
        </p>
      </header>

      <form className="qa-form" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={PLACEHOLDER}
          rows={4}
          className="question-input"
        />

        <div className="form-actions">
          <div className="upload-area">
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              style={{ display: "none" }}
            />
            <button type="button" className="btn btn-outline" onClick={() => fileRef.current?.click()}>
              {"📷"} 上传图片（可选）
            </button>
            {image && <span className="file-name">{image.name}</span>}
            {image && (
              <button type="button" className="btn-clear" onClick={() => { setImage(null); setPreview(null); }}>
                ✕
              </button>
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={status === "loading"}>
            {status === "loading" ? "检索中..." : "提问"}
          </button>
        </div>

        {preview && (
          <div className="preview-box">
            <img src={preview} alt="预览" />
          </div>
        )}
      </form>

      {status === "error" && (
        <div className="alert alert-error">
          <strong>请求失败</strong>：{error}
        </div>
      )}

      {status === "loading" && (
        <div className="loading-indicator">
          <div className="spinner" />
          <span>正在检索文献并生成答案...</span>
        </div>
      )}

      {result && (
        <div className="result-area">
          <AnswerBox answer={result.answer} />
          <SourceList sources={result.sources} scores={result.scores} />
        </div>
      )}
    </div>
  );
}

function AnswerBox({ answer }: { answer: string }) {
  return (
    <div className="answer-box">
      <h3 className="section-title">{"📖"} 回答</h3>
      <p className="answer-text">{answer}</p>
    </div>
  );
}

function SourceList({ sources, scores }: { sources: Source[]; scores: number[] }) {
  if (!sources.length) return null;
  return (
    <details className="source-panel" open>
      <summary className="section-title">
        {"📄"} 参考来源（{sources.length} 条）
      </summary>
      <div className="source-list">
        {sources.map((s, i) => (
          <div key={s.chunk_id} className="source-item">
            <div className="source-meta">
              <span className="source-book">{s.book_title}</span>
              <span className="source-chapter">{s.chapter_title}</span>
              {scores[i] > 0 && (
                <span className="source-score">相关度 {(scores[i] * 100).toFixed(1)}%</span>
              )}
            </div>
            <p className="source-text">{s.text}</p>
          </div>
        ))}
      </div>
    </details>
  );
}
