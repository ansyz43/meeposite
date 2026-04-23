export default function StatCard({ icon: Icon, label, value, color = 'emerald', subtitle }) {
  const colors = {
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    emerald: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    teal: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  }
  return (
    <div className="stat-card p-5 group hover:border-white/[0.1] transition-all duration-300">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${colors[color]} transition-shadow duration-300 group-hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]`}>
          <Icon size={20} />
        </div>
        <span className="text-white/40 text-sm">{label}</span>
      </div>
      <div className="text-2xl font-display font-bold">{value}</div>
      {subtitle && <div className="text-xs text-white/30 mt-1">{subtitle}</div>}
    </div>
  )
}
