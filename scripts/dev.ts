const args = process.argv.slice(2)

const build = Bun.spawnSync({
  cmd: ['bun', 'run', './scripts/build.ts', '--dev'],
  cwd: process.cwd(),
  stdin: 'inherit',
  stdout: 'inherit',
  stderr: 'inherit',
})

if (build.exitCode !== 0) {
  process.exit(build.exitCode ?? 1)
}

const cli = Bun.spawn({
  cmd: ['./cli-dev', ...args],
  cwd: process.cwd(),
  stdin: 'inherit',
  stdout: 'inherit',
  stderr: 'inherit',
})

const exitCode = await cli.exited
process.exit(exitCode)
