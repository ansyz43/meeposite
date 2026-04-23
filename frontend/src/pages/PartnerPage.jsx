import { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../hooks/useAuth'
import { Copy, Check, Link, Users } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import ReferralTree from '../components/ReferralTree'

export default function PartnerPage() {
  const { user } = useAuth()
  const [referrals, setReferrals] = useState([])
  const [tree, setTree] = useState([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const results = await Promise.allSettled([
        api.get('/api/referral/my-referrals'),
        api.get('/api/referral/my-tree'),
      ])
      const referralsData = results[0]?.status === 'fulfilled' ? results[0].value.data : []
      const treeData = results[1]?.status === 'fulfilled' ? results[1].value.data : []
      setReferrals(Array.isArray(referralsData) ? referralsData : [])
      setTree(Array.isArray(treeData) ? treeData : [])
    } catch { /* ignore */ }
    setLoading(false)
  }

  function copyRefLink() {
    if (user?.ref_link) {
      navigator.clipboard.writeText(user.ref_link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loading) return <Loader />

  const totalInTree = countNodes(tree)

  return (
    <div>
      <PageHeader title="Рефералы" />

      {/* Ref link */}
      {user?.ref_link && (
        <div className="glass-card p-4 mb-6">
          <div className="text-xs text-white/40 mb-2">Ваша реферальная ссылка — отправьте её друзьям для регистрации</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Link size={16} className="text-sky-400 shrink-0" />
              <span className="text-white/70 text-sm truncate">{user.ref_link}</span>
            </div>
            <button onClick={copyRefLink} className="flex items-center gap-2 text-sm text-sky-400 hover:text-sky-300 shrink-0 ml-3 transition-colors">
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'Скопировано' : 'Скопировать'}
            </button>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="glass-card p-5">
          <div className="text-white/40 text-xs font-medium mb-2">Прямые рефералы</div>
          <div className="text-2xl font-display font-bold text-white">{referrals.length}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-white/40 text-xs font-medium mb-2">Всего в команде</div>
          <div className="text-2xl font-display font-bold text-white">{totalInTree}</div>
        </div>
      </div>

      {/* Direct referrals list */}
      {referrals.length > 0 && (
        <div className="glass-card overflow-hidden mb-6">
          <div className="p-5 border-b border-white/[0.06]">
            <h2 className="font-display font-semibold flex items-center gap-2">
              <Users size={18} className="text-sky-400" />
              Прямые рефералы ({referrals.length})
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/30 text-xs border-b border-white/[0.06]">
                  <th className="text-left py-3 px-4 font-medium">Имя</th>
                  <th className="text-left py-3 px-4 font-medium">Email</th>
                  <th className="text-right py-3 px-4 font-medium">Дата регистрации</th>
                </tr>
              </thead>
              <tbody>
                {referrals.map(r => (
                  <tr key={r.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-white/80">{r.name}</td>
                    <td className="py-3 px-4 text-white/50">{r.email}</td>
                    <td className="py-3 px-4 text-right text-white/40">
                      {new Date(r.created_at).toLocaleDateString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Referral tree */}
      <ReferralTree tree={tree} userName={user?.name} />
    </div>
  )
}

function countNodes(nodes) {
  let count = 0
  for (const n of nodes) {
    count += 1
    if (n.children) count += countNodes(n.children)
  }
  return count
}
