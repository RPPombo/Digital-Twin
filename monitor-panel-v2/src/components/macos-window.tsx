/* 🎨 Mac window genérica */
export default function MacOSWindow({ title, children, small = false }: { title: string; children: React.ReactNode; small?: boolean }) {
  return (
    <div className={`bg-[#1e1e1e] rounded-xl shadow-xl border border-gray-800 overflow-hidden ${small ? "h-auto" : "w-auto"}`}>
      <div className="bg-[#2d2d2d] px-3 py-1.5 flex items-center gap-2 border-b border-gray-800">
        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
        <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <span className="ml-1 text-[11px] text-gray-400 font-medium">{title}</span>
      </div>
      <div className={`p-4 ${small ? "h-[200px]" : ""}`}>{children}</div>
    </div>
  )
}