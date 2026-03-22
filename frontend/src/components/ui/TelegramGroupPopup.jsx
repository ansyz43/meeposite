import { X, ExternalLink, Users } from 'lucide-react'

const TG_GROUP_LINK = 'https://t.me/+lb0Q34TaeDgyNGZi'

export default function TelegramGroupPopup({ open, onClose }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="relative w-full max-w-md bg-[#0C1219] border border-white/[0.08] rounded-2xl overflow-hidden animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top accent */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-500 to-transparent" />

        {/* Close */}
        <button 
          onClick={onClose} 
          className="absolute top-4 right-4 p-1 text-white/30 hover:text-white transition-colors cursor-pointer z-10"
        >
          <X size={18} />
        </button>

        <div className="p-8 text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-5 shadow-glow">
            <Users size={28} className="text-emerald-400" />
          </div>

          <h3 className="font-display text-xl font-bold mb-3">Вступите в группу поддержки</h3>
          
          <p className="text-white/50 text-sm leading-relaxed mb-6">
            Обязательно вступите в группу поддержки и сбора отзывов, 
            или вы будете исключены из программы
          </p>

          <a
            href={TG_GROUP_LINK}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold py-3 px-8 rounded-xl transition-all duration-300 hover:shadow-[0_8px_30px_rgba(16,185,129,0.3)] hover:-translate-y-0.5 active:translate-y-0"
          >
            <ExternalLink size={16} />
            Наша ссылка
          </a>

          <p className="text-white/20 text-xs mt-4">Нажмите для перехода в Telegram</p>
        </div>
      </div>
    </div>
  )
}
