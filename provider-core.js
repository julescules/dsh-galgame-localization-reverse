import { readFile } from 'node:fs/promises'

export function stripFrontmatter(markdown) {
  if (typeof markdown !== 'string') throw new TypeError('skill markdown must be a string')
  const normalized = markdown.replace(/^\uFEFF/, '')
  const match = normalized.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n/)
  if (!match) throw new Error('SKILL.md must begin with YAML frontmatter')
  return normalized.slice(match[0].length)
}

export async function readSkillBody(skillUrl) {
  return stripFrontmatter(await readFile(skillUrl, 'utf8'))
}
