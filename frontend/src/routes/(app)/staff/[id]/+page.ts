export const ssr = false;

import { error } from "@sveltejs/kit";
import { api } from "$api/client";
import type { StaffMemberDetail } from "$api/types";

export async function load({ params }: { params: { id: string } }) {
  try {
    const { data } = await api.get<StaffMemberDetail>(`/staff/${params.id}`);
    return { member: data };
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status ?? 500;
    throw error(status, status === 404 ? "Staff member not found" : "Failed to load staff member");
  }
}

export type PageData = Awaited<ReturnType<typeof load>>;
