import { supabase } from './supabase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  // Retrieve the user session token from Supabase
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API request failed with status: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function getProjectGraph(projectId: string) {
  return fetchWithAuth(`/api/projects/${projectId}/graph`);
}

export async function editRequirement(projectId: string, requirementId: string, title: string, description: string) {
  return fetchWithAuth(`/api/projects/${projectId}/requirements/${requirementId}/edit`, {
    method: 'POST',
    body: JSON.stringify({ title, description }),
  });
}

export async function editTechDecision(projectId: string, decisionId: string, chosenOption: string) {
  return fetchWithAuth(`/api/projects/${projectId}/decisions/${decisionId}/edit`, {
    method: 'POST',
    body: JSON.stringify({ chosen_option: chosenOption }),
  });
}

export async function ingestDocument(projectId: string, filename: string, content: string) {
  return fetchWithAuth(`/api/projects/${projectId}/documents/ingest`, {
    method: 'POST',
    body: JSON.stringify({ filename, content }),
  });
}

export async function searchDocuments(projectId: string, query: string) {
  return fetchWithAuth(`/api/projects/${projectId}/documents/search?query=${encodeURIComponent(query)}`);
}
