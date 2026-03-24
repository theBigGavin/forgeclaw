import { 
  Globe, 
  FileText, 
  Mail, 
  Database, 
  Code,
  Settings,
  Search,
  Sparkles,
} from 'lucide-react'
import { useState } from 'react'

interface SkillItem {
  type: string
  name: string
  icon: React.ElementType
  skillId?: string
  defaults: Record<string, any>
}

interface SkillPaletteProps {
  onAddNode: (type: string, defaults?: Record<string, any>) => void
}

const skills = [
  {
    category: 'Data',
    items: [
      { type: 'skill', name: 'HTTP Request', icon: Globe, skillId: 'http.request', defaults: { skill_id: 'http.request' } },
      { type: 'skill', name: 'File Read', icon: FileText, skillId: 'file.read', defaults: { skill_id: 'file.read' } },
      { type: 'skill', name: 'Database Query', icon: Database, skillId: 'db.query', defaults: { skill_id: 'db.query' } },
      { type: 'skill', name: 'Web Search', icon: Search, skillId: 'search.web', defaults: { skill_id: 'search.web' } },
    ] as SkillItem[],
  },
  {
    category: 'Communication',
    items: [
      { type: 'skill', name: 'Send Email', icon: Mail, skillId: 'email.send', defaults: { skill_id: 'email.send' } },
      { type: 'skill', name: 'Webhook', icon: Globe, skillId: 'http.webhook', defaults: { skill_id: 'http.webhook' } },
    ] as SkillItem[],
  },
  {
    category: 'AI/LLM',
    items: [
      { type: 'skill', name: 'LLM Generate', icon: Sparkles, skillId: 'llm.generate', defaults: { skill_id: 'llm.generate' } },
      { type: 'skill', name: 'LLM Summarize', icon: Sparkles, skillId: 'llm.summarize', defaults: { skill_id: 'llm.summarize' } },
    ] as SkillItem[],
  },
  {
    category: 'Logic',
    items: [
      { type: 'code', name: 'Code Block', icon: Code, defaults: {} },
      { type: 'template', name: 'Template', icon: FileText, defaults: {} },
      { type: 'decision', name: 'Decision', icon: Settings, defaults: {} },
    ] as SkillItem[],
  },
]

export default function SkillPalette({ onAddNode }: SkillPaletteProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredSkills = skills.map(category => ({
    ...category,
    items: category.items.filter(item => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.skillId?.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.items.length > 0)

  return (
    <div className="w-72 card p-4">
      <h3 className="font-semibold mb-4">Skill Palette</h3>
      
      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search skills..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input w-full pl-9 text-sm"
        />
      </div>

      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {filteredSkills.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No skills found</p>
        ) : (
          filteredSkills.map((category) => (
            <div key={category.category}>
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                {category.category}
              </h4>
              <div className="space-y-1">
                {category.items.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => onAddNode(item.type, { name: item.name, ...item.defaults })}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg hover:bg-gray-100 transition-colors group"
                    title={item.skillId || item.name}
                  >
                    <item.icon className="w-4 h-4 text-gray-500 group-hover:text-primary-600" />
                    <span className="text-sm">{item.name}</span>
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
      
      <div className="mt-4 pt-4 border-t text-xs text-gray-500">
        <p>Click to add to canvas</p>
        <p className="mt-1">Drag nodes to reposition</p>
      </div>
    </div>
  )
}
