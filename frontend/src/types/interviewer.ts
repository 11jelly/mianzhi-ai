export type InterviewerState = 'IDLE' | 'SPEAKING' | 'LISTENING' | 'THINKING' | 'COMPLETED'

export type InterviewerStateInput = {
  completed?: boolean
  thinking?: boolean
  listening?: boolean
  speaking?: boolean
}
