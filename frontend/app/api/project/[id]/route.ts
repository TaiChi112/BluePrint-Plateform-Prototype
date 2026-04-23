import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import type { Project, Version, Artifact } from '@/types';

const SWR_CACHE_HEADER = 'public, s-maxage=60, stale-while-revalidate=300';

function jsonWithSWR(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': SWR_CACHE_HEADER,
    },
  });
}

// Helper to clean tech stack tags
function cleanTechStackTags(techStack: string[]): string[] {
  return techStack
    .map((item) => {
      let cleaned = item.replace(/\*\*/g, '');
      const colonMatch = cleaned.match(/^[^:]+:\s*([^(]+)/);
      if (colonMatch) {
        cleaned = colonMatch[1].trim();
      } else {
        cleaned = cleaned.replace(/\([^)]*\)/g, '').trim();
      }
      cleaned = cleaned.split(/[,\/]/)[0].trim();
      return cleaned;
    })
    .filter((tag) => tag.length > 0 && tag.length < 30)
    .slice(0, 5);
}

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const { id } = params;

    // Try fetching from Prisma (user-generated specs)
    const spec = await prisma.projectSpec.findUnique({
      where: { id },
      select: {
        id: true,
        artifactId: true,
        projectName: true,
        problemStatement: true,
        solutionOverview: true,
        functionalRequirements: true,
        nonFunctionalRequirements: true,
        techStackRecommendation: true,
        status: true,
        isPublished: true,
        createdAt: true,
        updatedAt: true,
        user: {
          select: {
            name: true,
          },
        },
      },
    });

    if (spec) {
      // Transform ProjectSpec to Project format
      const requirementContent = [
        '## Functional Requirements',
        ...spec.functionalRequirements.map((req, idx) => `${idx + 1}. ${req}`),
        '',
        '## Non-Functional Requirements',
        ...spec.nonFunctionalRequirements.map((req, idx) => `${idx + 1}. ${req}`),
      ].join('\n');

      const artifact: Artifact = {
        id: spec.artifactId || `artifact-${spec.id}`,
        type: 'requirement',
        title: 'Requirements',
        content: requirementContent,
        contentFormat: 'text',
        updatedAt: spec.updatedAt.toISOString().slice(0, 10),
        dataSpec: {
          project_name: spec.projectName,
          problem_statement: spec.problemStatement,
          solution_overview: spec.solutionOverview,
          functional_requirements: spec.functionalRequirements,
          non_functional_requirements: spec.nonFunctionalRequirements,
          tech_stack_recommendation: spec.techStackRecommendation,
          status: spec.status || 'Draft',
          _saved_at: spec.createdAt.toISOString(),
        },
      };

      const version: Version = {
        versionNumber: '1.0',
        label: 'Initial',
        description: spec.solutionOverview || 'AI-generated specification',
        artifacts: [artifact],
      };

      const project: Project = {
        id: spec.id,
        title: spec.projectName,
        summary: spec.problemStatement,
        author: spec.user?.name || 'Unknown',
        isPublished: spec.isPublished,
        tags: cleanTechStackTags(spec.techStackRecommendation || []),
        versions: [version],
        createdAt: spec.createdAt.toISOString().slice(0, 10),
      };

      return jsonWithSWR(project);
    }

    // If not found in Prisma, try Python API (blueprints)
    try {
      const pythonResponse = await fetch(`http://localhost:8000/api/blueprints/${id}`);
      if (pythonResponse.ok) {
        const blueprintData = await pythonResponse.json();
        return jsonWithSWR(blueprintData);
      }
    } catch (pythonError) {
      console.error('Python API fallback failed:', pythonError);
    }

    // Project not found
    return jsonWithSWR(
      { error: 'Project not found' },
      404
    );
  } catch (error) {
    console.error('Error fetching project:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch project',
        ...(process.env.NODE_ENV === 'development' && error instanceof Error
          ? { details: error.message }
          : {}),
      },
      { status: 500 }
    );
  }
}
