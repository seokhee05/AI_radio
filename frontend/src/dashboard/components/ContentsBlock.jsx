export default function ContentsBlock({ name, label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(name, label)}
      className={`
        flex items-center gap-2 rounded-full px-4 py-2  transition-all duration-200
        ${active ? "border border-gray-400 bg-gray-100 shadow-md" : "border border-gray-200 bg-white text-gray-700 shadow-sm hover:bg-gray-50"}
      `}
    >
      {label}
    </button>
  );
}
