import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

function isPrismaConnectionError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  return /P1001|P1002|P1017|Can't reach database server|Connection terminated/i.test(error.message);
}

interface SaveSpecRequest {
  data: {
    project_name: string;
    problem_statement: string;
    solution_overview: string;
    functional_requirements: string[];
    non_functional_requirements: string[];
    tech_stack_recommendation: string[];
    status?: string;
    processDescription?: string;
    visualizationProcess?: Record<string, unknown>;
  };
  userId: string;
  isPublished: boolean;
  filename?: string; // For updates
}

export async function POST(request: Request) {
  try {
    const body: SaveSpecRequest = await request.json();
    const { data, userId, isPublished, filename } = body;

    // Validate required fields
    if (!data || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields: data or userId' },
        { status: 400 }
      );
    }

    // Check if this is an update (when filename is provided) or new create
    let savedSpec;

    if (filename) {
      // Try to find existing spec by userId and projectName to update
      const existingSpec = await prisma.projectSpec.findFirst({
        where: {
          userId: userId,
          projectName: data.project_name,
        },
      });

      if (existingSpec) {
        // Update existing spec
        savedSpec = await prisma.projectSpec.update({
          where: { id: existingSpec.id },
          data: {
            problemStatement: data.problem_statement,
            solutionOverview: data.solution_overview,
            functionalRequirements: data.functional_requirements || [],
            nonFunctionalRequirements: data.non_functional_requirements || [],
            techStackRecommendation: data.tech_stack_recommendation || [],
            status: data.status || 'Draft',
            processDescription: data.processDescription || null,
            isPublished: isPublished,
            visualizationProcess: data.visualizationProcess as never || undefined,
            updatedAt: new Date(),
          },
        });
      } else {
        // Create new spec if not found
        savedSpec = await prisma.projectSpec.create({
          data: {
            userId: userId,
            projectName: data.project_name,
            problemStatement: data.problem_statement,
            solutionOverview: data.solution_overview,
            functionalRequirements: data.functional_requirements || [],
            nonFunctionalRequirements: data.non_functional_requirements || [],
            techStackRecommendation: data.tech_stack_recommendation || [],
            status: data.status || 'Draft',
            processDescription: data.processDescription || null,
            isPublished: isPublished,
            visualizationProcess: data.visualizationProcess as never || undefined,
          },
        });
      }
    } else {
      // Create new spec
      savedSpec = await prisma.projectSpec.create({
        data: {
          userId: userId,
          projectName: data.project_name,
          problemStatement: data.problem_statement,
          solutionOverview: data.solution_overview,
          functionalRequirements: data.functional_requirements || [],
          nonFunctionalRequirements: data.non_functional_requirements || [],
          techStackRecommendation: data.tech_stack_recommendation || [],
          status: data.status || 'Draft',
          processDescription: data.processDescription || null,
          isPublished: isPublished,
          visualizationProcess: data.visualizationProcess as never || undefined,
        },
      });
    }

    return NextResponse.json({
      message: 'Spec saved successfully',
      id: savedSpec.id,
      isPublished: savedSpec.isPublished,
    });
  } catch (error) {
    console.error('Error saving spec:', error);

    if (isPrismaConnectionError(error)) {
      return NextResponse.json(
        {
          error: 'Database is temporarily unavailable. Please try again shortly.',
          code: 'DATABASE_UNAVAILABLE'
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      {
        error: 'Failed to save spec to database',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
