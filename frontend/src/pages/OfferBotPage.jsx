/**
 * Короткая версия пользовательского соглашения для конечных Клиентов
 * (тех, кто пишет ботам в Telegram/VK). Открывается из inline-кнопки бота.
 */
export default function OfferBotPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <header className="mb-8">
          <div className="text-xs uppercase tracking-wider text-foreground/40 mb-2">Соглашение пользователя</div>
          <h1 className="text-2xl md:text-3xl font-display font-bold mb-2">
            Условия общения с ботом
          </h1>
          <p className="text-foreground/60 text-sm">Платформа Meepo · Редакция от 07.04.2025</p>
        </header>

        <article className="space-y-6 text-[15px] leading-relaxed text-foreground/80">
          <p>
            Бот, с которым вы общаетесь, работает на платформе <span className="font-semibold">Meepo</span> (ООО «Мееро»,
            ИНН 0300038291, ОГРН 1260300001235). Начиная переписку, вы соглашаетесь со следующим:
          </p>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">1. Что такое бот</h2>
            <p>
              Бот — это автоматический помощник владельца канала/сообщества, который отвечает на ваши вопросы,
              помогает оформить заказ или связаться с менеджером. Ответы могут формироваться искусственным интеллектом.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">2. Какие данные сохраняются</h2>
            <p>
              Чтобы бот мог продолжать диалог, сохраняются: ваше имя/никнейм в мессенджере, идентификатор
              (Telegram ID или VK ID), номер телефона (если вы делитесь им сами), а также текст сообщений и
              время их отправки. Платёжные данные банковских карт ботом не запрашиваются и не сохраняются.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">3. Зачем сохраняются данные</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Ответ на ваши вопросы и продолжение диалога.</li>
              <li>Передача владельцу бота, чтобы он мог связаться с вами.</li>
              <li>Улучшение качества работы бота и предотвращение злоупотреблений.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">4. Передача третьим лицам</h2>
            <p>
              Данные не передаются третьим лицам, кроме владельца бота, который их получает, и сервисов,
              обеспечивающих работу платформы (хостинг, инфраструктура). Хранение — на серверах в РФ.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">5. Ваши права</h2>
            <p>
              Вы можете в любой момент прекратить общение с ботом, заблокировать его или запросить удаление
              ваших данных, написав на <a href="mailto:meepo.llc@gmail.com" className="text-sky-400 hover:underline">meepo.llc@gmail.com</a>.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">6. Возраст</h2>
            <p>
              Общаясь с ботом, вы подтверждаете, что вам исполнилось 18 лет. Если нет — не отправляйте сообщения.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-foreground mb-2">7. Полные условия</h2>
            <p>
              Полная редакция договора и Политики обработки данных доступна по адресам{' '}
              <a href="/offer" className="text-sky-400 hover:underline">meepo.su/offer</a> и{' '}
              <a href="/privacy" className="text-sky-400 hover:underline">meepo.su/privacy</a>.
            </p>
          </section>

          <p className="text-sm text-foreground/50 pt-4 border-t border-foreground/10">
            Нажимая кнопку «Принимаю» в боте или продолжая общение, вы подтверждаете согласие с этими
            условиями и Политикой обработки персональных данных.
          </p>
        </article>
      </div>
    </div>
  )
}
