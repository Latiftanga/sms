export const ssr = false;

import { api } from "$api/client";
import type { StaffMemberDetail } from "$api/types";

export async function load({ params }: { params: { id: string } }) {
  const { data } = await api.get<StaffMemberDetail>(`/staff/${params.id}`);
  return { member: data };
}

export type PageData = Awaited<ReturnType<typeof load>>;
