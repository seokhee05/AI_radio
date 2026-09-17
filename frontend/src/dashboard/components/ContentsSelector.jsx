import { useState } from "react";
import ContentsBlock from "./ContentsBlock";

export default function ContentsSelector({ onChange }) {
  const [selectedBlocks, setSelectedBlocks] = useState([]);

  // 부모(Dashboard)로 값 전달
  const handleChange = (name, label) => {
    setSelectedBlocks((prev) => {
      let updated;
      
      // ✨ 핵심 로직: 이미 선택된 걸 또 누르면 빈 배열(해제), 아니면 방금 누른 것 1개만 덮어쓰기!
      if (prev.length > 0 && prev[0].name === name) {
        updated = [];
      } else {
        updated = [{ name, label }];
      }

      if (onChange) {
        const names = updated.map((b) => b.name); // API용
        const labels = updated.map((b) => b.label); // UI용
        onChange(names, labels);
      }
      return updated;
    });
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

      {/* 사연 */}
      <ContentsBlock
        name="story_main"
        label="🎙️ 사연 공감"
        active={selectedBlocks.some((b) => b.name === "story_main")}
        onClick={handleChange}
      />
      <ContentsBlock
        name="story_discussion"
        label="💬 사연 토론"
        active={selectedBlocks.some((b) => b.name === "story_discussion")}
        onClick={handleChange}
      />

      {/* 음악 */}
      <ContentsBlock
        name="music_history"
        label="🕰️ 음악 역사"
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
        label="🎤 아티스트 집중 조명"
        active={selectedBlocks.some((b) => b.name === "music_artist")}
        onClick={handleChange}
      />
      {/* 교통 */}
      <ContentsBlock 
        name="traffic" 
        label="🚗 교통 정보" 
        active={selectedBlocks.some((b) => b.name === "traffic")} 
        onClick={handleChange} 
      /> 
    </div>
  );
}