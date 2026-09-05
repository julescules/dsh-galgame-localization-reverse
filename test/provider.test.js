import assert from 'node:assert/strict'
import { access, readFile } from 'node:fs/promises'
import test from 'node:test'
import { candidate, provider, apply } from '../index.js'
import { stripFrontmatter } from '../provider-core.js'

test('frontmatter is removed from model-facing skill content', async () => {
  assert.equal(stripFrontmatter('---\nname: demo\ndescription: Demo\n---\n# Body\n'), '# Body\n')
  assert.throws(() => stripFrontmatter('# Body\n'), /frontmatter/)
  const skill = await provider.get(candidate)
  assert.match(skill.content, /^# Galgame Localization Reverse/m)
  assert.doesNotMatch(skill.content, /^---$/m)
})

test('candidate follows the DSH packaged-provider contract', async () => {
  assert.match(candidate.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/)
  assert.equal(candidate.provider, provider.name)
  assert.equal(candidate.rank, 600)
  assert.deepEqual(candidate.invocation, { modelInvocable: true, userInvocable: true })
  await access(candidate.path)
  await access(candidate.resourceBase.path)
})

test('Cordis apply registers the provider factory', () => {
  let registered
  apply({ skills: { registerProvider(factory) { registered = factory() } } })
  assert.equal(registered, provider)
})

test('all direct skill references and scripts exist', async () => {
  const body = await readFile(candidate.path, 'utf8')
  const links = [...body.matchAll(/`((?:references|scripts)\/[A-Za-z0-9._/-]+)`/g)].map(match => match[1])
  assert.ok(links.length >= 12)
  for (const link of new Set(links)) await access(new URL(`../skill/${link}`, import.meta.url))
})

test('package metadata supports DSH profile inventory without installing duplicate host peers', async () => {
  const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'))
  assert.equal(pkg.version, '0.8.0')
  assert.equal(pkg.exports['./package.json'], './package.json')
  assert.ok(pkg.files.includes('examples'))
  assert.ok(pkg.files.includes('scripts/build-release-metadata.mjs'))
  assert.ok(pkg.files.includes('scripts/verify-release.ps1'))
  assert.equal(pkg.peerDependenciesMeta['@deepseek-ai/cordis'].optional, true)
  assert.equal(pkg.peerDependenciesMeta['@deepseek-ai/dsh-skill'].optional, true)
})

test('Galgame Doctor entry points are packaged and discoverable', async () => {
  await access(new URL('../skill/scripts/vn_project_audit.py', import.meta.url))
  await access(new URL('../skill/scripts/vn_qa.py', import.meta.url))
  await access(new URL('../skill/scripts/vn_script_adapter.py', import.meta.url))
  await access(new URL('../skill/scripts/vn_translation_memory.py', import.meta.url))
  await access(new URL('../examples/synthetic-project/game/startup.tjs', import.meta.url))
  await access(new URL('../examples/translations.jsonl', import.meta.url))
  await access(new URL('../examples/glossary.json', import.meta.url))
  await access(new URL('../examples/translation-memory/current.jsonl', import.meta.url))
  await access(new URL('../examples/translation-memory/previous.jsonl', import.meta.url))
  await access(new URL('../examples/translation-memory/previous-hotfix.jsonl', import.meta.url))
  assert.match(candidate.description, /Galgame Doctor/)
  assert.match(candidate.whenToUse, /inspect a Galgame directory/)
  assert.match(candidate.whenToUse, /migrate translations/)
})
