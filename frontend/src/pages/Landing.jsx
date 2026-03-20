import { Link } from 'react-router-dom'
import { Bot, MessageSquare, Users, Clock, Brain, Zap, Shield, ChevronRight, ArrowRight, CheckCircle2, HelpCircle } from 'lucide-react'
import { useState } from 'react'

function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-dark-900/80 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold">
          <span className="text-accent-400">Meepo</span>
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-white/70 hover:text-white transition-colors text-sm">Войти</Link>
          <Link to="/register" className="btn-primary text-sm !py-2 !px-5">Начать бесплатно</Link>
        </div>
      </div>
    </nav>
  )
}

function Hero() {
  return (
    <section className="pt-32 pb-20 px-6 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-accent-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="max-w-5xl mx-auto text-center relative">
        <div className="inline-flex items-center gap-2 bg-accent-500/10 border border-accent-500/20 rounded-full px-4 py-1.5 mb-6">
          <Zap size={14} className="text-accent-400" />
          <span className="text-accent-400 text-sm font-medium">Платформа для дистрибьюторов FitLine</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6">
          Ваш ИИ-ассистент, который продаёт{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400">
            FitLine за вас 24/7
          </span>
        </h1>
        <p className="text-lg text-white/60 max-w-2xl mx-auto mb-10">
          Персональный Telegram-бот, который знает всё о продукции, отвечает клиентам
          от вашего имени и приводит готовых покупателей
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/register" className="btn-primary text-lg flex items-center justify-center gap-2">
            Попробовать бесплатно <ArrowRight size={20} />
          </Link>
          <a href="#how-it-works" className="btn-secondary text-lg flex items-center justify-center gap-2">
            Как это работает
          </a>
        </div>
      </div>

      {/* Chat mockup */}
      <div className="max-w-md mx-auto mt-16">
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center gap-3 pb-4 border-b border-white/10">
            <div className="w-10 h-10 rounded-full bg-accent-500/20 flex items-center justify-center">
              <Bot size={20} className="text-accent-400" />
            </div>
            <div>
              <div className="font-semibold text-sm">Ассистент Анны</div>
              <div className="text-xs text-green-400">онлайн</div>
            </div>
          </div>
          <ChatBubble from="bot" text="Привет! Я ассистент Анны. Чем могу помочь? 😊" />
          <ChatBubble from="user" text="Расскажи, что такое FitLine?" />
          <ChatBubble from="bot" text="FitLine — линейка продуктов для здоровья от немецкой компании PM-International, основанной в 1993 году. Все продукты созданы на технологии NTC — усвоение до 5 раз быстрее. Что интересует: энергия, пищеварение или красота?" />
          <ChatBubble from="user" text="Усталость и плохой сон" />
          <ChatBubble from="bot" text="Рекомендую FitLine Restorate — восстанавливает кислотно-щелочной баланс, укрепляет нервную систему, улучшает сон. Хотите попробовать? Анна лично поможет с заказом!" />
        </div>
      </div>
    </section>
  )
}

function ChatBubble({ from, text }) {
  const isBot = from === 'bot'
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
        isBot
          ? 'bg-dark-700 text-white/90 rounded-tl-md'
          : 'bg-accent-500 text-white rounded-tr-md'
      }`}>
        {text}
      </div>
    </div>
  )
}

function PainPoints() {
  const pains = [
    { icon: MessageSquare, title: 'Одни и те же вопросы', desc: '«Что такое NTC?», «Чем Basics отличается от Restorate?» — вы отвечаете на это 20 раз в день' },
    { icon: Clock, title: 'Потерянные клиенты', desc: 'Написал человек в 23:00, вы спали — утром он уже забыл или ушёл к другому' },
    { icon: Users, title: 'Нет времени на всех', desc: '50 контактов, каждому нужно объяснить, показать, убедить. Физически невозможно' },
    { icon: Brain, title: 'Сложно объяснить продукт', desc: 'Состав, патенты, технология NTC — не каждый может чётко и убедительно рассказать' },
    { icon: HelpCircle, title: 'Новички буксуют', desc: 'Пришёл новый партнёр, не знает продукт, боится общаться — теряет первых клиентов' },
  ]

  return (
    <section className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">Знакомо?</h2>
        <p className="text-white/50 text-center mb-12">Проблемы, с которыми сталкивается каждый дистрибьютор</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pains.map((p, i) => (
            <div key={i} className="glass-card p-6 hover:border-red-500/30 transition-colors">
              <p.icon size={28} className="text-red-400 mb-4" />
              <h3 className="font-semibold text-lg mb-2">{p.title}</h3>
              <p className="text-white/50 text-sm">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Solution() {
  const features = [
    { icon: Brain, title: 'Знает всю продукцию', desc: 'Activize, Restorate, Basics, Omega, Q10, Beauty, Antioxy — состав, показания, технологию NTC' },
    { icon: Clock, title: 'Отвечает 24/7', desc: 'Мгновенно, грамотно, без выходных и обеденных перерывов' },
    { icon: Bot, title: 'Говорит от вашего имени', desc: '«Привет! Я ассистент Анны» — ваш личный бренд, ваш бот' },
    { icon: Users, title: 'Собирает контакты', desc: 'Вы видите всех, кто написал боту: имя, никнейм, что спрашивали' },
    { icon: MessageSquare, title: 'Все переписки в ЛК', desc: 'Читайте все диалоги бота с клиентами в реальном времени' },
    { icon: ArrowRight, title: 'Передаёт вам клиента', desc: 'Когда человек заинтересован — бот даёт вашу ссылку' },
  ]

  return (
    <section className="py-20 px-6 bg-dark-800/50 relative">
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-accent-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="max-w-5xl mx-auto relative">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">
          <span className="text-accent-400">Meepo</span> берёт это на себя
        </h2>
        <p className="text-white/50 text-center mb-12">Всё, что делал бы идеальный ассистент — но без зарплаты</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={i} className="glass-card p-6 hover:border-accent-500/30 transition-colors">
              <f.icon size={28} className="text-accent-400 mb-4" />
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-white/50 text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function HowItWorks() {
  const steps = [
    { num: '1', title: 'Зарегистрируйтесь', desc: 'Email и пароль — 30 секунд' },
    { num: '2', title: 'Подключите бота', desc: 'Создайте бота в @BotFather и вставьте токен' },
    { num: '3', title: 'Получайте клиентов', desc: 'Бот уже знает всё о FitLine и работает от вашего имени' },
  ]

  return (
    <section id="how-it-works" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Как это работает</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((s, i) => (
            <div key={i} className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-accent-500/20 border border-accent-500/30 flex items-center justify-center text-2xl font-bold text-accent-400 mx-auto mb-4 shadow-glow">
                {s.num}
              </div>
              <h3 className="font-semibold text-lg mb-2">{s.title}</h3>
              <p className="text-white/50 text-sm">{s.desc}</p>
              {i < 2 && <ChevronRight size={24} className="text-white/20 mx-auto mt-4 hidden md:block rotate-0" />}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Advantages() {
  const items = [
    'Единая проверенная база знаний — без ошибок',
    'Работает на технологии OpenAI GPT',
    'Ваше имя, ваша аватарка, ваш бот',
    'Все переписки видны в личном кабинете',
    'Подходит и новичкам, и опытным партнёрам',
    'Подключение за 5 минут без технических знаний',
  ]

  return (
    <section className="py-20 px-6 bg-dark-800/50 relative">
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-accent-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="max-w-3xl mx-auto relative">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Почему Meepo</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {items.map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-4">
              <CheckCircle2 size={20} className="text-green-400 mt-0.5 flex-shrink-0" />
              <span className="text-white/80">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function FAQ() {
  const [open, setOpen] = useState(null)
  const items = [
    { q: 'Нужно ли разбираться в технологиях?', a: 'Нет. Создайте бота через @BotFather в Telegram (2 минуты), вставьте токен в личном кабинете — готово.' },
    { q: 'Бот будет говорить ерунду?', a: 'Нет. Он обучен на проверенной базе знаний FitLine и отвечает строго по ней. Если не знает ответ — честно скажет и предложит связаться с вами.' },
    { q: 'Могу ли я изменить имя ассистента?', a: 'Да. В личном кабинете вы можете изменить имя, приветственное сообщение и аватарку бота.' },
    { q: 'Это легально?', a: 'Да. Бот информирует о продукции и направляет к вам. Он не продаёт напрямую и не принимает оплату.' },
    { q: 'Сколько клиентов может обслуживать бот?', a: 'Без ограничений. Бот отвечает каждому пользователю в течение нескольких секунд, параллельно.' },
  ]

  return (
    <section className="py-20 px-6">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Частые вопросы</h2>
        <div className="space-y-3">
          {items.map((item, i) => (
            <div key={i} className="glass-card overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between p-5 text-left"
              >
                <span className="font-medium">{item.q}</span>
                <ChevronRight size={20} className={`text-white/40 transition-transform ${open === i ? 'rotate-90' : ''}`} />
              </button>
              {open === i && (
                <div className="px-5 pb-5 text-white/60 text-sm">{item.a}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTA() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <div className="glass-card p-12 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border-emerald-500/20">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Готовы начать?</h2>
          <p className="text-white/60 mb-8">Подключите бота за 5 минут и пусть он работает за вас</p>
          <Link to="/register" className="btn-primary text-lg inline-flex items-center gap-2">
            Создать аккаунт бесплатно <ArrowRight size={20} />
          </Link>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-white/5 py-8 px-6">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-white/40 text-sm">© 2026 Meepo. Все права защищены.</div>
        <div className="flex gap-6 text-white/40 text-sm">
          <a href="#" className="hover:text-white/70 transition-colors">Политика конфиденциальности</a>
          <a href="#" className="hover:text-white/70 transition-colors">Условия использования</a>
        </div>
      </div>
    </footer>
  )
}

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <PainPoints />
      <Solution />
      <HowItWorks />
      <Advantages />
      <FAQ />
      <CTA />
      <Footer />
    </div>
  )
}
