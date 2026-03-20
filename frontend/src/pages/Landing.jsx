import { Link } from 'react-router-dom'
import { Bot, MessageSquare, Users, Clock, Brain, Zap, Shield, ArrowRight, CheckCircle2, ChevronDown, Sparkles, BarChart3, Globe, Eye, Send, Plug, Settings2 } from 'lucide-react'
import { useState, useEffect, useRef, useCallback } from 'react'

/* ─── Intersection Observer hook ─── */
function useInView(options = {}) {
  const ref = useRef(null)
  const [isInView, setIsInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setIsInView(true); observer.unobserve(el) }
    }, { threshold: 0.15, ...options })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])
  return [ref, isInView]
}

/* ─── Animated counter ─── */
function AnimatedNumber({ value, suffix = '' }) {
  const [count, setCount] = useState(0)
  const [ref, isInView] = useInView()
  useEffect(() => {
    if (!isInView) return
    let start = 0
    const end = parseInt(value)
    const duration = 1500
    const step = Math.max(1, Math.floor(end / (duration / 16)))
    const timer = setInterval(() => {
      start += step
      if (start >= end) { setCount(end); clearInterval(timer) }
      else setCount(start)
    }, 16)
    return () => clearInterval(timer)
  }, [isInView, value])
  return <span ref={ref} className="font-mono">{count}{suffix}</span>
}

/* ─── Mouse-follow card ─── */
function GlassCard({ children, className = '', hover = true }) {
  const cardRef = useRef(null)
  const handleMouseMove = useCallback((e) => {
    const rect = cardRef.current.getBoundingClientRect()
    cardRef.current.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`)
    cardRef.current.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`)
  }, [])
  return (
    <div ref={cardRef} onMouseMove={hover ? handleMouseMove : undefined}
      className={`glass-card ${className}`}>
      {children}
    </div>
  )
}

/* ─────────────────────── NAVBAR ─────────────────────── */
function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-500 ${
      scrolled ? 'bg-[#060B11]/80 backdrop-blur-2xl border-b border-white/[0.06] shadow-lg shadow-black/20' : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
            <Bot size={18} className="text-white" />
          </div>
          <span className="text-xl font-display font-bold gradient-text">Meepo</span>
        </Link>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-white/50 hover:text-white text-sm transition-colors duration-200">Возможности</a>
          <a href="#how-it-works" className="text-white/50 hover:text-white text-sm transition-colors duration-200">Как работает</a>
          <a href="#faq" className="text-white/50 hover:text-white text-sm transition-colors duration-200">FAQ</a>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-white/60 hover:text-white transition-colors text-sm hidden sm:block">Войти</Link>
          <Link to="/register" className="btn-primary text-sm !py-2 !px-5">
            <span className="relative z-10">Попробовать</span>
          </Link>
        </div>
      </div>
    </nav>
  )
}

/* ─────────────────────── HERO ─────────────────────── */
function Hero() {
  const [ref, isInView] = useInView()
  return (
    <section ref={ref} className="relative min-h-screen flex items-center pt-16 pb-20 px-6 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 mesh-gradient" />
      <div className="absolute top-[20%] left-[10%] w-[500px] h-[500px] bg-emerald-500/[0.07] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[10%] right-[5%] w-[400px] h-[400px] bg-teal-500/[0.05] rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute inset-0 noise" />

      <div className="max-w-7xl mx-auto w-full relative">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Text */}
          <div className={`transition-all duration-700 ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="section-badge">
              <Sparkles size={14} />
              <span>AI-Платформа для FitLine</span>
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] mb-6 tracking-tight">
              Ваш ИИ-ассистент, который продаёт{' '}
              <span className="gradient-text">FitLine за вас</span>
              {' '}24/7
            </h1>
            <p className="text-lg text-white/50 max-w-xl mb-8 leading-relaxed">
              Персональный Telegram-бот на GPT, который знает всё о продукции, 
              отвечает клиентам от вашего имени и приводит готовых покупателей
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Link to="/register" className="btn-primary text-base flex items-center justify-center gap-2 group">
                <span className="relative z-10 flex items-center gap-2">
                  Создать бота бесплатно 
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>
              <a href="#how-it-works" className="btn-secondary text-base flex items-center justify-center gap-2">
                Как это работает
              </a>
            </div>
            {/* Metrics */}
            <div className="flex items-center gap-8 text-sm">
              <div>
                <div className="text-2xl font-display font-bold text-white">Личный</div>
                <div className="text-white/40 mt-1">ИИ-ассистент</div>
              </div>
              <div className="w-px h-10 bg-white/10" />
              <div>
                <div className="text-2xl font-display font-bold text-white"><AnimatedNumber value="100" suffix="+" /></div>
                <div className="text-white/40 mt-1">клиентов в день</div>
              </div>
              <div className="w-px h-10 bg-white/10" />
              <div>
                <div className="text-2xl font-display font-bold text-white">24/7</div>
                <div className="text-white/40 mt-1">без выходных</div>
              </div>
            </div>
          </div>

          {/* Right: Chat mockup */}
          <div className={`transition-all duration-700 delay-200 ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-br from-emerald-500/10 to-teal-500/5 rounded-3xl blur-2xl pointer-events-none" />
              <GlassCard className="p-6 relative">
                <div className="flex items-center gap-3 pb-4 border-b border-white/[0.06]">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
                    <Bot size={20} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="font-display font-semibold text-sm">Ассистент Анны</div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-xs text-emerald-400">онлайн</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3 pt-4">
                  <ChatBubble from="bot" text="Привет! Я ассистент Анны 👋 Расскажи, что хочется улучшить в самочувствии?" delay={0} />
                  <ChatBubble from="user" text="Постоянно устаю, к вечеру сил вообще нет" delay={1} />
                  <ChatBubble from="bot" text="Знакомо! Представь — утром встаёшь и реально чувствуешь бодрость без кофе, а сил хватает до вечера. Оптимальный Сет FitLine именно для этого. Хочешь расскажу подробнее?" delay={2} />
                  <ChatBubble from="user" text="Да, расскажи" delay={3} />
                  <ChatBubble from="bot" text="Это два продукта — утром и вечером. 1000+ профессиональных спортсменов пьют это каждый день. Хочешь попробовать? Скину ссылку для заказа 🙌" delay={4} />
                </div>
                {/* Input mockup */}
                <div className="mt-4 flex items-center gap-2 bg-white/[0.03] rounded-xl px-4 py-3 border border-white/[0.06]">
                  <span className="text-white/30 text-sm flex-1">Напишите сообщение...</span>
                  <Send size={16} className="text-emerald-400" />
                </div>
              </GlassCard>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function ChatBubble({ from, text, delay = 0 }) {
  const isBot = from === 'bot'
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} animate-fade-in-up`}
      style={{ animationDelay: `${delay * 0.3}s` }}>
      <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
        isBot
          ? 'bg-white/[0.05] text-white/80 rounded-tl-md border border-white/[0.04]'
          : 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-tr-md'
      }`}>
        {text}
      </div>
    </div>
  )
}

/* ─────────────────────── PAIN POINTS ─────────────────────── */
function PainPoints() {
  const [ref, isInView] = useInView()
  const pains = [
    { icon: MessageSquare, title: 'Одни и те же вопросы', desc: '«Что такое NTC?», «Чем Basics отличается от Restorate?» — отвечаете по 20 раз в день' },
    { icon: Clock, title: 'Потерянные клиенты', desc: 'Человек написал в 23:00, вы спали — утром он уже ушёл к другому' },
    { icon: Users, title: 'Нет времени на всех', desc: '50+ контактов, каждому нужно объяснить и убедить. Физически невозможно' },
    { icon: Brain, title: 'Сложно объяснить продукт', desc: 'Состав, патенты, NTC — не каждый может рассказать чётко и убедительно' },
    { icon: Shield, title: 'Новички буксуют', desc: 'Новый партнёр не знает продукт, боится общаться — теряет первых клиентов' },
  ]

  return (
    <section className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div ref={ref} className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <div className="section-badge mx-auto">
            <Eye size={14} />
            <span>Проблемы</span>
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            Знакомые <span className="text-red-400">боли</span>?
          </h2>
          <p className="text-white/40 max-w-lg mx-auto">С чем сталкивается каждый дистрибьютор FitLine</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {pains.map((p, i) => (
            <GlassCard key={i} className={`p-6 transition-all duration-500 ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
              style={{ transitionDelay: `${i * 100}ms` }}>
              <div className="w-11 h-11 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
                <p.icon size={20} className="text-red-400" />
              </div>
              <h3 className="font-display font-semibold text-base mb-2">{p.title}</h3>
              <p className="text-white/40 text-sm leading-relaxed">{p.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── FEATURES ─────────────────────── */
function Features() {
  const [ref, isInView] = useInView()
  const features = [
    { icon: Brain, title: 'Знает всю продукцию', desc: 'Activize, Restorate, Basics, Omega, Q10, Beauty — состав, показания, технологию NTC', accent: true },
    { icon: Clock, title: 'Работает 24/7', desc: 'Мгновенно, грамотно, без выходных и обеденных перерывов' },
    { icon: Sparkles, title: 'Говорит от вашего имени', desc: '«Привет! Я ассистент Анны» — ваш бренд, ваш бот, ваш стиль' },
    { icon: BarChart3, title: 'Собирает контакты', desc: 'Все клиенты в вашем ЛК: имя, никнейм, что спрашивали, когда писали' },
    { icon: Globe, title: 'Все диалоги в одном месте', desc: 'Читайте переписки бота с клиентами в реальном времени' },
    { icon: Send, title: 'Передаёт клиента вам', desc: 'Когда человек заинтересован — бот отправляет вашу ссылку для заказа' },
  ]

  return (
    <section id="features" className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div className="absolute top-[30%] right-0 w-[500px] h-[500px] bg-emerald-500/[0.04] rounded-full blur-[120px] pointer-events-none" />

      <div ref={ref} className="max-w-6xl mx-auto relative">
        <div className="text-center mb-16">
          <div className="section-badge mx-auto">
            <Zap size={14} />
            <span>Возможности</span>
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            <span className="gradient-text">Meepo</span> берёт это на себя
          </h2>
          <p className="text-white/40 max-w-lg mx-auto">Всё, что делал бы идеальный ассистент — но без зарплаты</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <GlassCard key={i}
              className={`p-6 group hover:shadow-card-hover hover:-translate-y-1 transition-all duration-500 ${
                isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
              } ${f.accent ? 'border-emerald-500/20' : ''}`}
              style={{ transitionDelay: `${i * 80}ms` }}>
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 transition-colors duration-300 ${
                f.accent 
                  ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30' 
                  : 'bg-white/[0.05] border border-white/[0.08] group-hover:border-emerald-500/30 group-hover:bg-emerald-500/10'
              }`}>
                <f.icon size={20} className={`${f.accent ? 'text-emerald-400' : 'text-white/60 group-hover:text-emerald-400'} transition-colors`} />
              </div>
              <h3 className="font-display font-semibold text-base mb-2">{f.title}</h3>
              <p className="text-white/40 text-sm leading-relaxed">{f.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── HOW IT WORKS ─────────────────────── */
function HowItWorks() {
  const [ref, isInView] = useInView()
  const steps = [
    { icon: Users, num: '01', title: 'Регистрация за 30 секунд', desc: 'Email, пароль — и вы уже в личном кабинете' },
    { icon: Sparkles, num: '02', title: 'Настройте ассистента', desc: 'Укажите имя, загрузите аватарку и ваш бот готов к работе' },
    { icon: Send, num: '03', title: 'Делитесь ссылкой', desc: 'Отправляйте ссылку клиентам — бот проконсультирует, подберёт продукт и передаст вам готового покупателя' },
  ]

  return (
    <section id="how-it-works" className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div ref={ref} className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <div className="section-badge mx-auto">
            <Settings2 size={14} />
            <span>3 шага</span>
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold">Как это работает</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6 relative">
          {/* Connector lines */}
          <div className="hidden md:block absolute top-[3.25rem] left-[calc(33.333%-1rem)] right-[calc(33.333%-1rem)] h-px">
            <div className={`h-full bg-gradient-to-r from-emerald-500/40 via-emerald-500/20 to-emerald-500/40 transition-all duration-1000 ${isInView ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}`} />
          </div>
          {steps.map((s, i) => (
            <div key={i} className={`text-center transition-all duration-600 ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
              style={{ transitionDelay: `${i * 150}ms` }}>
              <div className="relative inline-flex mb-6">
                <div className="w-[4.5rem] h-[4.5rem] rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center shadow-glow">
                  <s.icon size={28} className="text-emerald-400" />
                </div>
                <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-emerald-500 text-[10px] font-mono font-bold text-white flex items-center justify-center">
                  {i + 1}
                </span>
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{s.title}</h3>
              <p className="text-white/40 text-sm leading-relaxed max-w-xs mx-auto">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── ADVANTAGES ─────────────────────── */
function Advantages() {
  const [ref, isInView] = useInView()
  const items = [
    { icon: Shield, text: 'Единая проверенная база знаний — без ошибок' },
    { icon: Sparkles, text: 'Работает на технологии OpenAI GPT' },
    { icon: Bot, text: 'Ваше имя, ваша аватарка, ваш бот' },
    { icon: Eye, text: 'Все переписки видны в личном кабинете' },
    { icon: Users, text: 'Подходит и новичкам, и опытным партнёрам' },
    { icon: Zap, text: 'Подключение за 5 минут без технических знаний' },
  ]

  return (
    <section className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div className="absolute bottom-[10%] left-[5%] w-[400px] h-[400px] bg-teal-500/[0.04] rounded-full blur-[100px] pointer-events-none" />
      <div ref={ref} className="max-w-4xl mx-auto relative">
        <div className="text-center mb-16">
          <div className="section-badge mx-auto">
            <CheckCircle2 size={14} />
            <span>Преимущества</span>
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold">Почему Meepo</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          {items.map((item, i) => (
            <div key={i}
              className={`flex items-center gap-4 p-5 rounded-xl bg-white/[0.02] border border-white/[0.04]
              hover:border-emerald-500/20 hover:bg-white/[0.04] transition-all duration-300 cursor-default
              ${isInView ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}
              style={{ transitionDelay: `${i * 80}ms` }}>
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <item.icon size={16} className="text-emerald-400" />
              </div>
              <span className="text-white/70 text-sm">{item.text}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── FAQ ─────────────────────── */
function FAQ() {
  const [open, setOpen] = useState(null)
  const [ref, isInView] = useInView()
  const items = [
    { q: 'Нужно ли разбираться в технологиях?', a: 'Нет. Создайте бота через @BotFather в Telegram (2 минуты), вставьте токен в личном кабинете — готово. Технические знания не требуются.' },
    { q: 'Бот будет говорить ерунду?', a: 'Нет. Он обучен на проверенной базе знаний FitLine и отвечает строго по ней. Если не знает ответ — честно скажет и предложит связаться с вами.' },
    { q: 'Могу ли я изменить имя ассистента?', a: 'Да. В личном кабинете вы можете изменить имя, приветственное сообщение и аватарку бота — полная кастомизация.' },
    { q: 'Это легально?', a: 'Да. Бот информирует о продукции и направляет к вам. Он не продаёт напрямую и не принимает оплату.' },
    { q: 'Сколько клиентов может обслуживать?', a: 'Без ограничений. Бот отвечает каждому моментально и параллельно. Одновременно обслуживает сотни чатов.' },
  ]

  return (
    <section id="faq" className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div ref={ref} className="max-w-2xl mx-auto">
        <div className="text-center mb-16">
          <div className="section-badge mx-auto">
            <MessageSquare size={14} />
            <span>FAQ</span>
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold">Частые вопросы</h2>
        </div>
        <div className="space-y-3">
          {items.map((item, i) => (
            <div key={i}
              className={`rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden transition-all duration-300
              hover:border-white/[0.1] ${open === i ? 'border-emerald-500/20 bg-emerald-500/[0.02]' : ''}
              ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
              style={{ transitionDelay: `${i * 60}ms` }}>
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between p-5 text-left cursor-pointer group">
                <span className="font-display font-medium text-sm pr-4">{item.q}</span>
                <ChevronDown size={18} className={`text-white/30 flex-shrink-0 transition-transform duration-300 ${open === i ? 'rotate-180 text-emerald-400' : 'group-hover:text-white/50'}`} />
              </button>
              <div className={`overflow-hidden transition-all duration-300 ${open === i ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="px-5 pb-5 text-white/50 text-sm leading-relaxed">{item.a}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── CTA ─────────────────────── */
function CTA() {
  const [ref, isInView] = useInView()
  return (
    <section className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      <div ref={ref} className={`max-w-4xl mx-auto transition-all duration-700 ${isInView ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
        <div className="relative rounded-3xl overflow-hidden">
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-teal-500/5 to-emerald-600/10" />
          <div className="absolute inset-0 mesh-gradient opacity-50" />
          <div className="absolute inset-0 border border-emerald-500/20 rounded-3xl" />
          
          <div className="relative p-12 md:p-16 text-center">
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
              Готовы начать <span className="gradient-text">продавать умнее</span>?
            </h2>
            <p className="text-white/50 max-w-lg mx-auto mb-8 leading-relaxed">
              Подключите ИИ-ассистента за 5 минут и пусть он работает за вас — 
              пока вы занимаетесь важными делами
            </p>
            <Link to="/register" className="btn-primary text-base inline-flex items-center gap-2 group">
              <span className="relative z-10 flex items-center gap-2">
                Создать бота бесплатно
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
            <p className="text-white/30 text-xs mt-4">Бесплатная регистрация • Без банковской карты</p>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────── FOOTER ─────────────────────── */
function Footer() {
  return (
    <footer className="border-t border-white/[0.06] py-10 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
              <Bot size={14} className="text-white" />
            </div>
            <span className="font-display font-bold text-white/60">Meepo</span>
          </div>
          <div className="flex gap-8 text-white/30 text-sm">
            <a href="#features" className="hover:text-white/60 transition-colors cursor-pointer">Возможности</a>
            <a href="#how-it-works" className="hover:text-white/60 transition-colors cursor-pointer">Как работает</a>
            <a href="#faq" className="hover:text-white/60 transition-colors cursor-pointer">FAQ</a>
          </div>
          <div className="text-white/20 text-xs">© 2026 Meepo. Все права защищены.</div>
        </div>
      </div>
    </footer>
  )
}

/* ─────────────────────── MAIN ─────────────────────── */
export default function Landing() {
  return (
    <div className="min-h-screen bg-[#060B11] relative">
      <Navbar />
      <Hero />
      <PainPoints />
      <Features />
      <HowItWorks />
      <Advantages />
      <FAQ />
      <CTA />
      <Footer />
    </div>
  )
}
