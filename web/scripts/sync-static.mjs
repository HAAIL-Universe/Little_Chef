import { mkdir, copyFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(scriptDir, "..");

const copies = [
  ["index.html", path.join("dist", "index.html")],
  [path.join("src", "style.css"), path.join("dist", "style.css")],
];

for (const [srcRel, destRel] of copies) {
  const src = path.join(webRoot, srcRel);
  const dest = path.join(webRoot, destRel);
  await mkdir(path.dirname(dest), { recursive: true });
  await copyFile(src, dest);
}
