export type XfyunAvatarStatus =
  | 'disabled'
  | 'unconfigured'
  | 'ready'
  | 'starting'
  | 'running'
  | 'speaking'
  | 'error'

export type XfyunAvatarConfig = {
  enabled: boolean
  appId: string
  apiKey: string
  apiSecret: string
  avatarId: string
  vcn: string
}
