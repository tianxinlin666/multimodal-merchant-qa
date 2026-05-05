/** API 客户端 —— 与 FastAPI 后端通信。 */

import axios from "axios";

const api = axios.create({
  baseURL: "/",
  timeout: 60000,
});

// ---- 类型定义 ----

export interface Source {
  chunk_id: string;
  book_title: string;
  chapter_title: string;
  text: string;
}

export interface QAResponse {
  answer: string;
  sources: Source[];
  scores: number[];
}

export interface UploadResponse {
  filename: string;
  content_type: string;
  size: number;
  base64: string;
}

// ---- API 方法 ----

export async function askQuestion(
  question: string,
  image?: File
): Promise<QAResponse> {
  const form = new FormData();
  form.append("question", question);
  if (image) {
    form.append("image", image);
  }
  const { data } = await api.post<QAResponse>("/api/qa", form);
  return data;
}

export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("image", file);
  const { data } = await api.post<UploadResponse>("/api/upload/image", form);
  return data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const { data } = await api.get<{ status: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}
