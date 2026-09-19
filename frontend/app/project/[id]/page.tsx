'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import WorkspaceLayout from '@/app/components/WorkspaceLayout';

export default function ProjectPage() {
  const { id } = useParams();
  const projectId = typeof id === 'string' ? id : Array.isArray(id) ? id[0] : undefined;

  return <WorkspaceLayout initialProjectId={projectId} />;
}
