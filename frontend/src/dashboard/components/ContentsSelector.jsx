import { useState } from "react";
import ContentsBlock from "./ContentsBlock";

export default function ContentSelector({ onChange }) {
  const [selectedBlocks, setSelectedBlocks] = useState([]);

  // 부모(Dashboard)로 값 전달
  const handleChange = (name, label) => {
    // 1. 상태 업데이트할 값을 미리 계산
    const isSame = selectedBlocks.length > 0 && selectedBlocks[0].name === name;
    const updated = isSame ? [] : [{ name, label }];

    // 2. 내부 상태 업데이트
    setSelectedBlocks(updated);

    // 3. 부모 컴포넌트의 렌더링 충돌을 막기 위해 상태 변경 외의 작업은 바깥에서 수행
    if (onChange) {
      const names = updated.map((b) => b.name); // API용
      const labels = updated.map((b) => b.label); // UI용
      onChange(names, labels);
    }
  };

  return (
    <div className="space-y-6">
      {/* 📰 뉴스 카테고리 */}
      <div className="space-y-2">
        <h1 className="text-s text-left font-bold text-slate-400 uppercase tracking-wider">
          [📑 뉴스 카테고리]
        </h1>
        <div className="flex flex-wrap gap-2">
          <ContentsBlock
            name="headline"
            label="📰 헤드라인 뉴스"
            active={selectedBlocks.some((b) => b.name === "headline")}
            onClick={handleChange}
          />
          <ContentsBlock
            name="deep"
            label="🔎 심층 뉴스"
            active={selectedBlocks.some((b) => b.name === "deep")}
            onClick={handleChange}
          />
          <ContentsBlock
            name="busan"
            label="🗞️ 부산 뉴스"
            active={selectedBlocks.some((b) => b.name === "busan")}
            onClick={handleChange}
          />
        </div>
      </div>

      {/* 💌 사연 카테고리 */}
      <div className="space-y-2">
        <h1 className="text-s text-left font-bold text-slate-400 uppercase tracking-wider">
          [💌 사연 카테고리]
        </h1>
        <div className="flex flex-wrap gap-2">
          <ContentsBlock
            name="story_main"
            label="🎙️ 사연 토크"
            active={selectedBlocks.some((b) => b.name === "story_main")}
            onClick={handleChange}
          />
        </div>
      </div>

      {/* 🎵 음악 카테고리 */}
      <div className="space-y-2">
        <h1 className="text-s text-left font-bold text-slate-400 uppercase tracking-wider">
          [🎵 음악 카테고리]
        </h1>
        <div className="flex flex-wrap gap-2">
          <ContentsBlock
            name="music_story"
            label="🎧 장르&음악 이야기"
            active={selectedBlocks.some((b) => b.name === "music_story")}
            onClick={handleChange}
          />
          <ContentsBlock
            name="music_trend"
            label="📊 최신 음악 트렌드"
            active={selectedBlocks.some((b) => b.name === "music_trend")}
            onClick={handleChange}
          />
          <ContentsBlock
            name="music_artist"
            label="🌟 오늘의 아티스트"
            active={selectedBlocks.some((b) => b.name === "music_artist")}
            onClick={handleChange}
          />
        </div>
      </div>

      {/* 🚗 교통 카테고리 */}
      <div className="space-y-2">
        <h1 className="text-s text-left font-bold text-slate-400 uppercase tracking-wider">
          [ 🚦교통 카테고리]
        </h1>
        <div className="flex flex-wrap gap-2">
          <ContentsBlock
            name="traffic"
            label="🚗교통 정보"
            active={selectedBlocks.some((b) => b.name === "traffic")}
            onClick={handleChange}
          />
        </div>
      </div>
    </div>
  );
}