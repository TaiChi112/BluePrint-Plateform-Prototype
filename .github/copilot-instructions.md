# Copilot instructions

## Project overview
- Next.js App Router project with a single client-side page (most UI lives in app/page.tsx).
- UI is built from many local React components and in-memory mock data (no backend/API yet).
- Tailwind v4 is used via @import in app/globals.css; most styling is className-only.
- Fonts are loaded via next/font in app/layout.tsx.

## Key architecture and flows
- Main view state lives in the App component in app/page.tsx and switches between: home, project, request, profile.
- Data models (Project, Artifact, RequirementSection, UserProfile) and mock data are declared in app/page.tsx.
- Project creation and edits are local-only: updates are done by mapping state arrays (no persistence).
- Mermaid diagrams are rendered via a MermaidDiagram component that injects the script from a CDN and calls window.mermaid (see app/page.tsx).
- Login is mocked in handleLogin and only toggles local state; avatar URLs come from ui-avatars.com.

## Conventions and patterns
- Keep new UI components colocated in app/page.tsx unless you are explicitly asked to split files.
- Artifact rendering branches on contentFormat: text vs mermaid vs structured. Preserve that behavior.
- When adding new images with next/image, always supply width/height and ensure external hosts are allowed in next.config.ts.

## External integration points
- Mermaid is loaded at runtime from https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js.
- Avatar images are loaded from https://ui-avatars.com; the host is whitelisted in next.config.ts.

## Dev workflows
- Dev server: npm run dev (or yarn/pnpm/bun).
- Build: npm run build. Lint: npm run lint.
- No test runner is configured in package.json.
