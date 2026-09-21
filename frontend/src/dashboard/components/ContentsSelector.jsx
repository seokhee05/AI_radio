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
    <div className="mt-2 flex flex-wrap gap-2">
      {/* 뉴스 */}
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
        name="current"
        label="🗞️ 추가 뉴스"
        active={selectedBlocks.some((b) => b.name === "current")}
        onClick={handleChange}
      />

      {/* 사연 (공감과 토론을 하나의 세트로 통합) */}
      <ContentsBlock
        name="story_main"
        label="🎙️ 사연 토크"
        active={selectedBlocks.some((b) => b.name === "story_main")}
        onClick={handleChange}
      />

      {/* 음악 */}
      <ContentsBlock
        name="music_history"
        label="📀 음악 역사"
        active={selectedBlocks.some((b) => b.name === "music_history")}
        onClick={handleChange}
      />
      <ContentsBlock
        name="music_trend"
        label="📊 최신 음악 트렌드"
        active={selectedBlocks.some((b) => b.name === "music_trend")}
        onClick={handleChange}
      />
      <ContentsBlock
        name="music_genre"
        label="🎧 장르 탐험"
        active={selectedBlocks.some((b) => b.name === "music_genre")}
        onClick={handleChange}
      />
      <ContentsBlock
        name="music_artist"
        label="🌟 아티스트 집중 조명"
        active={selectedBlocks.some((b) => b.name === "music_artist")}
        onClick={handleChange}
      />
    </div>
  );
}