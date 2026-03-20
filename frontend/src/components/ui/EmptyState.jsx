export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="glass-card p-10 text-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/[0.03] to-transparent pointer-events-none" />
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-5">
          <Icon size={28} className="text-emerald-400" />
        </div>
        <h2 className="text-lg font-display font-semibold mb-2">{title}</h2>
        {description && <p className="text-white/40 mb-6 max-w-sm mx-auto text-sm">{description}</p>}
        {action}
      </div>
    </div>
  )
}
