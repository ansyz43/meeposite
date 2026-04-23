export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="glass-card p-10 text-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-sky-500/[0.03] to-transparent pointer-events-none" />
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500/20 to-cyan-500/10 border border-sky-500/20 flex items-center justify-center mx-auto mb-5">
          <Icon size={28} className="text-sky-400" />
        </div>
        <h2 className="text-lg font-display font-semibold mb-2">{title}</h2>
        {description && <p className="text-white/40 mb-6 max-w-sm mx-auto text-sm">{description}</p>}
        {action}
      </div>
    </div>
  )
}
