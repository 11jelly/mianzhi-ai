import type { InterviewerState, InterviewerStateInput } from '../types/interviewer'

export function useInterviewerState({
  completed,
  thinking,
  listening,
  speaking,
}: InterviewerStateInput): InterviewerState {
  if (completed) {
    return 'COMPLETED'
  }
  if (thinking) {
    return 'THINKING'
  }
  if (listening) {
    return 'LISTENING'
  }
  if (speaking) {
    return 'SPEAKING'
  }
  return 'IDLE'
}
