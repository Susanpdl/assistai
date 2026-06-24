// ============================================================
// Mock data for the AssistAI Classroom UI prototype.
// No backend yet — everything here is illustrative content so
// the three views can be demoed end to end.
// ============================================================

export const student = { name: 'Susan Poudel', initials: 'SP' }
export const instructor = { name: 'Dr. Elena Marsh', initials: 'EM' }

export const courses = [
  { id: 'cs310', code: 'CS 310', name: 'Operating Systems', active: true },
  { id: 'cs240', code: 'CS 240', name: 'Data Structures', active: false },
  { id: 'math221', code: 'MATH 221', name: 'Linear Algebra', active: false },
  { id: 'phil180', code: 'PHIL 180', name: 'Ethics & Technology', active: false },
]

// A grounded async-study conversation (student doing homework).
export const studyConversation = [
  {
    id: 'm1',
    role: 'user',
    text: 'Can you explain the difference between a process and a thread? I keep mixing them up.',
    time: '8:42 PM',
  },
  {
    id: 'm2',
    role: 'ai',
    text:
      'Great question — they\'re related but distinct.\n\nA process is an independent program in execution with its own memory space (code, heap, stack) and resources. A thread is the smallest unit of execution that runs inside a process and shares that process\'s memory with other threads.\n\nThink of a process as a house and threads as the people living in it: they share the same rooms (memory), which makes coordinating easy but also means one careless roommate can affect the others.',
    source: 'Week 4 — Processes & Threads, slide 9',
    time: '8:42 PM',
  },
  {
    id: 'm3',
    role: 'user',
    text: 'So why would I ever use multiple threads instead of multiple processes?',
    time: '8:43 PM',
  },
  {
    id: 'm4',
    role: 'ai',
    text:
      'Threads are cheaper. Because they share memory, creating a thread and switching between threads is much faster than for processes, and communicating between them doesn\'t need expensive inter-process communication.\n\nThe trade-off is safety: shared memory means you have to synchronize access (locks, semaphores) or you get race conditions. Use threads for tightly-coupled, parallel work inside one app; use processes when you need isolation.',
    source: 'Week 4 — Concurrency Basics, p.14',
    time: '8:43 PM',
  },
]

export const studySuggestions = [
  'Explain deadlock and the four conditions for it',
  'Walk me through how paging translates a virtual address',
  'Quiz me on CPU scheduling algorithms',
  'Summarize this week\'s lecture on file systems',
]

// In-class live session
export const liveSession = {
  course: 'CS 310 — Operating Systems',
  professor: 'Dr. Elena Marsh',
  connected: 38,
}

export const livePoll = {
  id: 'p1',
  question: 'Which scheduling algorithm can cause starvation if not managed carefully?',
  options: [
    { id: 'a', label: 'Round Robin' },
    { id: 'b', label: 'First-Come First-Served' },
    { id: 'c', label: 'Priority Scheduling' },
    { id: 'd', label: 'Shortest Job First' },
  ],
}

// Live results (what the instructor sees / the aside panel shows)
export const liveResults = [
  { id: 'a', label: 'Round Robin', count: 4 },
  { id: 'c', label: 'Priority Scheduling', count: 19 },
  { id: 'b', label: 'First-Come First-Served', count: 3 },
  { id: 'd', label: 'Shortest Job First', count: 8 },
]

export const liveSideChat = [
  {
    id: 'lm1',
    role: 'user',
    text: 'Quick one while we wait — is priority scheduling preemptive or non-preemptive?',
    time: 'now',
  },
  {
    id: 'lm2',
    role: 'ai',
    text:
      'It can be either. In preemptive priority scheduling a higher-priority job that arrives will interrupt the running one; in the non-preemptive version it waits until the current job finishes. Both can starve low-priority jobs — aging is the usual fix.',
    source: 'Week 5 — CPU Scheduling, slide 17',
    time: 'now',
  },
]

// Instructor dashboard
export const dashboardStats = [
  { id: 'enrolled', icon: '👥', tone: 'purple', value: 42, label: 'Students enrolled', delta: '+3 this week' },
  { id: 'questions', icon: '💬', tone: 'blue', value: 137, label: 'Questions today', delta: '+18% vs. yesterday' },
  { id: 'escalated', icon: '🚩', tone: 'coral', value: 4, label: 'Escalated to you', delta: '2 still need answers' },
]

export const escalatedQuestions = [
  {
    id: 'e1',
    question: 'The lecture says the page table is in memory, but where is the page table for the page table stored? Multi-level paging is confusing.',
    student: 'Marcus Lee',
    course: 'CS 310',
    time: '12 min ago',
    status: 'needs',
    reason: 'AI low confidence — conceptual depth',
  },
  {
    id: 'e2',
    question: 'For assignment 3, can we use a spinlock instead of a mutex, or will that be marked down?',
    student: 'Priya Nair',
    course: 'CS 310',
    time: '38 min ago',
    status: 'needs',
    reason: 'Course-policy question',
  },
  {
    id: 'e3',
    question: 'Is the final exam going to cover virtual memory or just scheduling?',
    student: 'Jordan Kim',
    course: 'CS 310',
    time: '1 hr ago',
    status: 'answered',
    reason: 'Logistics',
  },
  {
    id: 'e4',
    question: 'Banker\'s algorithm — does the safe sequence have to be unique?',
    student: 'Ava Rodriguez',
    course: 'CS 310',
    time: '2 hr ago',
    status: 'answered',
    reason: 'AI escalated for verification',
  },
]

export const courseFiles = [
  { id: 'f1', name: 'Week 5 — CPU Scheduling.pptx', type: 'pptx', size: '4.2 MB', chunks: 48, status: 'indexed' },
  { id: 'f2', name: 'Week 4 — Processes & Threads.pdf', type: 'pdf', size: '2.1 MB', chunks: 31, status: 'indexed' },
  { id: 'f3', name: 'Syllabus & Grading Policy.docx', type: 'docx', size: '88 KB', chunks: 6, status: 'indexed' },
  { id: 'f4', name: 'Week 6 — Deadlocks (draft).pdf', type: 'pdf', size: '3.0 MB', chunks: 0, status: 'processing' },
]

export const roster = [
  { id: 'r1', name: 'Marcus Lee', initials: 'ML', tone: 'blue', questions: 24, progress: 78, lastActive: '8 min ago' },
  { id: 'r2', name: 'Priya Nair', initials: 'PN', tone: 'purple', questions: 31, progress: 92, lastActive: '15 min ago' },
  { id: 'r3', name: 'Jordan Kim', initials: 'JK', tone: 'green', questions: 12, progress: 54, lastActive: '1 hr ago' },
  { id: 'r4', name: 'Ava Rodriguez', initials: 'AR', tone: 'slate', questions: 19, progress: 66, lastActive: '2 hr ago' },
  { id: 'r5', name: 'Diego Santos', initials: 'DS', tone: 'blue', questions: 8, progress: 41, lastActive: 'Yesterday' },
]

export const presetPolls = [
  { id: 'pp1', q: 'Which scheduling algorithm can cause starvation?', opts: 4 },
  { id: 'pp2', q: 'What is the purpose of a TLB?', opts: 4 },
  { id: 'pp3', q: 'True or False: threads share a heap.', opts: 2 },
]

// Canned AI replies for the interactive composer (no backend).
export const cannedReplies = [
  {
    text:
      'Good question. The key idea is that the OS keeps a per-process table tracking which resources are allocated and which are still needed, then only grants a request if the resulting state is still "safe" — meaning some ordering of the remaining processes can all finish.',
    source: 'Week 6 — Deadlocks, slide 11',
  },
  {
    text:
      'Let\'s break it down step by step. The virtual address splits into a page number and an offset. The page number indexes the page table to find the frame; the offset is added to the frame\'s base to get the physical address.',
    source: 'Week 7 — Virtual Memory, p.6',
  },
  {
    text:
      'From your course materials: the four necessary conditions for deadlock are mutual exclusion, hold-and-wait, no preemption, and circular wait. Breaking any one of them prevents deadlock.',
    source: 'Week 6 — Deadlocks, slide 4',
  },
]
