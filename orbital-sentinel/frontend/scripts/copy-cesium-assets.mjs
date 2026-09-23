import { access, cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const entry = path.dirname(require.resolve("cesium"));
const candidates = [
  path.resolve(entry, "Build", "Cesium"),
  path.resolve(entry, "..", "Build", "Cesium"),
  path.resolve(entry, "..", "..", "Build", "Cesium"),
];
let source = null;
for (const candidate of candidates) {
  try { await access(candidate); source = candidate; break; } catch {}
}
if (!source) throw new Error("Could not locate Cesium Build/Cesium static assets");

const target = path.resolve("public", "cesium");
await mkdir(path.dirname(target), { recursive: true });
await rm(target, { recursive: true, force: true });
await cp(source, target, { recursive: true });
console.log(`Copied Cesium static assets from ${source} to ${target}`);
