/**
 * Offline write queue — Dexie.js (IndexedDB).
 *
 * Usage pattern:
 *   1. Try the live API call first.
 *   2. On network failure, queue the payload to IndexedDB.
 *   3. On window 'online', drain the queue automatically.
 *
 * Only attendance and score capture use this queue (Phase 5 & 6).
 */
import Dexie, { type EntityTable } from "dexie";

interface AttendanceQueueItem {
  id?: number;
  schoolCalendarId: string;
  schoolPeriodId: string | null;
  records: Array<{
    studentTermEnrollmentId: string;
    status: string;
    note: string | null;
  }>;
  queuedAt: number; // epoch ms
  retryCount: number;
}

interface ScoreQueueItem {
  id?: number;
  studentSubjectRegistrationId: string;
  assessmentType: string;
  assessmentLabel: string | null;
  rawScore: number;
  maxScore: number;
  queuedAt: number;
  retryCount: number;
}

class OfflineDatabase extends Dexie {
  attendanceQueue!: EntityTable<AttendanceQueueItem, "id">;
  scoreQueue!: EntityTable<ScoreQueueItem, "id">;

  constructor() {
    super("ttek_sis_offline");
    this.version(1).stores({
      attendanceQueue: "++id, schoolCalendarId, queuedAt",
      scoreQueue: "++id, studentSubjectRegistrationId, queuedAt",
    });
  }
}

export const offlineDb = new OfflineDatabase();

// ── Attendance ────────────────────────────────────────────────────

export async function queueAttendance(
  payload: Omit<AttendanceQueueItem, "id" | "queuedAt" | "retryCount">
): Promise<void> {
  await offlineDb.attendanceQueue.add({
    ...payload,
    queuedAt: Date.now(),
    retryCount: 0,
  });
}

export async function getPendingAttendance(): Promise<AttendanceQueueItem[]> {
  return offlineDb.attendanceQueue.orderBy("queuedAt").toArray();
}

// ── Score ─────────────────────────────────────────────────────────

export async function queueScore(
  payload: Omit<ScoreQueueItem, "id" | "queuedAt" | "retryCount">
): Promise<void> {
  await offlineDb.scoreQueue.add({
    ...payload,
    queuedAt: Date.now(),
    retryCount: 0,
  });
}

// ── Queue drain ───────────────────────────────────────────────────

export async function drainQueues(apiClient: typeof import("$api/client").api): Promise<void> {
  const attendance = await getPendingAttendance();
  for (const item of attendance) {
    try {
      await apiClient.post("/attendance/mark", {
        school_calendar_id: item.schoolCalendarId,
        school_period_id: item.schoolPeriodId,
        records: item.records.map((r) => ({
          student_term_enrollment_id: r.studentTermEnrollmentId,
          status: r.status,
          note: r.note,
        })),
      });
      await offlineDb.attendanceQueue.delete(item.id!);
    } catch {
      await offlineDb.attendanceQueue.update(item.id!, {
        retryCount: item.retryCount + 1,
      });
    }
  }

  const scores = await offlineDb.scoreQueue.toArray();
  for (const item of scores) {
    try {
      await apiClient.post("/scores", {
        student_subject_registration_id: item.studentSubjectRegistrationId,
        assessment_type: item.assessmentType,
        assessment_label: item.assessmentLabel,
        raw_score: item.rawScore,
        max_score: item.maxScore,
      });
      await offlineDb.scoreQueue.delete(item.id!);
    } catch {
      await offlineDb.scoreQueue.update(item.id!, {
        retryCount: item.retryCount + 1,
      });
    }
  }
}

// ── Auto-drain on reconnect ───────────────────────────────────────

if (typeof window !== "undefined") {
  window.addEventListener("online", async () => {
    const { api } = await import("$api/client");
    await drainQueues(api);
  });
}
