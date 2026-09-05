import { useState } from "react";
import ContentsSelector from "./components/ContentsSelector";

export default function Dashboard() {
  const [keyword, setKeyword] = useState("");
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [selectedBlocksShow, setSelectedBlocksShow] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("ko");

  const handlePlayRadio = async () => {
    alert("라디오 스크립트 생성 시작!");
    setLoading(true); // 로딩 시작
    setScripts([]);
    try {
      const res = await fetch("http://localhost:8000/api/run-radio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blocks: selectedBlocks, keyword, language }),
      });

      if (res.ok) {
        const data = await res.json();
        setScripts(data.scripts);
        alert("라디오 스크립트 생성 완료!");
      } else {
        alert("실패했습니다.");
      }
    } catch (err) {
      console.error(err);
      alert("에러 발생!");
    } finally {
      setLoading(false); // 로딩 종료
    }
  };

  return (
    <main className=" mx-auto max-w-xl py-8">
      <h1 className="text-3xl font-bold">🎙️ AI 라디오 설정</h1>
      <section className="mt-6">
        <label>언어 선택:</label>
        <div className="mt-2 flex gap-4">
          <button
            onClick={() => setLanguage("ko")}
            className={`rounded-lg px-4 py-2 ${
              language === "ko"
                ? "bg-emerald-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            한국어
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`rounded-lg px-4 py-2 ${
              language === "en"
                ? "bg-emerald-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            English
          </button>
        </div>
      </section>

      <section className="mt-6">
        <label>오늘의 키워드:</label>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="예: 가을, 감성, 출근"
          className="mt-2 w-full rounded-lg border p-2"
        />
      </section>

      <section className="my-6">
        <label>콘텐츠 선택:</label>
        <ContentsSelector
          onChange={(names, labels) => {
            setSelectedBlocks(names); // API용
            setSelectedBlocksShow(labels); // UI용
          }}
        />
      </section>
      <hr />
      <section className="mt-6">
        <label>선택한 콘텐츠:</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {selectedBlocksShow.length > 0 ? (
            selectedBlocksShow.map((label, idx) => (
              <span
                key={idx}
                className="flex items-center gap-2 rounded-full border border-gray-200  bg-white px-4 py-2 text-gray-700 shadow-sm transition-all duration-200 hover:bg-gray-50"
              >
                {idx + 1}. {label}
              </span>
            ))
          ) : (
            <span className="text-gray-500">
              아직 선택한 콘텐츠가 없습니다.
            </span>
          )}
        </div>
      </section>
      <button
        onClick={handlePlayRadio}
        disabled={loading} // 로딩 중이면 비활성화
        className={`mt-6 w-full rounded-lg py-2 text-white ${
          loading ? "bg-gray-400" : "bg-emerald-600"
        }`}
      >
        {loading ? "생성 중..." : "스크립트 생성"}
      </button>

      {loading && (
        <div className="mt-4 flex justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent"></div>
          <span className="ml-2 text-emerald-600">
            라디오 스크립트를 생성 중입니다...
          </span>
        </div>
      )}

      {scripts.map((s, idx) => (
        <section key={idx} className="mt-4 rounded-lg border bg-gray-50 p-4">
          <h2 className="font-bold">{s.type.toUpperCase()}</h2>
          <p>{s.content}</p>
        </section>
      ))}
    </main>
  );
}
