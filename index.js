import { fileURLToPath } from 'node:url'
import { readSkillBody } from './provider-core.js'

const PROVIDER_NAME = 'galgame-localization-reverse'
const SKILL_URL = new URL('./skill/SKILL.md', import.meta.url)
const RESOURCE_BASE = {
  kind: 'directory',
  path: fileURLToPath(new URL('./skill/', import.meta.url)),
}
const INVOCATION = { modelInvocable: true, userInvocable: true }
const DESCRIPTION = 'Galgame Doctor for Windows visual novels: safe translation-memory migration, project inspection, strict QA, engine evidence, and reversible releases.'

export const candidate = {
  name: 'galgame-localization-reverse',
  description: DESCRIPTION,
  whenToUse: 'Use when a user wants to inspect a Galgame directory, identify its engine, migrate translations after a game or script update, audit translated text, diagnose encoding or UI risks, or build and verify a reversible localization patch.',
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
