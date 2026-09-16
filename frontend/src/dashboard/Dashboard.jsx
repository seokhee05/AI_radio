import { useState } from "react";
import ContentsSelector from "./components/ContentsSelector";

export default function Dashboard() {
  const [keyword, setKeyword] = useState("");
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [selectedBlocksShow, setSelectedBlocksShow] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("ko");

  // ✨ 알림 모달을 관리하는 통합 State
  const [modal, setModal] = useState({ 
    isOpen: false, 
    type: "success", // "success" | "error"
    title: "", 
    message: "" 
  });

  const handlePlayRadio = async () => {
    // ❌ alert("라디오 스크립트 생성 시작!"); -> UX를 위해 제거 (로딩 애니메이션이 대신함)
    setLoading(true);
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
        // ✨ 성공 모달 띄우기
        setModal({
          isOpen: true,
          type: "success",
          title: "스크립트 생성 완료",
          message: "AI 라디오 스크립트가 성공적으로 생성되었습니다!"
        });
      } else {
        // ✨ 실패 모달 띄우기
        setModal({
          isOpen: true,
          type: "error",
          title: "생성 실패",
          message: "스크립트 생성에 실패했습니다. 잠시 후 다시 시도해주세요."
        });
      }
    } catch (err) {
      console.error(err);
      // ✨ 에러 모달 띄우기
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
            {/* 2. 키워드 입력 섹션 */}
            <section>
              <label className="block text-base font-bold text-slate-700 mb-3">
                오늘의 키워드
              </label>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="예: 가을, 감성, 출근"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-slate-900 transition-all duration-200 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-100"
              />
            </section>

            {/* 3. 콘텐츠 선택 섹션 */}
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
                  }}
                />
              </div>
            </section>

            {/* 4. 선택된 콘텐츠 확인 섹션 */}
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

          {/* 5. 생성 버튼 */}
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

          {/* 로딩 표시 */}
          {loading && (
            <div className="mt-6 flex flex-col items-center justify-center space-y-3 rounded-xl bg-blue-50 p-6">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
              <span className="font-medium text-blue-700">
                AI가 스크립트를 생성하고 있습니다...
              </span>
            </div>
          )}
        </main>

        {/* 오른쪽: 생성된 스크립트 결과 패널 */}
        {scripts.length > 0 && (
          <aside className="w-full flex-1 rounded-2xl bg-white p-8 xl:p-10 shadow-xl border border-slate-100 animate-[fadeIn_0.5s_ease-in-out]">
            <h2 className="text-2xl font-bold text-slate-900 mb-8 flex items-center gap-2 border-b border-slate-100 pb-4">
              📝 생성된 스크립트
            </h2>
            <div className="space-y-6">
              {scripts.map((s, idx) => (
                <section
                  key={idx}
                  className="rounded-2xl border border-slate-100 bg-slate-50 p-6 shadow-sm transition-all hover:shadow-md hover:border-slate-200"
                >
                  <div className="mb-4 flex items-center gap-2">
                    <span className="rounded-lg bg-blue-100 px-3 py-1.5 text-xs font-bold tracking-wider text-blue-700 uppercase">
                      {s.type}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-left text-[15.5px] leading-relaxed text-slate-700 tracking-wide break-keep">
                    {s.content}
                  </p>
                </section>
              ))}
            </div>
          </aside>
        )}
      </div>

      {/* ✨ 결과 알림 커스텀 모달 (성공/실패 동적 렌더링) */}
      {modal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm animate-[fadeIn_0.2s_ease-in-out]">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              {/* 성공일 때는 초록색 체크, 에러일 때는 빨간색 경고 아이콘 */}
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