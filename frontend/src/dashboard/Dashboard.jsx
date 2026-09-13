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
    setLoading(true); // 로딩 시작 애니메이션 켜기
    setScripts([]);

    // 실제 백엔드 요청 대신 setTimeout으로 1.5초 딜레이를 주어 로딩을 시뮬레이션함
    setTimeout(() => {
      // 가짜(Mock) 스크립트 데이터
      const mockData = [
        { 
          type: "opening", 
          content: "안녕하세요! 오늘 하루도 정말 고생 많으셨습니다. 여러분의 지친 일상을 달래줄 AI 라디오, 지금 바로 시작합니다." 
        },
        { 
          type: "story", 
          content: "오늘의 첫 번째 사연입니다. 익명의 청취자님이 보내주신 이야기인데요, 요즘 날씨가 부쩍 쌀쌀해지면서 출근길이 너무 힘들다고 하시네요.\n이럴 때일수록 따뜻한 커피 한 잔의 여유가 필요하겠죠?" 
        },
        { 
          type: "music", 
          content: "🎵 (잔잔한 어쿠스틱 기타 음악 재생)" 
        },
        { 
          type: "closing", 
          content: "오늘 준비한 사연과 음악은 여기까지입니다. 내일도 이 시간에 찾아오겠습니다. 편안한 밤 보내세요!" 
        }
      ];

      setScripts(mockData); // 생성된(가짜) 데이터 적용
      setLoading(false); // 로딩 종료 애니메이션 끄기
    }, 1500); 
  };

  return (
    // 배경색을 옅은 회색으로 깔고 가운데 정렬
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6">
      <main className="mx-auto max-w-2xl rounded-2xl bg-white p-8 shadow-xl border border-gray-100">
        
        <header className="mb-8 border-b border-gray-100 pb-6">
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            🎙️ AI 라디오 설정
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            키워드와 콘텐츠를 선택하여 맞춤형 라디오 대본을 생성해보세요.
          </p>
        </header>

        <div className="space-y-8">
          {/* 1. 언어 선택 섹션 */}
          <section>
            <label className="block text-sm font-bold text-gray-700 mb-3">
              언어 선택
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setLanguage("ko")}
                className={`flex-1 rounded-xl py-3 font-medium transition-all duration-200 ${
                  language === "ko"
                    ? "bg-emerald-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                한국어
              </button>
              <button
                onClick={() => setLanguage("en")}
                className={`flex-1 rounded-xl py-3 font-medium transition-all duration-200 ${
                  language === "en"
                    ? "bg-emerald-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                English
              </button>
            </div>
          </section>

          {/* 2. 키워드 입력 섹션 */}
          <section>
            <label className="block text-sm font-bold text-gray-700 mb-3">
              오늘의 키워드
            </label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="예: 가을, 감성, 출근"
              className="w-full rounded-xl border border-gray-300 bg-gray-50 p-3.5 text-gray-900 transition-all duration-200 focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-200"
            />
          </section>

          {/* 3. 콘텐츠 선택 섹션 */}
          <section>
            <label className="block text-sm font-bold text-gray-700 mb-3">
              콘텐츠 선택
            </label>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
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
            <label className="block text-sm font-bold text-gray-700 mb-3">
              선택된 콘텐츠 순서
            </label>
            <div className="flex flex-wrap gap-2 min-h-[44px] items-center rounded-xl border border-gray-100 bg-gray-50 p-3">
              {selectedBlocksShow.length > 0 ? (
                selectedBlocksShow.map((label, idx) => (
                  <span
                    key={idx}
                    className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3.5 py-1.5 text-sm font-medium text-emerald-800"
                  >
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-[10px] text-white">
                      {idx + 1}
                    </span>
                    {label}
                  </span>
                ))
              ) : (
                <span className="text-sm text-gray-400 pl-2">
                  아직 선택한 콘텐츠가 없습니다.
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
                ? "cursor-not-allowed bg-gray-300"
                : "bg-emerald-600 shadow-lg hover:bg-emerald-700 hover:shadow-xl active:scale-[0.98]"
            }`}
          >
            {loading ? "스크립트 생성 중..." : "스크립트 생성하기"}
          </button>
        </div>

        {/* 로딩 표시 */}
        {loading && (
          <div className="mt-6 flex flex-col items-center justify-center space-y-3 rounded-xl bg-emerald-50 p-6">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent"></div>
            <span className="font-medium text-emerald-700">
              AI가 멋진 라디오 대본을 작성하고 있습니다...
            </span>
          </div>
        )}

        {/* 결과 출력부 */}
        {scripts.length > 0 && (
          <div className="mt-10 space-y-4 border-t border-gray-200 pt-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">📝 생성된 대본</h2>
            {scripts.map((s, idx) => (
              <section 
                key={idx} 
                className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:shadow-md"
              >
                <div className="mb-3 flex items-center gap-2">
                  <span className="rounded-lg bg-gray-800 px-2.5 py-1 text-xs font-bold tracking-wider text-white">
                    {s.type.toUpperCase()}
                  </span>
                </div>
                <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
                  {s.content}
                </p>
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}