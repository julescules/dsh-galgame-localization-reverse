#!/usr/bin/env node
import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

const [artifactArg, outputArg] = process.argv.slice(2)
if (!artifactArg || !outputArg) {
  console.error('usage: node scripts/build-release-metadata.mjs <package.tgz> <output-directory>')
  process.exit(2)
}
const artifact = path.resolve(artifactArg)
const output = path.resolve(outputArg)
const bytes = await readFile(artifact)
const digest = createHash('sha256').update(bytes).digest('hex')
const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'))
await mkdir(output, { recursive: true })
await writeFile(path.join(output, 'SHA256SUMS'), `${digest}  ${path.basename(artifact)}\n`, 'utf8')
await writeFile(path.join(output, `${pkg.name}-${pkg.version}.sbom.cdx.json`), `${JSON.stringify({
  bomFormat: 'CycloneDX', specVersion: '1.5',
  serialNumber: `urn:uuid:${digest.slice(0, 8)}-${digest.slice(8, 12)}-${digest.slice(12, 16)}-${digest.slice(16, 20)}-${digest.slice(20, 32)}`,
  version: 1,
  metadata: { component: { type: 'library', 'bom-ref': `pkg:npm/${pkg.name}@${pkg.version}`, name: pkg.name, version: pkg.version, hashes: [{ alg: 'SHA-256', content: digest }], licenses: [{ license: { id: pkg.license } }] } },
  components: Object.entries(pkg.peerDependencies ?? {}).map(([name, version]) => ({ type: 'library', name, version, scope: 'optional', properties: [{ name: 'npm:peerDependency', value: 'true' }] })),
}, null, 2)}\n`, 'utf8')
console.log(`sha256=${digest}`)
