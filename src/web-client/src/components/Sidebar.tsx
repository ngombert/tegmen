import { type LucideIcon, User, Users, Baby } from 'lucide-react';

interface UserProfile {
    id: string;
    name: string;
    icon: LucideIcon;
    color: string;
}

export const USERS: UserProfile[] = [
    { id: 'user-parent-1', name: 'Jean (Parent)', icon: User, color: 'bg-blue-500' },
    { id: 'user-child-1', name: 'Léo (Enfant)', icon: Baby, color: 'bg-green-500' },
];

interface SidebarProps {
    currentUser: string;
    onUserSelect: (userId: string) => void;
}

export function Sidebar({ currentUser, onUserSelect }: SidebarProps) {
    return (
        <div className="w-64 bg-slate-900 text-white flex flex-col h-full border-r border-slate-700">
            <div className="p-4 border-b border-slate-700">
                <h1 className="text-xl font-bold flex items-center gap-2">
                    <span className="text-2xl">🏡</span> Tegmen
                </h1>
            </div>

            <div className="flex-1 p-4 space-y-2">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Profils</h2>
                {USERS.map((user) => (
                    <button
                        key={user.id}
                        onClick={() => onUserSelect(user.id)}
                        className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${currentUser === user.id
                            ? 'bg-slate-700 text-white'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                            }`}
                    >
                        <div className={`p-1.5 rounded-md ${user.color}`}>
                            <user.icon size={16} className="text-white" />
                        </div>
                        <span className="font-medium">{user.name}</span>
                    </button>
                ))}
            </div>

            <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
                Family Agents v0.1.0
            </div>
        </div>
    );
}
