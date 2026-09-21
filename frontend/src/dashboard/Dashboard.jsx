import { useState, useEffect } from "react";
import ContentsSelector from "./components/ContentsSelector";

export default function Dashboard() {
  const [keyword, setKeyword] = useState("");
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [selectedBlocksShow, setSelectedBlocksShow] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(false);

  // ✨ 알림 모달을 관리하는 통합 State
  const [modal, setModal] = useState({
    isOpen: false,
    type: "success", // "success" | "error"
    title: "",
    message: ""
  });

  // ✨ 모달이 열려 있을 때 Enter 키를 누르면 모달 닫기
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Enter" && modal.isOpen) {
        setModal((prev) => ({ ...prev, isOpen: false }));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [modal.isOpen]);

  const handlePlayRadio = async () => {
    setLoading(true);
    setScripts([]);

    try {
      const res = await fetch("http://localhost:8000/api/run-radio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blocks: selectedBlocks, keyword }),
      });

      if (res.ok) {
        const data = await res.json();
        setScripts(data.scripts);
        setModal({
          isOpen: true,
          type: "success",
          title: "스크립트 생성 완료",
          message: "AI 라디오 스크립트가 성공적으로 생성되었습니다!"
        });
      } else {
        setModal({
          isOpen: true,
          type: "error",
          title: "생성 실패",
          message: "스크립트 생성에 실패했습니다. 잠시 후 다시 시도해주세요."
        });
      }
    } catch (err) {
      console.error(err);
      setModal({
        isOpen: true,
        type: "error",
        title: "서버 연결 오류",
        message: "백엔드 서버와 통신하는 중 문제가 발생했습니다."
      });
    } finally {
      setLoading(false);
    }
  };

  // ✨ 헤드라인(headline)이나 추가 뉴스(current) 선택 시 키워드 입력 제한
  const isHeadline = selectedBlocks.includes("headline");
  const isCurrent = selectedBlocks.includes("current");
  const isKeywordDisabled = isHeadline || isCurrent;

  // ✨ 선택된 콘텐츠에 따른 맞춤형 placeholder 결정
  let keywordPlaceholder = "예: 인공지능, 가족여행, 출근";
  if (isHeadline) {
    keywordPlaceholder = "헤드라인 뉴스는 키워드를 입력할 수 없습니다.";
  } else if (isCurrent) {
    keywordPlaceholder = "추가 뉴스는 키워드를 입력할 수 없습니다.";
  }

  // ✨ 객체가 중첩되어 들어와도 안전하게 문자열(텍스트)로 추출하는 헬퍼 함수
  // ✨ 배열, 객체, 중첩 구조가 와도 텍스트만 쏙 빼내는 강력한 헬퍼 함수
  const renderScriptContent = (item) => {
    if (typeof item === "string") return item;
    
    // 만약 배열 형태라면 내부 아이템들을 각각 풀어서 합쳐줌
    if (Array.isArray(item)) {
      return item.map((sub) => renderScriptContent(sub)).join("\n\n");
    }
    
    // 객체 형태라면 content 속성을 우선적으로 찾고, 없으면 재귀 탐색
    if (typeof item === "object" && item !== null) {
      if (item.content) {
        return renderScriptContent(item.content);
      }
      // 내부에 text나 message 같은 다른 키가 있을 경우 대비
      if (item.text) {
        return renderScriptContent(item.text);
      }
      return Object.values(item)
        .map((val) => renderScriptContent(val))
        .join("\n\n");
    }
    
    return String(item || "");
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 relative">
      <div
        className={`mx-auto flex flex-col xl:flex-row gap-8 items-start transition-all duration-500 ease-in-out ${
          scripts.length > 0 ? "w-full max-w-[1700px]" : "max-w-2xl"
        }`}
      >
        <main
          className="w-full max-w-2xl shrink-0 rounded-2xl bg-white p-8 shadow-xl border border-slate-100 transition-all xl:sticky xl:top-12"
        >
          <header className="mb-8 border-b border-slate-100 pb-6">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
              🎙️ AI 라디오 설정
            </h1>
            <p className="mt-2 text-sm text-slate-500 leading-relaxed">
              키워드와 콘텐츠를 선택하여 맞춤형 스크립트를 생성해보세요.
            </p>
          </header>

          <div className="space-y-8">
            <section>
              <div className="mb-3">
                <label className="block text-base font-bold text-slate-700">
                  오늘의 키워드
                </label>
                <p className="mt-1 text-xs sm:text-sm text-slate-400 leading-relaxed">
                  키워드를 구체적으로 입력할수록 더 완성도 높은 스크립트가 생성됩니다.
                </p>
              </div>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                disabled={isKeywordDisabled}
                placeholder={keywordPlaceholder}
                className={`w-full rounded-xl border p-3.5 transition-all duration-200 ${
                  isKeywordDisabled
                    ? "cursor-not-allowed border-slate-200 bg-slate-200 text-slate-400 placeholder:text-slate-400"
                    : "border-slate-200 bg-slate-50 text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-100"
                }`}
              />
            </section>

            <section>
              <div className="mb-3">
                <label className="block text-base font-bold text-slate-700">
                  콘텐츠 선택
                </label>
                <p className="mt-1 text-sm text-slate-500">
                  원하는 콘텐츠를 <span className="font-semibold text-blue-600">하나만</span> 선택해주세요.
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <ContentsSelector
                  onChange={(names, labels) => {
                    setSelectedBlocks(names);
                    setSelectedBlocksShow(labels);

                    if (names.includes("headline") || names.includes("current")) {
                      setKeyword("");
                    }
                  }}
                />
              </div>
            </section>

            <section>
              <label className="block text-base font-bold text-slate-700 mb-3">
                선택된 콘텐츠
              </label>
              <div className="flex flex-wrap gap-2 min-h-[44px] items-center rounded-xl border border-slate-200 bg-slate-50 p-3">
                {selectedBlocksShow.length > 0 ? (
                  <span className="flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 shadow-sm">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                        <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                      </svg>
                    </span>
                    {selectedBlocksShow[0]}
                  </span>
                ) : (
                  <span className="text-sm text-slate-400 pl-2">
                    콘텐츠를 선택해주세요.
                  </span>
                )}
              </div>
            </section>
          </div>

          <div className="mt-10">
            <button
              onClick={handlePlayRadio}
              disabled={loading || selectedBlocks.length === 0}
              className={`w-full rounded-xl py-4 text-lg font-bold text-white transition-all duration-200 ${
                loading || selectedBlocks.length === 0
                  ? "cursor-not-allowed bg-slate-300"
                  : "bg-blue-600 shadow-md hover:bg-blue-700 hover:shadow-lg active:scale-[0.98]"
              }`}
            >
              {loading ? "스크립트를 생성하는 중..." : "스크립트 생성하기"}
            </button>
          </div>

          {loading && (
            <div className="mt-6 flex flex-col items-center justify-center space-y-3 rounded-xl bg-blue-50 p-6">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
              <span className="font-medium text-blue-700">
                AI가 스크립트를 생성하고 있습니다...
              </span>
            </div>
          )}
        </main>

        {scripts.length > 0 && (
          <aside className="w-full flex-1 rounded-2xl bg-white p-8 xl:p-10 shadow-xl border border-slate-100 animate-[fadeIn_0.5s_ease-in-out]">
            <h2 className="text-2xl font-bold text-slate-900 mb-8 flex items-center gap-2 border-b border-slate-100 pb-4">
              📝 생성된 스크립트
            </h2>
            <div className="space-y-6">
              {scripts.map((s, idx) => (
                <section
                  key={idx}
                  className="relative rounded-2xl border border-slate-100 bg-slate-50 p-6 shadow-sm transition-all hover:shadow-md hover:border-slate-200"
                >
                  {(s.type?.toLowerCase() === "opening" || s.type?.toLowerCase() === "closing") && (
                    <button
                      onClick={() =>
                        setScripts((prev) => prev.filter((_, i) => i !== idx))
                      }
                      className="absolute top-5 right-5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-500 transition hover:bg-red-100 hover:border-red-400"
                    >
                      삭제
                    </button>
                  )}

                  <div className="mb-4 flex items-center gap-2">
                    <span className="rounded-lg bg-blue-100 px-3 py-1.5 text-xs font-bold tracking-wider text-blue-700 uppercase">
                      {typeof s.type === "object" && s.type !== null ? (s.type.name || JSON.stringify(s.type)) : String(s.type || "SCRIPT")}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-left text-[15.5px] leading-relaxed text-slate-700 tracking-wide break-keep">
                    {renderScriptContent(s)}
                  </p>
                </section>
              ))}
            </div>
          </aside>
        )}
      </div>

      {modal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm animate-[fadeIn_0.2s_ease-in-out]">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              {modal.type === "success" ? (
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="h-6 w-6 text-emerald-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </span>
              ) : (
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-100">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-6 w-6 text-rose-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </span>
              )}
              <h3 className="text-lg font-bold text-slate-900">{modal.title}</h3>
            </div>

            <p className="mb-6 text-[15px] text-slate-600 leading-relaxed">
              {modal.message}
            </p>

            <button
              onClick={() => setModal({ ...modal, isOpen: false })}
              className={`w-full rounded-xl py-3.5 font-bold text-white transition-all active:scale-[0.98] ${
                modal.type === "success"
                  ? "bg-emerald-600 hover:bg-emerald-700"
                  : "bg-rose-600 hover:bg-rose-700"
              }`}
            >
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  );
}