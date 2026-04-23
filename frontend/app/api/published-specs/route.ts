import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import type { Project, Version, Artifact } from '@/types';

// Helper function to clean tech stack text
function cleanTechStackTags(techStack: string[]): string[] {
  return techStack
    .map((item) => {
      // Remove markdown bold markers
      let cleaned = item.replace(/\*\*/g, '');

      // Extract text before colon or parenthesis
      // "Mobile Application: React Native (for...)" -> "React Native"
      const colonMatch = cleaned.match(/^[^:]+:\s*([^(]+)/);
      if (colonMatch) {
        cleaned = colonMatch[1].trim();
      } else {
        // If no colon, just remove parenthesis content
        cleaned = cleaned.replace(/\([^)]*\)/g, '').trim();
      }

      // Split by comma or slash and take first item
      cleaned = cleaned.split(/[,\/]/)[0].trim();

      return cleaned;
    })
    .filter((tag) => tag.length > 0 && tag.length < 30) // Only keep reasonable length tags
    .slice(0, 5); // Limit to 5 tags
}

export async function GET() {
  try {
    // Fetch all published specs with minimal user fields (avoid schema drift on optional user columns)
    const projectSpecs = await prisma.projectSpec.findMany({
      where: {
        isPublished: true,
      },
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
      orderBy: {
        createdAt: 'desc',
      },
    });

    // Transform ProjectSpec[] to Project[]
    const projects: Project[] = projectSpecs.map((spec) => {
      // Create requirement artifact from functional and non-functional requirements
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

      return project;
    });

    return NextResponse.json(projects);
  } catch (error) {
    console.error('Error fetching published specs:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch published specs',
        ...(process.env.NODE_ENV === 'development' && error instanceof Error
          ? { details: error.message }
          : {}),
      },
      { status: 500 }
    );
  }
}
