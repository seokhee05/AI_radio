import { useState, useEffect, useRef } from "react";
import ContentsSelector from "./components/ContentsSelector";

const BACKEND_URL = "http://localhost:8000";

export default function Dashboard() {
  const [keyword, setKeyword] = useState("");
  const [selectedBlocks, setSelectedBlocks] = useState([]);
  const [selectedBlocksShow, setSelectedBlocksShow] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(false);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);
  const bgmRef = useRef(null);

  const [modal, setModal] = useState({
    isOpen: false,
    type: "success", 
    title: "",
    message: ""
  });

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

  useEffect(() => {
    const bgm = new Audio();
    bgm.volume = 0.12;
    bgm.loop = true;

    bgmRef.current = bgm;

    return () => {
      bgm.pause();
      bgm.removeAttribute("src");
      bgmRef.current = null;
    };
  }, []);


  const loadJamendoBGM = async () => {
    try {
      // 뉴스 및 교통 카테고리
      const newsTrafficBlocks = [
        "headline",
        "deep",
        "busan",
        "traffic",
      ];

      // 선택한 카테고리 확인
      const isNewsTraffic = selectedBlocks.some((block) =>
        newsTrafficBlocks.includes(block)
      );

      // 뉴스·교통 = lofi
      // 사연·음악 = piano
      const mood = isNewsTraffic ? "lofi" : "piano";

      console.log("🎵 선택된 BGM:", mood);

      const response = await fetch(
        `${BACKEND_URL}/api/bgm?mood=${mood}`
      );

      if (!response.ok) {
        throw new Error("Jamendo BGM 검색 실패");
      }

      const data = await response.json();

      if (data.bgm?.audio && bgmRef.current) {
        bgmRef.current.pause();
        bgmRef.current.src = data.bgm.audio;
        bgmRef.current.volume = isNewsTraffic ? 0.25 : 0.4;
        bgmRef.current.loop = true;
        bgmRef.current.load();

        console.log("✅ BGM 준비 완료:", data.bgm.title);
      } else {
        console.warn("⚠️ BGM을 불러오지 못했습니다.");
      }
    } catch (error) {
      console.error("❌ BGM 로드 오류:", error);
    }
  };


  const handlePlayRadio = async () => {
    setLoading(true);
    setScripts([]);
    setIsPlaying(false);
    setCurrentIndex(0);

    try {
      const res = await fetch(`${BACKEND_URL}/api/run-radio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blocks: selectedBlocks, keyword, language: "ko" }),
      });

      if (res.ok) {
        const data = await res.json();
        const fetchedScripts = data.scripts || [];
        setScripts(fetchedScripts);
        await loadJamendoBGM();

        setModal({
          isOpen: true,
          type: "success",
          title: "스크립트 및 음성 생성 완료",
          message: "AI 라디오 방송 준비가 완료되었습니다. 우측의 '방송 시작' 버튼을 눌러 들어보세요!"
        });

        if (fetchedScripts.length > 0 && fetchedScripts[0].audio_url) {
          setCurrentIndex(0);
          if (audioRef.current) {
            audioRef.current.src = `${BACKEND_URL}${fetchedScripts[0].audio_url}`;
          }
        }
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

  

const handleAudioEnded = () => {
  const nextIndex = currentIndex + 1;

  if (nextIndex < scripts.length) {
    setCurrentIndex(nextIndex);

    const nextAudioUrl = scripts[nextIndex]?.audio_url;

    if (nextAudioUrl && audioRef.current) {
      audioRef.current.src = new URL(
        nextAudioUrl,
        BACKEND_URL
      ).href;

      audioRef.current.play().catch(console.error);

      // 다음 DJ 멘트에서도 BGM 계속 재생
      if (bgmRef.current?.src) {
        bgmRef.current.play().catch(console.error);
      }
    }
  } else {
    // 방송이 완전히 끝났을 때만 BGM 종료
    bgmRef.current?.pause();
    setIsPlaying(false);
  }
};


  const isHeadline = selectedBlocks.includes("headline");
  const isBusan = selectedBlocks.includes("busan");
  const isTraffic = selectedBlocks.includes("traffic");
  const isKeywordDisabled = isHeadline || isBusan || isTraffic;
  const isStory = selectedBlocks.includes("story_main");
  const isDeep = selectedBlocks.includes("deep");
  const isMusicStory = selectedBlocks.includes("music_story");
  const isMusicTrend = selectedBlocks.includes("music_trend");
  const isMusicArtist = selectedBlocks.includes("music_artist");

  let keywordPlaceholder = "먼저 아래에서 콘텐츠 종류를 선택해 주세요.";
  if (isHeadline) {
    keywordPlaceholder = "헤드라인 뉴스는 키워드를 입력할 수 없습니다.";
  } else if (isBusan) {
    keywordPlaceholder = "부산 뉴스는 키워드를 입력할 수 없습니다.";
  } else if (isTraffic) {
    keywordPlaceholder = "교통 정보는 부산 지역으로 고정되어 생성됩니다";
  } else if (isStory) {
    keywordPlaceholder = "ex. 아르바이트, 가족, 병원";
  } else if (isDeep) {
    keywordPlaceholder = "ex. 인공지능, 경제";
  } else if (isMusicStory) {
    keywordPlaceholder = "ex. 힙합, R&B, 발라드";
  } else if (isMusicTrend) {
    keywordPlaceholder = "ex. K-POP, 밴드";
  } else if (isMusicArtist) {
    keywordPlaceholder = "ex. 아이유, 방탄소년단";
  }

  const renderScriptContent = (item) => {
    if (typeof item === "string") return item;

    if (Array.isArray(item)) {
      return item.map((sub) => renderScriptContent(sub)).join("\n\n");
    }

    if (typeof item === "object" && item !== null) {
      if (item.content) return renderScriptContent(item.content);
      if (item.text) return renderScriptContent(item.text);
      return Object.values(item).map((val) => renderScriptContent(val)).join("\n\n");
    }

    return String(item || "");
  };

  const handleDeleteScript = (targetIdx) => {
    const updatedScripts = scripts.filter((_, i) => i !== targetIdx);

    if (isPlaying && targetIdx === currentIndex) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setIsPlaying(false);

      if (updatedScripts.length > 0) {
        const nextIdx = Math.min(targetIdx, updatedScripts.length - 1);
        setCurrentIndex(nextIdx);
        if (audioRef.current && updatedScripts[nextIdx]?.audio_url) {
          audioRef.current.src = `${BACKEND_URL}${updatedScripts[nextIdx].audio_url}`;
        }
      } else {
        setCurrentIndex(0);
        if (audioRef.current) audioRef.current.removeAttribute("src");
      }
    } 
    else if (targetIdx < currentIndex) {
      const newIndex = Math.max(0, currentIndex - 1);
      setCurrentIndex(newIndex);
    }

    setScripts(updatedScripts);
  };

  const togglePlayPause = () => {
    if (!audioRef.current || scripts.length === 0) return;

    if (isPlaying) {
      audioRef.current.pause();
      bgmRef.current?.pause();

      setIsPlaying(false);
    } else {
      const currentAudioUrl = scripts[currentIndex]?.audio_url;

      if (!currentAudioUrl) {
        console.warn("재생할 오디오 URL이 없습니다.");
        return;
      }

      const fullUrl = new URL(currentAudioUrl, BACKEND_URL).href;

      if (audioRef.current.src !== fullUrl) {
        audioRef.current.src = fullUrl;
      }

      audioRef.current.play().then(() => {
        setIsPlaying(true);

        if (
          scripts[currentIndex]?.type !== "music_song" &&
          bgmRef.current?.src
        ) {
          bgmRef.current.play().catch((err) => {
            console.error("BGM 재생 오류:", err);
          });
        }
      })
      .catch((err) => {
        console.error("오디오 재생 오류:", err);
        setIsPlaying(false);
      });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 relative">
      <audio ref={audioRef} onEnded={handleAudioEnded} className="hidden" />

      <div
        className={`mx-auto flex flex-col xl:flex-row gap-8 items-start transition-all duration-500 ease-in-out ${scripts.length > 0 ? "w-full max-w-[1700px]" : "max-w-2xl"
          }`}
      >
        <main className="w-full max-w-2xl shrink-0 rounded-2xl bg-white p-8 shadow-xl border border-slate-100 transition-all xl:sticky xl:top-12">
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
                className={`w-full rounded-xl border p-3.5 transition-all duration-200 ${isKeywordDisabled
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

                    if (names.includes("headline") || names.includes("busan")) {
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
              className={`w-full rounded-xl py-4 text-lg font-bold text-white transition-all duration-200 ${loading || selectedBlocks.length === 0
                  ? "cursor-not-allowed bg-slate-300"
                  : "bg-blue-600 shadow-md hover:bg-blue-700 hover:shadow-lg active:scale-[0.98]"
                }`}
            >
              {loading ? "스크립트 및 음성 생성 중..." : "스크립트 생성하기"}
            </button>
          </div>

          {loading && (
            <div className="mt-6 flex flex-col items-center justify-center space-y-3 rounded-xl bg-blue-50 p-6">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
              <span className="font-medium text-blue-700">
                AI가 대본 및 음성을 생성하고 있습니다...
              </span>
            </div>
          )}
        </main>

        {scripts.length > 0 && (
          <aside className="w-full flex-1 rounded-2xl bg-white p-8 xl:p-10 shadow-xl border border-slate-100 animate-[fadeIn_0.5s_ease-in-out]">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-8">
              <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                📝 생성된 스크립트
              </h2>

              <button
                onClick={togglePlayPause}
                className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white transition-all active:scale-[0.98] ${isPlaying
                    ? "bg-amber-500 hover:bg-amber-600 shadow-md"
                    : "bg-emerald-600 hover:bg-emerald-700 shadow-md"
                  }`}
              >
                {isPlaying ? (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                      <path fillRule="evenodd" d="M6.75 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75zm9 0a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75z" clipRule="evenodd" />
                    </svg>
                    방송 일시정지
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                      <path fillRule="evenodd" d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z" clipRule="evenodd" />
                    </svg>
                    방송 시작 / 이어서 듣기
                  </>
                )}
              </button>
            </div>

            <div className="space-y-6">
              {scripts.map((s, idx) => {
                const isCurrentPlaying = isPlaying && idx === currentIndex;

                return (
                  <section
                    key={idx}
                    className={`relative rounded-2xl border p-6 transition-all duration-300 ${isCurrentPlaying
                        ? "border-blue-500 bg-blue-50/60 shadow-md ring-2 ring-blue-200"
                        : "border-slate-100 bg-slate-50 hover:border-slate-200"
                      }`}
                  >
                    {(s.type?.toLowerCase() === "opening" || s.type?.toLowerCase() === "closing") && (
                      <button
                        onClick={() => handleDeleteScript(idx)}
                        className="absolute top-5 right-5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-500 transition hover:bg-red-100 hover:border-red-400"
                      >
                        삭제
                      </button>
                    )}

                    <div className="mb-4 flex items-center gap-2">
                      <span className={`rounded-lg px-3 py-1.5 text-xs font-bold tracking-wider uppercase ${isCurrentPlaying ? "bg-blue-600 text-white" : "bg-blue-100 text-blue-700"
                        }`}>
                        {typeof s.type === "object" && s.type !== null
                          ? s.type.name || JSON.stringify(s.type)
                          : String(s.type || "SCRIPT")}
                      </span>

                      {isCurrentPlaying && (
                        <span className="flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700 animate-pulse">
                          <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                          🔊 라이브 재생 중
                        </span>
                      )}
                    </div>

                    <p className="whitespace-pre-wrap text-left text-[15.5px] leading-relaxed text-slate-700 tracking-wide break-keep">
                      {renderScriptContent(s)}
                    </p>
                  </section>
                );
              })}
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
              className={`w-full rounded-xl py-3.5 font-bold text-white transition-all active:scale-[0.98] ${modal.type === "success"
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