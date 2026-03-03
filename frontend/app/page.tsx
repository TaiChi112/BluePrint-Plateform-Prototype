"use client";
import { PlusCircle, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { signIn, useSession } from 'next-auth/react';
import type { Artifact, Project, UserProfile } from '../types';
import { INITIAL_PROJECTS } from '../constants/mockData';
import BlueprintDetail from '../components/BlueprintDetail';
import LoginModal from '../components/LoginModal';
import Navbar from '../components/Navbar';
import ProjectCard from '../components/ProjectCard';

export default function App() {
  const router = useRouter();
  const { data: session } = useSession();
  const [view, setView] = useState<'home' | 'project' | 'request' | 'profile'>('home');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const currentUser: UserProfile | null = session?.user
    ? {
        id: session.user.id,
        name: session.user.name || 'User',
        role: 'student',
        provider: 'google',
        avatar: session.user.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(session.user.name || 'User')}&background=random`,
      }
    : null;

  const normalizeProject = (input: Partial<Project> & { problemStatement?: string }): Project => ({
    id: input.id || crypto.randomUUID(),
    title: input.title || 'Untitled Blueprint',
    summary: input.summary || input.problemStatement || '',
    author: input.author || 'Unknown',
    isPublished: input.isPublished ?? true,
    tags: input.tags || [],
    versions: input.versions || [],
    references: input.references,
    createdAt: input.createdAt || new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    const syncData = async () => {
      try {
        // Fetch blueprints from Python API
        let blueprintProjects: Project[] = [];
        try {
          const blueprintsResponse = await fetch('http://localhost:8000/api/blueprints?is_published=true');
          if (blueprintsResponse.ok) {
            const dbData = await blueprintsResponse.json();
            blueprintProjects = Array.isArray(dbData)
              ? dbData.map((project) => normalizeProject(project))
              : [];
          }
        } catch (error) {
          console.error("Failed to fetch blueprints from Python API:", error);
        }

        // Fetch published user specs from Next.js API
        let userSpecProjects: Project[] = [];
        try {
          const specsResponse = await fetch('/api/published-specs');
          if (specsResponse.ok) {
            const specData = await specsResponse.json();
            userSpecProjects = Array.isArray(specData) ? specData : [];
          }
        } catch (error) {
          console.error("Failed to fetch published specs:", error);
        }

        // Merge all data sources: Mock + Blueprints + User Specs
        setProjects([...INITIAL_PROJECTS, ...blueprintProjects, ...userSpecProjects]);
      } catch (error) {
        console.error("Data sync error:", error);
      }
    };
    syncData();
  }, []);

  const handleLogin = async (provider: 'google' | 'github') => {
    await signIn(provider, { callbackUrl: '/' });
    setIsLoginModalOpen(false);
  };

  const handleUpdateArtifact = (updatedArtifact: Artifact) => {
    // ฟังก์ชันนี้จะถูกใช้เมื่อมีการ Contribute/Review ในอนาคต
    console.log("Update requested for:", updatedArtifact.id);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-blue-100">
      <Navbar
        onViewChange={(nextView: 'home' | 'project' | 'request' | 'profile') => {
          if (nextView === 'profile') {
            // Profile navigation is handled in Navbar via router.push
            return;
          }
          setView(nextView);
        }}
        user={currentUser}
        onLoginClick={() => setIsLoginModalOpen(true)}
        onLogoutClick={() => {
          setView('home');
        }}
      />

      <main className="container mx-auto py-8 px-4">
        {view === 'home' && (
          <div className="animate-in fade-in duration-500">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-4">
                The SDLC <span className="text-blue-600">Hub</span>
              </h1>
              <p className="text-lg text-slate-600">
                แหล่งรวม Software Blueprints มาตรฐาน เพื่อฝึกฝนทักษะ Software Engineering
              </p>

              <div className="mt-8 relative max-w-lg mx-auto">
                <Search className="absolute left-3 top-3.5 text-slate-400" size={20} />
                <input
                  type="text"
                  className="block w-full pl-10 pr-3 py-3 border border-slate-200 rounded-full bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ค้นหาไอเดียโปรเจกต์..."
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Card สำหรับสร้างไอเดียใหม่ */}
              <div
                onClick={() => router.push('/generator-test')}
                className="border-2 border-dashed border-blue-200 rounded-xl p-6 flex flex-col items-center justify-center text-blue-500 hover:bg-blue-50 transition cursor-pointer h-full min-h-70 bg-white shadow-sm"
              >
                <PlusCircle size={48} className="mb-4 opacity-80" />
                <span className="font-bold text-lg">Request New Blueprint</span>
                <p className="text-sm mt-2 text-slate-500 text-center px-4">
                  Prompt ไอเดียของคุณเพื่อให้ AI ช่วยสร้าง SDLC Docs
                </p>
              </div>

              {/* แสดงรายการโปรเจกต์จาก Mock + Database */}
              {projects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onClick={() => {
                    // Navigate to dynamic detail page
                    router.push(`/project/${project.id}`);
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {view === 'project' && selectedProject && (
          <BlueprintDetail
            project={selectedProject}
            onBack={() => setView('home')}
            user={currentUser}
            onLoginRequest={() => setIsLoginModalOpen(true)}
            onUpdateArtifact={handleUpdateArtifact}
          />
        )}
      </main>

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLogin={handleLogin}
      />
    </div>
  );
}
