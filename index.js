import { fileURLToPath } from 'node:url'
import { readSkillBody } from './provider-core.js'

const PROVIDER_NAME = 'galgame-localization-reverse'
const SKILL_URL = new URL('./skill/SKILL.md', import.meta.url)
const RESOURCE_BASE = {
  kind: 'directory',
  path: fileURLToPath(new URL('./skill/', import.meta.url)),
}
const INVOCATION = { modelInvocable: true, userInvocable: true }
const DESCRIPTION = 'Windows galgame and visual-novel localization engineering: engine detection, encoding-safe text and UI work, bytecode round trips, save compatibility, reversible patches, portable releases, and evidence-driven rollback.'

export const candidate = {
  name: 'galgame-localization-reverse',
  description: DESCRIPTION,
  whenToUse: 'Use for Windows visual-novel engine identification, localization, resource rebuilding, runtime compatibility, save-safe patching, release QA, and rollback planning.',
  invocation: INVOCATION,
  provider: PROVIDER_NAME,
  source: 'bundled',
  resourceBase: RESOURCE_BASE,
  // Matches the official BUNDLED_SKILL_RANK while remaining compatible with early DSH RCs.
  rank: 600,
  locator: SKILL_URL,
  path: fileURLToPath(SKILL_URL),
}

export const provider = {
  name: PROVIDER_NAME,
  list: () => Promise.resolve([candidate]),
  async get() {
    return {
      name: candidate.name,
      description: candidate.description,
      whenToUse: candidate.whenToUse,
      invocation: candidate.invocation,
      provider: candidate.provider,
      source: candidate.source,
      resourceBase: RESOURCE_BASE,
      path: candidate.path,
      content: await readSkillBody(SKILL_URL),
    }
  },
}

export const name = 'galgame-localization-reverse'
export const inject = ['skills']

export function apply(ctx) {
  ctx.skills.registerProvider(() => provider)
}
