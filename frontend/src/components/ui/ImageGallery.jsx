import { useState, useEffect, useCallback, useRef } from 'react'
import { X, ChevronLeft, ChevronRight, ZoomIn } from 'lucide-react'

/**
 * Lightbox-gallery for step-by-step instruction screenshots.
 * Shows thumbnails grid → click opens full-size with prev/next navigation.
 * Supports touch swipe on mobile.
 */
export default function ImageGallery({ images, open, onClose, startIndex = 0 }) {
  const [current, setCurrent] = useState(0)
  const touchRef = useRef({ startX: 0, startY: 0, didSwipe: false })

  useEffect(() => {
    if (open) setCurrent(startIndex)
  }, [open, startIndex])

  const goNext = useCallback(() => setCurrent(i => (i + 1) % images.length), [images.length])
  const goPrev = useCallback(() => setCurrent(i => (i - 1 + images.length) % images.length), [images.length])

  useEffect(() => {
    if (!open) return
    function onKey(e) {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowRight') goNext()
      if (e.key === 'ArrowLeft') goPrev()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose, goNext, goPrev])

  // Prevent body scroll when gallery is open
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [open])

  const onTouchStart = useCallback((e) => {
    const t = e.touches[0]
    touchRef.current = { startX: t.clientX, startY: t.clientY, didSwipe: false }
  }, [])

  const onTouchEnd = useCallback((e) => {
    const t = e.changedTouches[0]
    const dx = t.clientX - touchRef.current.startX
    const dy = t.clientY - touchRef.current.startY
    // Horizontal swipe with minimum 50px threshold
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
      touchRef.current.didSwipe = true
      if (dx < 0) goNext()
      else goPrev()
    }
  }, [goNext, goPrev])

  const handleOverlayClick = useCallback((e) => {
    // Don't close if user just finished a swipe
    if (touchRef.current.didSwipe) {
      touchRef.current.didSwipe = false
      return
    }
    onClose()
  }, [onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[70] bg-black/90 backdrop-blur-sm flex items-center justify-center"
      onClick={handleOverlayClick}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
    >
      <div className="relative w-full h-full flex items-center justify-center p-4" onClick={e => e.stopPropagation()}>
        {/* Close */}
        <button onClick={onClose} className="absolute top-4 right-4 z-10 p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer">
          <X size={20} />
        </button>

        {/* Counter */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 text-white/60 text-sm font-medium bg-white/10 px-4 py-1.5 rounded-full">
          {current + 1} / {images.length}
        </div>

        {/* Prev — hidden on mobile, swipe instead */}
        <button onClick={goPrev}
          className="absolute left-2 md:left-6 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer z-10 hidden md:flex">
          <ChevronLeft size={24} />
        </button>

        {/* Image */}
        <img
          src={images[current].src}
          alt={images[current].alt || `Шаг ${current + 1}`}
          className="max-w-full max-h-[85vh] object-contain rounded-xl shadow-2xl select-none pointer-events-none"
          draggable={false}
        />

        {/* Next — hidden on mobile, swipe instead */}
        <button onClick={goNext}
          className="absolute right-2 md:right-6 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer z-10 hidden md:flex">
          <ChevronRight size={24} />
        </button>

        {/* Caption */}
        {images[current].caption && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 max-w-lg text-center text-white/80 text-sm bg-black/60 backdrop-blur px-5 py-2.5 rounded-xl">
            {images[current].caption}
          </div>
        )}

        {/* Dot indicators on mobile */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2 md:hidden">
          {images.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={`w-2 h-2 rounded-full transition-all cursor-pointer ${
                i === current ? 'bg-sky-400 scale-125' : 'bg-white/30'
              }`}
            />
          ))}
        </div>

        {/* Thumbnails — desktop only */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 gap-1.5 max-w-[90vw] overflow-x-auto pb-1 hidden md:flex">
          {images.map((img, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={`w-12 h-12 rounded-lg overflow-hidden border-2 transition-all flex-shrink-0 cursor-pointer ${
                i === current ? 'border-sky-400 scale-110' : 'border-white/20 opacity-50 hover:opacity-80'
              }`}
            >
              <img src={img.src} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Instruction step card — used inside VkGuide
 */
export function InstructionStep({ number, title, description, image, onImageClick }) {
  return (
    <div className="flex gap-4 items-start">
      <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-sm flex-shrink-0 mt-0.5">
        {number}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-white/90 mb-1">{title}</h4>
        {description && <p className="text-xs text-white/50 mb-2">{description}</p>}
        {image && (
          <button onClick={onImageClick}
            className="group relative rounded-xl overflow-hidden border border-white/10 hover:border-blue-500/30 transition-colors cursor-pointer max-w-[280px]">
            <img src={image} alt={`Шаг ${number}`} className="w-full h-auto" loading="lazy" />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
              <ZoomIn size={24} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </button>
        )}
      </div>
    </div>
  )
}
