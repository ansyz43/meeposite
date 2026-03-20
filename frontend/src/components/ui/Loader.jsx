export default function Loader({ text = 'Загрузка...' }) {
  return (
    <div className="flex items-center gap-3 text-white/40">
      <div className="w-5 h-5 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
      {text}
    </div>
  )
}
